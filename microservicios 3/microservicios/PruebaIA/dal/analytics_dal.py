# backend/dal/analytics_dal.py
from typing import Any, Dict, List, Optional, Tuple
import json
from config import get_connection
import pyodbc
from datetime import datetime, date


def _rows_to_dicts(cur):
    if not cur.description:
        return []
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _dt(x):
    return x.isoformat() if isinstance(x, (datetime, date)) else x


# ---------- RUN / PROGRESO ----------
def create_run(tipo_entidad: str, entidad_id: int) -> int:
    con = get_connection()
    try:
        cur = con.cursor()
        sql = """
        DECLARE @rid INT;
        EXEC dbo.sp_Ana_CreateRun ?, ?, @rid OUTPUT;
        SELECT CAST(@rid AS INT) AS RunID;
        """
        cur.execute(sql, (tipo_entidad, entidad_id))

        # Avanza entre conjuntos hasta hallar el SELECT final
        row = None
        while True:
            try:
                row = cur.fetchone()
                break
            except pyodbc.ProgrammingError as e:
                # No hay filas en este set; pasa al siguiente si existe
                if "No results" in str(e):
                    if not cur.nextset():
                        raise
                else:
                    raise

        if not row or row[0] is None:
            raise RuntimeError("sp_Ana_CreateRun no devolvió RunID")
        run_id = int(row[0])
        con.commit()
        return run_id
    finally:
        con.close()


def progress_init(run_id: int) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("EXEC dbo.sp_Ana_Progress_Init ?", (run_id,))
        con.commit()
    finally:
        con.close()


def progress_update(
    run_id: int,
    stage: str,
    *,
    steps_done: Optional[int] = None,
    substage: Optional[str] = None,
    message: Optional[str] = None,
    state: Optional[str] = None,
) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "EXEC dbo.sp_Ana_Progress_Update ?,?,?,?, ?,?",
            (run_id, stage, substage, steps_done, message, state),
        )
        con.commit()
    finally:
        con.close()


def progress_get(run_id: int) -> dict:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("EXEC dbo.sp_Ana_Progress_Get ?", (run_id,))
        rows = _rows_to_dicts(cur)
        if not rows:
            return {}
        row = rows[0]
        stages = json.loads(
            row.get("StagesJSON") or "[]"
        )  # ya viene como strings desde SQL
        return {
            "run_id": row["RunID"],
            "estado": row["Estado"],
            "percent_global": float(row["PercentGlobal"] or 0),
            "mensaje": row.get("Mensaje"),
            "iniciado_en": _dt(row.get("IniciadoEn")),
            "actualizado_en": _dt(row.get("ActualizadoEn")),
            "stages": stages,
        }
    finally:
        con.close()


def progress_set_state(run_id: int, estado: str, mensaje: Optional[str] = None) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        # SP: sp_Ana_Progress_SetState @RunID, @Estado, @Mensaje
        cur.execute(
            "EXEC dbo.sp_Ana_Progress_SetState ?, ?, ?", (run_id, estado, mensaje)
        )
        con.commit()
    finally:
        con.close()


# ---------- LECTURAS (datos de origen) ----------
def get_proyecto(proyecto_id: int) -> Optional[Dict[str, Any]]:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("EXEC dbo.sp_Ana_GetProyecto ?", (proyecto_id,))
        rows = _rows_to_dicts(cur)
        return rows[0] if rows else None
    finally:
        con.close()


def get_tareas_wbs(proyecto_id: int) -> List[Dict[str, Any]]:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("EXEC dbo.sp_Ana_GetTareasWBS ?", (proyecto_id,))
        return _rows_to_dicts(cur)
    finally:
        con.close()


def get_tarea_usuarios(proyecto_id: int) -> Dict[int, Dict[str, Any]]:
    """Devuelve dict {TareaID: {NumAsignados, UsuariosIDs, UsuariosNombres}}"""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("EXEC dbo.sp_Ana_GetTareaUsuarios ?", (proyecto_id,))
        rows = _rows_to_dicts(cur)
        return {r["TareaID"]: r for r in rows}
    finally:
        con.close()


def get_bitacora_tarea(proyecto_id: int) -> List[Dict[str, Any]]:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("EXEC dbo.sp_Ana_GetBitacoraTarea ?", (proyecto_id,))
        return _rows_to_dicts(cur)
    finally:
        con.close()


# ---------- PERSISTENCIAS (JSON) ----------
def save_cronograma(
    run_id: int,
    cronograma_json: Dict[str, Any],
    tareas_json: List[Dict[str, Any]],
    paths_json: List[Dict[str, Any]],
    montecarlo_json: List[Dict[str, Any]],
) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "EXEC dbo.sp_Ana_SaveCronograma ?, ?, ?, ?, ?",
            (
                run_id,
                json.dumps(cronograma_json, ensure_ascii=False),
                json.dumps(tareas_json, ensure_ascii=False),
                json.dumps(paths_json, ensure_ascii=False),
                json.dumps(montecarlo_json, ensure_ascii=False),
            ),
        )
        con.commit()
    finally:
        con.close()


def save_recursos(
    run_id: int, resumen_json: Dict[str, Any], personas_json: List[Dict[str, Any]]
) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "EXEC dbo.sp_Ana_SaveRecursos ?, ?, ?",
            (
                run_id,
                json.dumps(resumen_json, ensure_ascii=False),
                json.dumps(personas_json, ensure_ascii=False),
            ),
        )
        con.commit()
    finally:
        con.close()


def save_asignaciones(run_id: int, asignaciones_json: List[Dict[str, Any]]) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "EXEC dbo.sp_Ana_SaveAsignaciones ?, ?",
            (run_id, json.dumps(asignaciones_json, ensure_ascii=False)),
        )
        con.commit()
    finally:
        con.close()


def save_finanzas(
    run_id: int, fin_json: Dict[str, Any], serie_json: List[Dict[str, Any]]
) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "EXEC dbo.sp_Ana_SaveFinanzas ?, ?, ?",
            (
                run_id,
                json.dumps(fin_json, ensure_ascii=False),
                json.dumps(serie_json, ensure_ascii=False),
            ),
        )
        con.commit()
    finally:
        con.close()


def save_recomendaciones(run_id: int, recs_json: List[Dict[str, Any]]) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "EXEC dbo.sp_Ana_SaveRecomendaciones ?, ?",
            (run_id, json.dumps(recs_json, ensure_ascii=False)),
        )
        con.commit()
    finally:
        con.close()


def save_informe_seccion(
    run_id: int, seccion: str, titulo: str, html: str, word_count: int
) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "EXEC dbo.sp_Ana_SaveInformeSeccion ?, ?, ?, ?, ?",
            (run_id, seccion, titulo, html, word_count),
        )
        con.commit()
    finally:
        con.close()


def close_run(run_id: int, score_general: float, semaforo: str, resumen: str) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "EXEC dbo.sp_Ana_CloseRun ?, ?, ?, ?",
            (run_id, score_general, semaforo, resumen),
        )
        con.commit()
    finally:
        con.close()


# ---------- LECTURAS DE RESULTADO ----------
def _get_run_head(run_id: int) -> Optional[Dict[str, Any]]:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT r.RunID, r.ScoreGeneral, r.Semaforo, r.ResumenEjecutivo,
                   r.IniciadoEn, r.FinalizadoEn,
                   p.ProyectoID, p.NombreProyecto
            FROM dbo.AnalisisRun r
            LEFT JOIN dbo.proyecto p ON p.ProyectoID = r.EntidadID
            WHERE r.RunID = ?
        """,
            (run_id,),
        )
        rows = _rows_to_dicts(cur)
        return rows[0] if rows else None
    finally:
        con.close()


def _get_sections(run_id: int) -> List[Dict[str, Any]]:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT Seccion, Titulo, Html
            FROM dbo.AnalisisInformeSeccion
            WHERE RunID = ?
            ORDER BY SeccionID ASC
        """,
            (run_id,),
        )
        return _rows_to_dicts(cur)
    finally:
        con.close()


def _get_cases(run_id: int) -> List[Dict[str, Any]]:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT Modulo, Severidad, Prioridad,
                   TituloFinal, LeadFinal, CuerpoFinal, AccionFinal, KPIFinal
            FROM dbo.AnalisisRunCaso
            WHERE RunID = ?
            ORDER BY Prioridad ASC, Severidad DESC, OrdenNarrativa ASC, RunCasoID ASC
        """,
            (run_id,),
        )
        return _rows_to_dicts(cur)
    finally:
        con.close()


def _get_kpis(run_id: int) -> Dict[str, Dict[str, Any]]:
    con = get_connection()
    try:
        cur = con.cursor()
        data: Dict[str, Dict[str, Any]] = {}

        cur.execute("SELECT * FROM dbo.AnalisisCronograma WHERE RunID=?", (run_id,))
        r = _rows_to_dicts(cur)
        if r:
            c = r[0]
            data["cronograma"] = {
                "score": c.get("Score"),
                "detalle": f"{c.get('Completadas',0)}/{c.get('TareasTotales',0)} compl. · {c.get('Atrasadas',0)} atrasadas · {c.get('EnRiesgo',0)} en riesgo",
            }

        cur.execute("SELECT * FROM dbo.AnalisisRecursos WHERE RunID=?", (run_id,))
        r = _rows_to_dicts(cur)
        if r:
            c = r[0]
            data["recursos"] = {
                "score": c.get("Score"),
                "detalle": f"{c.get('Recursos',0)} recursos · {c.get('Sobrecargados',0)} sobrecargados · {c.get('Subutilizados',0)} subutilizados",
            }

        cur.execute("SELECT * FROM dbo.AnalisisFinanzas WHERE RunID=?", (run_id,))
        r = _rows_to_dicts(cur)
        if r:
            c = r[0]
            cpi = c.get("CPI")
            spi = c.get("SPI")
            data["finanzas"] = {
                "score": c.get("Score"),
                "detalle": f"CPI {cpi} · SPI {spi}",
            }

        cur.execute("SELECT * FROM dbo.AnalisisFlujo WHERE RunID=?", (run_id,))
        r = _rows_to_dicts(cur)
        if r:
            c = r[0]
            data["flujo"] = {
                "score": c.get("Score"),
                "detalle": f"WIP {c.get('WIPPromedio',0)} · lead p95 {c.get('LeadTimeP95',0)} d · bloqueos {c.get('BloqueosActivos',0)}",
            }

        cur.execute("SELECT * FROM dbo.AnalisisRiesgos WHERE RunID=?", (run_id,))
        r = _rows_to_dicts(cur)
        if r:
            c = r[0]
            data["riesgos"] = {
                "score": c.get("Score"),
                "detalle": f"{c.get('RiesgosAltos',0)}/{c.get('RiesgosAbiertos',0)} riesgos altos",
            }
        return data
    finally:
        con.close()


def get_informe_html(run_id: int) -> str:
    """Render bonito con portada, KPIs, (casos si hay) y secciones."""
    head = _get_run_head(run_id) or {}
    sections = _get_sections(run_id)
    cases = _get_cases(run_id)
    kpis = _get_kpis(run_id)

    proyecto = head.get("NombreProyecto") or f"Run {run_id}"
    salud = head.get("ScoreGeneral")
    semaf = (head.get("Semaforo") or "").lower()
    resumen = head.get("ResumenEjecutivo") or "Informe generado automáticamente."

    semaf_color = {"verde": "#2ecc71", "amarillo": "#f1c40f", "rojo": "#e74c3c"}.get(
        semaf, "#95a2c6"
    )
    fecha = head.get("FinalizadoEn") or head.get("IniciadoEn") or datetime.utcnow()
    if isinstance(fecha, (datetime, date)):
        fecha_txt = str(fecha)[:19]
    else:
        fecha_txt = str(fecha)

    # KPIs cards
    kpi_cards = ""

    def card(mod, titulo):
        d = kpis.get(mod)
        if not d:
            return ""
        score = d.get("score")
        det = d.get("detalle", "")
        return f"""
        <div class="kpi">
          <div class="kpi-title">{titulo}</div>
          <div class="kpi-score">{'' if score is None else round(score,2)}</div>
          <div class="kpi-det">{det}</div>
        </div>
        """

    kpi_cards += card("cronograma", "Cronograma")
    kpi_cards += card("recursos", "Recursos")
    kpi_cards += card("finanzas", "Finanzas")
    kpi_cards += card("flujo", "Flujo")
    kpi_cards += card("riesgos", "Riesgos")

    # Casos (si hay)
    casos_html = ""
    if cases:
        items = []
        for c in cases:
            sev = int(c.get("Severidad") or 2)
            sev_txt = {3: "ALTA", 2: "MEDIA", 1: "BAJA"}.get(sev, "MEDIA")
            sev_color = {3: "#e74c3c", 2: "#f1c40f", 1: "#2ecc71"}.get(sev, "#f1c40f")
            items.append(
                f"""
            <div class="case">
              <div class="case-head">
                <span class="chip" style="background:{sev_color}">{sev_txt}</span>
                <strong>{c.get('TituloFinal','')}</strong>
              </div>
              <p class="lead">{c.get('LeadFinal','')}</p>
              <p>{c.get('CuerpoFinal','')}</p>
              <div class="accion"><strong>Acción:</strong> {c.get('AccionFinal','')}</div>
              {f"<div class='kpiobjetivo'><strong>KPI:</strong> {c.get('KPIFinal')}</div>" if c.get('KPIFinal') else ""}
            </div>
            """
            )
        casos_html = (
            f"<section class='card'><h2>Casos destacados</h2>{''.join(items)}</section>"
        )

    # Secciones guardadas
    secs_html = (
        "\n".join(
            [
                f"<section class='card'><h2>{s['Titulo']}</h2>{s['Html']}</section>"
                for s in sections
            ]
        )
        if sections
        else "<section class='card'><h2>Secciones</h2><p>No hay contenido.</p></section>"
    )

    # Render
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8" />
<title>Informe • {proyecto}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  :root {{ --bg:#FFFFFF; --panel:#FAF7F7; --muted:#555555; --accent:#000000; }}
  body {{ margin:0; font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Arial; background:var(--bg); color:#000000; }}
  .wrap {{ max-width:1100px; margin:40px auto; padding:0 16px; }}
  header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:24px; }}
  .brand {{ font-size:22px; font-weight:700; line-height:1.2; }}
  .meta {{ color:var(--muted); font-size:13px; }}
  .health {{ display:flex; align-items:center; gap:8px; }}
  .health .dot {{ width:12px; height:12px; border-radius:999px; display:inline-block; }}
  .health .score {{ font-weight:700; }}
  .card {{ background:var(--panel); border:1px solid #EAEAEA; border-radius:16px; padding:20px; margin:12px 0; box-shadow:0 4px 12px rgba(0,0,0,.05); }}
  h2 {{ font-size:18px; margin:0 0 10px; color:#000000; }}
  .kpis {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; }}
  .kpi {{ background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.06); border-radius:12px; padding:12px; }}
  .kpi-title {{ color:var(--muted); font-size:12px; }}
  .kpi-score {{ font-size:22px; font-weight:700; margin:6px 0; }}
  .kpi-det {{color:#000000; font-size:12px; }}
  .case {{ border-top:1px solid #EAEAEA; padding-top:10px; margin-top:12px; }}
  .case:first-child {{ border-top:none; padding-top:0; margin-top:0; }}
  .case-head {{ display:flex; align-items:center; gap:8px; margin-bottom:6px; }}
  .chip {{ color:#000000; font-weight:700; font-size:11px; padding:3px 8px; border-radius:999px; }}
  .lead {{ color:#000000; margin:4px 0; }}
  .accion, .kpiobjetivo {{ background:#F0F0F0; border:1px dashed #D0D0D0; border-radius:8px; padding:8px; margin-top:8px; }}
  .resumen {{ color:#000000; }}
</style></head>
<body>
  <div class="wrap">
    <header>
      <div>
        <div class="brand">{proyecto}</div>
        <div class="meta">Generado: {fecha_txt}</div>
      </div>
      <div class="health">
        <span class="dot" style="background-color:{semaf_color};"></span>
        <div>
          <div class="score">Salud {salud if salud is not None else '-'}</div>
          <div class="meta">{semaf.capitalize() if semaf else ''}</div>
        </div>
      </div>
    </header>

    <section class="card">
      <h2>Resumen ejecutivo</h2>
      <p class="resumen">{resumen}</p>
    </section>

    <section class="card">
      <h2>KPIs del proyecto</h2>
      <div class="kpis">{kpi_cards}</div>
    </section>

    {casos_html}

    {secs_html}
  </div>
</body></html>"""


# dal/analytics_dal.py
def list_casos(modulo: str) -> list[dict]:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("EXEC dbo.sp_Ana_CasoCatalogo_Listar ?", (modulo,))
        return _rows_to_dicts(cur)
    finally:
        con.close()

def insert_run_casos(run_id: int, casos_resueltos: list[dict]) -> None:
    con = get_connection()
    try:
        cur = con.cursor()
        payload = json.dumps(casos_resueltos, ensure_ascii=False)
        cur.execute("EXEC dbo.sp_Ana_RunCasos_Insertar ?, ?", (run_id, payload))
        con.commit()
    finally:
        con.close()

def get_reportes(
    proyecto_id: Optional[int] = None,
    solo_activos: Optional[bool] = False,
    estado: Optional[str] = None,
    semaforo: Optional[str] = None,  # ✅ Agregar parámetro semáforo
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    buscar: Optional[str] = None,
    top: Optional[int] = 50
) -> List[Dict[str, Any]]:
    con = get_connection()
    try:
        cur = con.cursor()
        solo_activos_int = 1 if solo_activos else 0
        
        cur.execute("""
            EXEC dbo.sp_Ana_Reportes_Listar
                @ProyectoID = ?,
                @SoloActivos = ?,
                @Estado = ?,
                @Semaforo = ?,
                @Desde = ?,
                @Hasta = ?,
                @Buscar = ?,
                @Top = ?
        """, (proyecto_id, solo_activos_int, estado, semaforo, desde, hasta, buscar, top))
        
        return _rows_to_dicts(cur)
    finally:
        con.close()
        
    
def get_proyectos() -> List[Dict[str, Any]]:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT [ProyectoID], [NombreProyecto]
            FROM [LOGS].[dbo].[Proyecto]
            ORDER BY [NombreProyecto]
        """)
        return _rows_to_dicts(cur)
    finally:
        con.close()