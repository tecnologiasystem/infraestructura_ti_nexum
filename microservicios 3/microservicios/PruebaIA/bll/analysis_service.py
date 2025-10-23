# backend/bll/analysis_service.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import json
import re

from dal import analytics_dal as dal
from bll.ai_rewriter import rewrite_run_report

# ----------------- Utilidades -----------------

def _semaforo(score: float) -> str:
    return "verde" if score >= 75 else "amarillo" if score >= 60 else "rojo"

def _is_done_estado_avance(estado: str | None, avance: int | None) -> bool:
    s = (estado or "").lower()
    return s in ("completada", "terminada", "cerrada", "done") or (avance or 0) >= 100

def _build_section_html(title: str, bullets: List[str]) -> str:
    items = "".join(f"<li>{b}</li>" for b in bullets)
    return f"<article><p><strong>{title}</strong></p><ul>{items}</ul></article>"

# --- Utilidades para fechas/duración de tareas ---
def _tiene_deadline(t: dict) -> bool:
    """Devuelve True si la tarea tiene algún campo típico de fecha/limite."""
    if t.get("DiasRestantes") is not None:
        return True
    for k in ("FechaLimite", "FechaCompromiso", "FechaFinPlan", "FechaFinEstimada", "Deadline"):
        if t.get(k) is not None:
            return True
    return False

def _duracion_dias_guess(t: dict) -> float | None:
    """Intenta deducir duración en días con campos comunes; si no, None."""
    for k in ("DuracionDias", "Duracion", "DiasEstimados", "EstimadoDias"):
        v = t.get(k)
        if v is not None:
            try:
                return float(v)
            except Exception:
                pass
    # fallback: si no hay nada confiable, no inventamos
    return None

# ----------------- Motor de CASOS (JSONLogic + plantillas) -----------------

def _get_var(data: dict, path: str):
    cur = data
    for k in path.split("."):
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return None
    return cur

def eval_jsonlogic(rule: Any, data: dict) -> bool:
    """
    Soporta: and/or, >,>=,<,<= y var
    """
    if rule is True:
        return True
    if rule is False or rule is None:
        return False
    if isinstance(rule, dict):
        for op, val in rule.items():
            if op == "and":
                return all(eval_jsonlogic(x, data) for x in val)
            if op == "or":
                return any(eval_jsonlogic(x, data) for x in val)
            if op in (">", ">=", "<", "<="):
                a, b = val
                if isinstance(a, dict) and "var" in a:
                    a = _get_var(data, a["var"])
                if isinstance(b, dict) and "var" in b:
                    b = _get_var(data, b["var"])
                if a is None or b is None:
                    return False
                return (a > b) if op == ">" else (a >= b) if op == ">=" else (a < b) if op == "<" else (a <= b)
            if op == "var":
                return bool(_get_var(data, val))
    return False

def _fill_placeholders(text: str, values: dict) -> str:
    s = text or ""
    for k, v in (values or {}).items():
        s = s.replace("{{" + k + "}}", str(v))
    return s

def build_case_instance(cat: dict, values: dict, order: int) -> dict:
    # Combina corto + extendido + explicacion + FAQs
    def fill(txt: str | None) -> str:
        s = txt or ""
        for k, v in (values or {}).items():
            s = s.replace("{{" + k + "}}", str(v))
        # Limpieza final: si quedó algún placeholder sin resolver, colócalo como "—"
        s = re.sub(r"\{\{[^}]+\}\}", "—", s)
        return s

    cuerpo = fill(cat.get("CuerpoPlantilla"))
    if cat.get("CuerpoExtendidoPlantilla"):
        cuerpo += "\n\n" + fill(cat["CuerpoExtendidoPlantilla"])
    if cat.get("ExplicacionPlantilla"):
        cuerpo += "\n\n" + fill(cat["ExplicacionPlantilla"])
    if cat.get("FAQsPlantilla"):
        cuerpo += "\n\n" + fill(cat["FAQsPlantilla"])

    accion = fill(cat.get("AccionPlantilla"))
    if cat.get("AccionDetalladaPlantilla"):
        accion += "\n\n" + fill(cat["AccionDetalladaPlantilla"])

    return {
        "CasoID": cat["CasoID"],
        "Modulo": cat["Modulo"],
        "Severidad": cat["Severidad"],
        "Prioridad": cat["Prioridad"],
        "ValoresJSON": json.dumps(values, ensure_ascii=False),
        "EvidenciasJSON": None,
        "TituloFinal": fill(cat.get("TituloPlantilla")),
        "LeadFinal": fill(cat.get("LeadPlantilla")),
        "CuerpoFinal": cuerpo,
        "AccionFinal": accion,
        "KPIFinal": fill(cat.get("KPIPlantilla") or ""),
        "OrdenNarrativa": order
    }

# ----------------- Cálculos por módulo -----------------

def _cronograma_compute(proyecto_id: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    wbs = dal.get_tareas_wbs(proyecto_id)
    hojas = [t for t in wbs if t.get("EsHoja", 0) == 1]
    total = len(hojas)

    atrasadas = sum(
        1 for t in hojas
        if (t.get("DiasAtraso") or 0) > 0 and not _is_done_estado_avance(t.get("Estado"), t.get("PorcentajeAvance"))
    )
    en_riesgo = sum(
        1 for t in hojas
        if (t.get("DiasRestantes") or 9999) <= 3 and (t.get("PorcentajeAvance") or 0) < 80
        and not _is_done_estado_avance(t.get("Estado"), t.get("PorcentajeAvance"))
    )
    completadas = sum(1 for t in hojas if _is_done_estado_avance(t.get("Estado"), t.get("PorcentajeAvance")))
    avance_prom = round(sum((t.get("PorcentajeAvance") or 0) for t in hojas) / max(1, total), 2)

    # Score robusto (ponderado y acotado)
    if total == 0:
        score = 100.0
    else:
        overdue_pct = atrasadas / total
        risk_pct = en_riesgo / total
        progress_gap = max(0.0, (80.0 - avance_prom) / 80.0)  # distancia al 80%
        penal = 0.50 * overdue_pct + 0.30 * risk_pct + 0.20 * progress_gap
        score = round(max(0.0, 100.0 * (1.0 - min(1.0, penal))), 2)

    # Detalle por tarea (CPM placeholders; ES/EF/LS/LF nulos)
    detalle: List[Dict[str, Any]] = []
    for t in hojas[:2000]:  # safety
        detalle.append({
            "TareaID": t["TareaID"],
            "NombreTarea": _resolver_nombre_tarea(t),
            "ES": None, "EF": None, "LS": None, "LF": None,
            "HolguraTotal": t.get("HolguraTotal"),
            "EnRutaCritica": 1 if ((t.get("DiasRestantes") or 9999) <= 3 and (t.get("PorcentajeAvance") or 0) < 60) else 0,
            "PorcentajeCompletado": t.get("PorcentajeAvance"),
            "Estado": t.get("Estado"),
            "CategoriaCaso": "atrasada" if (t.get("DiasAtraso") or 0) > 0 else ("en_riesgo" if (t.get("DiasRestantes") or 9999) <= 3 else None),
            "ParentTareaID": t.get("IDTareaPadre"),
            "Nivel": t.get("Nivel"),
            "EsHoja": t.get("EsHoja"),
            "WBSPath": t.get("WBSPath")
        })

    paths = [{
        "PathIndex": 1,
        "TareasPath": "[" + ",".join(str(t["TareaID"]) for t in hojas[:5]) + "]",
        "DuracionDias": 20,
        "CriticalityIndex": 0.5
    }]
    mc = [{"TareaID": None, "P50": 10, "P85": 15, "P95": 22, "Media": 14, "StdDev": 3}]

    header = {
        "score": score,
        "metrics": {
            "total": total,
            "completadas": completadas,
            "atrasadas": atrasadas,
            "en_riesgo": en_riesgo,
            "avance_promedio": avance_prom,
            "prob_fin_atraso": 30,
            "fecha_p50": str(date.today()),
            "fecha_p85": str(date.today()),
            "fecha_p95": str(date.today()),
        },
        "alerts": [], "suggestions": []
    }
    return header, detalle, paths, mc

def _recursos_compute(proyecto_id: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    wbs = dal.get_tareas_wbs(proyecto_id)
    asign = dal.get_tarea_usuarios(proyecto_id)

    # Personas desde tareas hoja
    personas_map: Dict[int, Dict[str, Any]] = {}
    for t in wbs:
        if t.get("EsHoja", 0) != 1:
            continue
        tarea_id = t["TareaID"]
        usuarios: List[int] = []
        if tarea_id in asign and asign[tarea_id].get("UsuariosIDs"):
            usuarios = [int(x) for x in str(asign[tarea_id]["UsuariosIDs"]).split(",") if x]
        elif t.get("UsuarioAsignadoID"):
            usuarios = [int(t["UsuarioAsignadoID"])]
        for uid in usuarios:
            p = personas_map.setdefault(uid, {
                "UsuarioID": uid,
                "HorasPlanificadas": 0.0,
                "HorasRegistradas": 0.0,
                "Utilizacion": None,
                "Overtime": 0.0,
                "OnTimeRate": 0.7,
                "RiesgoIncumplir": 0.3
            })
            # Estimación simple: 16h por tarea hoja (placeholder)
            p["HorasPlanificadas"] += 16.0

    personas = list(personas_map.values())
    sobrecargados = 0
    subutilizados = 0
    for p in personas:
        plan = p["HorasPlanificadas"] or 0.0
        real = plan * 1.1 if plan > 0 else 0.0
        p["HorasRegistradas"] = real
        p["Utilizacion"] = round((real / plan), 2) if plan > 0 else None
        if p["Utilizacion"] and p["Utilizacion"] >= 1.2:
            sobrecargados += 1
        if p["Utilizacion"] and p["Utilizacion"] <= 0.6:
            subutilizados += 1

    balance_ok = max(0, len(personas) - (sobrecargados + subutilizados))
    score = max(0.0, min(100.0, 60 + (balance_ok / max(1, len(personas))) * 40 - 5 * sobrecargados))

    resumen = {
        "score": round(score, 2),
        "metrics": {
            "recursos": len(personas),
            "sobrecargados": sobrecargados,
            "subutilizados": subutilizados,
            "balance_ok": balance_ok
        }
    }
    # Asignaciones por usuario-tarea (peso 1/n)
    asignaciones: List[Dict[str, Any]] = []
    for t in wbs:
        if t.get("EsHoja", 0) != 1:
            continue
        tarea_id = t["TareaID"]
        usuarios: List[int] = []
        if tarea_id in asign and asign[tarea_id].get("UsuariosIDs"):
            usuarios = [int(x) for x in str(asign[tarea_id]["UsuariosIDs"]).split(",") if x]
        elif t.get("UsuarioAsignadoID"):
            usuarios = [int(t["UsuarioAsignadoID"])]

        n = max(1, len(usuarios))
        for uid in usuarios:
            asignaciones.append({
                "TareaID": tarea_id,
                "UsuarioID": uid,
                "PesoAsignacion": round(1.0 / n, 4),
                "HorasEstimadas": 16.0 / n,
                "CostoEstimado": None
            })

    return resumen, personas, asignaciones

def _finanzas_compute(proyecto_id: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    wbs = dal.get_tareas_wbs(proyecto_id)
    hojas = [t for t in wbs if t.get("EsHoja", 0) == 1]

    BAC = float(len(hojas) * 16.0 * 50.0)  # 16h por tarea * 50 moneda/hora
    PV = BAC * 0.5
    EV = BAC * 0.45
    AC = BAC * 0.52
    CPI = EV / AC if AC > 0 else 1.0
    SPI = EV / PV if PV > 0 else 1.0
    EAC = BAC / max(0.01, CPI)
    ETC = EAC - AC
    VAC = BAC - EAC
    BurnRate = AC / max(1.0, len(hojas) * 16.0)
    ProbSobreCosto = 40 if CPI < 0.95 else 20

    score = max(0.0, min(100.0, (70 * CPI + 20 * SPI - 20) if CPI < 1 else 75))
    fin = {
        "score": round(score, 2),
        "metrics": {
            "BAC": round(BAC, 2), "PV": round(PV, 2), "EV": round(EV, 2), "AC": round(AC, 2),
            "CPI": round(CPI, 3), "SPI": round(SPI, 3),
            "EAC": round(EAC, 2), "ETC": round(ETC, 2), "VAC": round(VAC, 2),
            "BurnRate": round(BurnRate, 4),
            "ProbSobreCosto": ProbSobreCosto
        }
    }
    serie: List[Dict[str, Any]] = []
    return fin, serie

# ----------------- ORQUESTADOR -----------------
def _armar_valores_caso(modulo: str, proyecto: dict, results: dict, metrics: dict, proyecto_id: int) -> dict:
    """
    Devuelve el diccionario de placeholders para rellenar la plantilla del caso.
    Puedes enriquecerlo todo lo que quieras con datos reales.
    """
    # Comunes
    owner = f"Líder {proyecto.get('NombreProyecto', 'del Frente')}"
    fecha_meta = str(date.today())
    values: dict = {"OWNER": owner, "FECHA_META": fecha_meta}

    if modulo == "cronograma":
        # Tareas críticas (de tu cron_detalle)
        criticas = [t for t in results.get("cron_detalle", []) if t.get("EnRutaCritica") == 1]
        
 # Crea el mapa ID->Nombre con el RESOLUTOR (una sola vez)
        wbs_completo = dal.get_tareas_wbs(proyecto_id)
        id_a_nombre_map = {t["TareaID"]: _resolver_nombre_tarea(t) for t in wbs_completo}
 

        # Heurísticas simples (mejóralas cuando tengas CPM real)
        impacto_dias = max(1, len(criticas))
        hito_siguiente = "Cierre de iteración actual"
        
# Usa el mapa para listar NOMBRES
        tareas_criticas_nombres = [
            id_a_nombre_map.get(t["TareaID"], f"ID:{t['TareaID']}")
            for t in criticas[:5]
        ]
        
        # Dependencias (si tus filas WBS traen antecesoras; si no, quedará vacío)
        dependencias_ids = []
        for t in criticas:
            dep_id = t.get("Antecesora") or t.get("antecesora")
            if dep_id:
                try: 
                    dependencias_ids.append(int(dep_id))
                except (ValueError, TypeError): 
                    pass
        
        # Usar el mismo mapa para convertir a nombres
        dependencias_nombres = [id_a_nombre_map.get(dep_id, f"ID:{dep_id}") for dep_id in sorted(list(set(dependencias_ids)))][:5]

        # Responsables
        responsables = []
        try:
            asign = dal.get_tarea_usuarios(proyecto_id)
            for t in criticas[:5]:
                info = asign.get(t["TareaID"])
                if info and info.get("UsuariosNombres"):
                    responsables.extend([n.strip() for n in str(info["UsuariosNombres"]).split(",") if n.strip()])
            responsables = sorted(set(responsables))[:5]
        except Exception:
            pass

        values.update({
            "FRENTE": "Integraciones",                  
            "TAREAS_CRITICAS": ", ".join(tareas_criticas_nombres),
            "HOLGURA_UMBRAL_DIAS": 2,
            "IMPACTO_DIAS": impacto_dias,
            "DEPENDENCIAS_CLAVE": ", ".join(dependencias_nombres) if dependencias_nombres else "Ninguna identificada",
            "RESPONSABLES": ", ".join(responsables) if responsables else "Equipo crítico",
            "HITO_SIGUIENTE": hito_siguiente,
            "OBJ_RIESGO": max(0, metrics["Cronograma"]["EnRiesgo"] - 5),
            "OBJ_P85": 3
        })
                # --------- (A) Tareas SIN FECHA y ejemplos ----------
        hojas_wbs = [t for t in wbs_completo if (t.get("EsHoja") or 0) == 1]
        tareas_sin_fecha = [t for t in hojas_wbs if not _tiene_deadline(t)]
        n_sin_fecha = len(tareas_sin_fecha)
        ejemplos_sin_fecha = [
            id_a_nombre_map.get(t["TareaID"], f"ID:{t['TareaID']}") for t in tareas_sin_fecha[:5]
        ]

        # --------- (B) Tareas GRANDES por duración ----------
        DURACION_UMBRAL = 10  # puedes parametrizarlo después
        tareas_grandes = []
        for t in hojas_wbs:
            d = _duracion_dias_guess(t)
            if d is not None and d > DURACION_UMBRAL:
                tareas_grandes.append(t)
        obj_tareas_grandes = max(0, len(tareas_grandes) - 3)

        # --------- (C) Aliases y placeholders esperados por la plantilla ----------
        values.update({
            "DEPENDENCIAS": values.get("DEPENDENCIAS_CLAVE") or "Ninguna identificada",
            "PERSONAS": values.get("RESPONSABLES") or "Equipo",
            "SIN_FECHA": n_sin_fecha,
            "EJEMPLOS": ", ".join(ejemplos_sin_fecha) if ejemplos_sin_fecha else "—",
            "OBJ_SIN_FECHA": max(0, n_sin_fecha - 2),
            "DURACION_UMBRAL": DURACION_UMBRAL,
            "OBJ_TAREAS_GRANDES": obj_tareas_grandes,
        })



    elif modulo == "recursos":
        criticas = [t for t in results.get("cron_detalle", []) if t.get("EnRutaCritica") == 1]
        asign = dal.get_tarea_usuarios(proyecto_id)  
        wbs_idx = {t["TareaID"]: t for t in dal.get_tareas_wbs(proyecto_id)}

        user_wip: dict[int, int] = {}
        user_names: dict[int, str] = {}
        tareas_por_user: dict[int, list[str]] = {}

        for t in criticas:
            tid = t["TareaID"]
            info = asign.get(tid) or {}
            ids = [int(x) for x in str(info.get("UsuariosIDs") or "").split(",") if x]
            noms = [s.strip() for s in str(info.get("UsuariosNombres") or "").split(",") if s.strip()]
             # Fallback: si no hay asignaciones en la SP, toma el asignado del WBS
            if not ids:
                wb = wbs_idx.get(tid) or {}
                uid = wb.get("UsuarioAsignadoID")
                if uid is not None:
                    try:
                        uid = int(uid)
                        name = (wb.get("UsuarioAsignadoNombre")
                                or wb.get("Responsable")
                                or f"Usuario {uid}")
                        ids = [uid]
                        noms = [name]
                    except (ValueError, TypeError):
                        pass
            
            # Alinear ids↔nombres lo mejor posible
            for i, uid in enumerate(ids):
                name = noms[i] if i < len(noms) and noms[i] else f"Usuario {uid}"
                user_names.setdefault(uid, name)
                user_wip[uid] = user_wip.get(uid, 0) + 1
                tareas_por_user.setdefault(uid, []).append(t.get("NombreTarea") or f"ID:{tid}")

        if user_wip:
            top_uid = max(user_wip, key=lambda u: user_wip[u])
            persona = user_names.get(top_uid, f"Usuario {top_uid}")
            wip = user_wip[top_uid]
            tareas_clave = ", ".join(dict.fromkeys(tareas_por_user.get(top_uid, [])))[:500]  # dedup + tope
        else:
            persona, wip, tareas_clave = "Equipo", 0, "—"
            
         # WIP objetivo (bajar al menos 1; mínimo 1)
        obj_wip = max(1, wip - 1) if wip else 1
        
        values.update({
            "PERSONA": persona,
            "WIP": wip,
            "TAREAS_CLAVE": tareas_clave,
            "OBJ_WIP": obj_wip,
            "SOBRE": ["J. Torres","A. Díaz"],
            "SUB": ["L. Pérez"],
            "OBJ_STD_UTILIZACION": 0.25
        })
                # Overtime, skills y alias PERSONAS
        rec_m = metrics.get("Recursos", {}) if isinstance(metrics, dict) else {}
        values.update({
            "OVERTIME": rec_m.get("OvertimePromedio", 0.0),
            "OBJ_OVERTIME": 0.10,  # objetivo ejemplo (10%)
            "SKILLS": rec_m.get("HabilidadesFaltantes", 0),
            "PERSONAS": values.get("PERSONAS") or values.get("PERSONA") or "Equipo",
        })



    elif modulo == "flujo":
        fl_m = metrics.get("Flujo", {}) if isinstance(metrics, dict) else {}
        leadp95 = fl_m.get("LeadTimeP95", None)
        retrabajo = fl_m.get("PorcentajeRetrabajo", None)
        wip = fl_m.get("WIPEnProceso", None)

        values.update({
            "OBJ_BLOQUEOS": 3,
            "COLAS_AFECTADAS": values.get("COLAS_AFECTADAS") or "Backlog, QA, Deploy",
            "LEADP95": leadp95 if leadp95 is not None else "—",
            "OBJ_LEADP95": (leadp95 - 2) if isinstance(leadp95, (int, float)) else 10,
            "PORC": round(retrabajo, 2) if isinstance(retrabajo, (int, float)) else 0.0,   # retrabajo actual
            "OBJ_RETRABAJO": max(0.0, round((retrabajo or 0.22) - 0.05, 2)),
            # Fallbacks por si este caso se arma sin pasar por 'recursos'
            "WIP": values.get("WIP") if values.get("WIP") is not None else (wip or 0),
            "OBJ_WIP": values.get("OBJ_WIP") if values.get("OBJ_WIP") is not None else max(1, (wip or 1) - 3),
        })


    elif modulo == "finanzas":
        fin_m = results.get("fin", {}).get("metrics", {})
        values.update({
            "CPI": fin_m.get("CPI", 1.0),
            "SPI": fin_m.get("SPI", 1.0),
            "AC":  fin_m.get("AC", 0.0),
            "EAC": fin_m.get("EAC", 0.0),
            "VAC": fin_m.get("VAC", 0.0),
            "OBJ_CPI": 1.0, 
            "OBJ_SPI": 1.0
    })
        # Burn rate y No Billable
        fin_m = results.get("fin", {}).get("metrics", {})
        burn = fin_m.get("BurnRate")
        nb = metrics.get("Finanzas", {}).get("PorcentajeNoBillable", None)

        values.update({
            "BURN": round(burn, 4) if isinstance(burn, (int, float)) else 0.0,
            "OBJ_BURN": max(0.0, round((burn or 0.04) - 0.005, 4)),
            "PORC": round(nb, 2) if isinstance(nb, (int, float)) else 0.0,           # no billable actual
            "OBJ_NB": max(0.0, round((nb or 0.25) - 0.05, 2)),
        })

    elif modulo == "calidad":
        values.update({
            "DEFECTOS": metrics.get("Calidad", {}).get("DefectosUAT", 0),
            "AREAS_AFECTADAS": ["Front-end", "Back-end"],
            "OBJ_DEFECTOS": max(0, metrics.get("Calidad", {}).get("DefectosUAT", 0) - 5)
        })
        cal_m = metrics.get("Calidad", {}) if isinstance(metrics, dict) else {}
        values.update({
            "COB": cal_m.get("CoberturaUnit", 0.0),
            "OBJ_COB": min(1.0, round((cal_m.get("CoberturaUnit", 0.45) + 0.15), 2)),
            "AREAS": ", ".join(values.get("AREAS_AFECTADAS", [])) if isinstance(values.get("AREAS_AFECTADAS"), list)
                     else (values.get("AREAS_AFECTADAS") or "—"),
        })


    elif modulo == "comunicaciones":
        values.update({
            "STAKEHOLDERS": ["Operaciones", "Ventas"],
            "TOPICOS": ["Alcance de la fase 2", "Fechas de go-live"]
        })

    elif modulo == "alcance":
        values.update({
            "CAMBIOS": metrics.get("Alcance", {}).get("CambiosNoPlanificados", 0),
            "EJEMPLOS": ["API extra para cliente X", "Reporte adicional no planificado"],
            "OBJ_CAMBIOS": 1
        })

    elif modulo == "riesgos":
        values.update({
            "ALTOS": metrics.get("Riesgos", {}).get("RiesgosAltos", 0),
            "SIN_PLAN": metrics.get("Riesgos", {}).get("SinMitigacion", 0),
            "OBJ_ALTOS": max(0, metrics.get("Riesgos", {}).get("RiesgosAltos", 0) - 2)
        })
    return values


def analyze_project(proyecto_id: int, modo_narrativa: str = "extendida") -> Dict[str, Any]:
    proyecto = dal.get_proyecto(proyecto_id)
    if not proyecto:
        raise ValueError("Proyecto no encontrado")

    run_id = dal.create_run("proyecto", proyecto_id)
    dal.progress_init(run_id)

    # Inicializa etapas
    for s in ["cronograma", "recursos", "finanzas", "flujo", "riesgos", "informe"]:
        dal.progress_update(run_id, s, steps_done=0, substage="pending", state="running")

    results: Dict[str, Any] = {}

    # Ejecuta en paralelo cronograma/recursos/finanzas
    def do_cron():
        header, detalle, paths, mc = _cronograma_compute(proyecto_id)
        dal.save_cronograma(run_id, header, detalle, paths, mc)
        dal.progress_update(run_id, "cronograma", steps_done=6, substage="done", message="Cronograma listo", state="done")
        results["cron_header"] = header
        results["cron_detalle"] = detalle
        results["cron_score"] = header["score"]
        return True

    def do_rec():
        resumen, personas, asignaciones = _recursos_compute(proyecto_id)
        dal.save_recursos(run_id, resumen, personas)
        if asignaciones:
            dal.save_asignaciones(run_id, asignaciones)
        dal.progress_update(run_id, "recursos", steps_done=5, substage="done", message="Recursos listos", state="done")
        results["rec_resumen"] = resumen
        results["rec_score"] = resumen["score"]
        return True

    def do_fin():
        fin, serie = _finanzas_compute(proyecto_id)
        dal.save_finanzas(run_id, fin, serie)
        dal.progress_update(run_id, "finanzas", steps_done=5, substage="done", message="Finanzas listas", state="done")
        results["fin"] = fin        
        results["fin_score"] = fin["score"]
        return True

    with ThreadPoolExecutor(max_workers=3) as ex:
        for _ in as_completed([ex.submit(do_cron), ex.submit(do_rec), ex.submit(do_fin)]):
            pass

    # Flujo & Riesgos (placeholders)
    results["flujo_score"] = 70.0
    dal.progress_update(run_id, "flujo", steps_done=5, substage="done", message="Flujo listo", state="done")
    results["riesgos_score"] = 78.0
    dal.progress_update(run_id, "riesgos", steps_done=4, substage="done", message="Riesgos listos", state="done")

    try:
        # --- Disparo de CASOS desde catálogo ---
        fin_m = results.get("fin", {}).get("metrics", {})

        metrics = {
            "Cronograma": {
                "EnRiesgo": results.get("cron_header", {}).get("metrics", {}).get("en_riesgo", 0),
                "CriticasHolguraBaja": sum(1 for t in results.get("cron_detalle", []) if t.get("EnRutaCritica") == 1),
                "TareasSinFecha": 3,          # TODO: calcula real (FechaLimite NULL)
                "TareasGrandes": 4,           # TODO: calcula real (FechaLimite-FechaInicio > umbral)
                "DepCriticas": 3,             # TODO: calcula real (antecesoras en críticas)
                "SinResponsable": 2           # TODO: calcula real (UsuarioAsignadoID NULL y sin tareausuario)
            },
            "Recursos": {
                "Sobrecargados": results.get("rec_resumen", {}).get("metrics", {}).get("sobrecargados", 0),
                "Subutilizados": results.get("rec_resumen", {}).get("metrics", {}).get("subutilizados", 0),
                "PersonasConWIPAlto": 1,      # TODO: real si mides WIP por persona
                "OvertimePromedio": 0.18,     # TODO: real si traes horas extra
                "AusenciasSemana": 2,         # TODO
                "HabilidadesFaltantes": 1     # TODO: gap de skills vs tareas
            },
            "Flujo": {
                "BloqueosActivos": 6,         # TODO: real si manejas bloqueos/estados
                "WIPEnProceso": 14,           # TODO
                "LeadTimeP95": 12,            # TODO: calcula con BitacoraTarea
                "PorcentajeRetrabajo": 0.22,  # TODO: reabiertas / total
                "ColumnaBloqueadaDias": 3     # TODO
            },
            "Finanzas": {
                "CPI": fin_m.get("CPI", 0.86),
                "SPI": fin_m.get("SPI", 0.90),
                "AC":  fin_m.get("AC", 0.0),
                "EAC": fin_m.get("EAC", 0.0),
                "VAC": fin_m.get("VAC", -1000.0),
                "BurnRate": fin_m.get("BurnRate", 0.042),
                "PorcentajeNoBillable": 0.25  # TODO: si separas imputaciones no facturables
            },
            "Calidad": {
                "DefectosUAT": 12,            # TODO: con tu fuente real
                "CoberturaUnit": 0.45,        # TODO: si tienes cobertura
                "DefectosRecurrentes": 7      # TODO: defectos reabiertos
            },
            "Comms": {
                "StakeholdersSinAlineacion": 2,
                "ReportesAtrasados": 1
            },
            "Alcance": {
                "CambiosNoPlanificados": 4,
                "RequisitosAmbiguos": 3
            },
            "Riesgos": {
                "RiesgosAltos": 3,
                "SinMitigacion": 1,
                "IssuesMaterializados": 2
            }
        }

        casos_resueltos: List[Dict[str, Any]] = []
        orden = 1
        for modulo in ("cronograma","recursos","flujo","finanzas","calidad","comunicaciones","alcance","riesgos"):
            for cat in dal.list_casos(modulo):
               # filtro por modo de narrativa (opcional)
               aud = (cat.get("Audiencia") or "").lower()
               lvl = (cat.get("Nivel") or "").lower()
               if modo_narrativa == "ejecutiva":
                   # quédate con lo directivo/general y evita "tecnica" o "corta"
                   if aud == "tecnica" or lvl == "corta":
                       continue
               rule = json.loads(cat.get("CondicionJSON") or "true")
               if eval_jsonlogic(rule, metrics):
                   values = _armar_valores_caso(modulo, proyecto, results, metrics, proyecto_id)
                   casos_resueltos.append(build_case_instance(cat, values, orden))
                   orden += 1

               if casos_resueltos and hasattr(dal, "insert_run_casos"):
                   dal.insert_run_casos(run_id, casos_resueltos)

    except Exception:
        pass

    # Secciones del informe
    dal.save_informe_seccion(
        run_id, "cronograma", "Cronograma & Tareas",
        _build_section_html("Resumen", [
            "Se detectaron tareas con poco margen y avance bajo; priorizar foco y desbloqueos.",
            "Dividir entregables semanales y revisar dependencias."
        ]), 120
    )
    dal.save_informe_seccion(
        run_id, "recursos", "Recursos",
        _build_section_html("Resumen", [
            "Balancear carga entre perfiles con WIP alto y bajo.",
            "Definir franja sin reuniones y límites de WIP por persona."
        ]), 100
    )
    dal.save_informe_seccion(
        run_id, "finanzas", "Finanzas",
        _build_section_html("Resumen", [
            "Vigilar costo vs valor ganado; ajustar compromisos no críticos.",
            "Revisar forecast para alinear EAC con presupuesto."
        ]), 100
    )
    dal.progress_update(run_id, "informe", steps_done=2, substage="done", message="Informe listo", state="done")

    # Score general ponderado
    cron_score = results.get("cron_score", 70.0)
    rec_score  = results.get("rec_score",  70.0)
    fin_score  = results.get("fin_score",  70.0)

    score_general = round(
        0.30 * cron_score +
        0.20 * rec_score  +
        0.20 * fin_score  +
        0.15 * results["flujo_score"] +
        0.10 * results["riesgos_score"] +
        0.05 * 90.0, 2
    )

    sema = _semaforo(score_general)
    resumen = (
        f"El proyecto '{proyecto.get('NombreProyecto','')}' "
        f"{('va bien' if sema=='verde' else 'requiere atención' if sema=='amarillo' else 'va mal')} "
        f"con salud {score_general}."
    )

    dal.close_run(run_id, score_general, sema, resumen)
    dal.progress_set_state(run_id, "completed", "Análisis finalizado")

    return {"run_id": run_id, "score_general": score_general, "semaforo": sema, "resumen": resumen}

def _resolver_nombre_tarea(t: dict) -> str:
    """
    Devuelve el mejor nombre posible para la tarea:
    - Prioriza columnas comunes de nombre/título/descr.
    - Si el nombre es genérico tipo 'Tarea 123', intenta con el último segmento del WBSPath.
    - Último fallback: 'ID:xxx'.
    """
    candidatos = [
        t.get("NombreTarea"),
        t.get("Nombre"),
        t.get("NombreActividad"),
        t.get("Actividad"),
        t.get("Titulo"),
        t.get("Descripcion"),
    ]
    name = ""
    for c in candidatos:
        c = (c or "").strip()
        if c:
            name = c
            break

    # Si viene algo genérico tipo "Tarea 101", intenta mejorar con WBSPath
    if name and re.fullmatch(r"(tarea|task)\s*#?\s*\d+", name, flags=re.IGNORECASE):
        wbs = (t.get("WBSPath") or "").strip()
        if wbs:
            # Soporta separadores '>' o '/'
            last = wbs.split(">")[-1].split("/")[-1].strip()
            if last and not re.fullmatch(r"(tarea|task)\s*#?\s*\d+", last, re.IGNORECASE):
                name = last

    if not name:
        # Último recurso
        name = f"ID:{t.get('TareaID')}"
    return name

def generar_informe_ia(run_id: int, audiencia: str = "ejecutiva"):
    """Servicio BLL para reescritura on-demand (Plan B)."""
    return rewrite_run_report(run_id, audiencia=audiencia)