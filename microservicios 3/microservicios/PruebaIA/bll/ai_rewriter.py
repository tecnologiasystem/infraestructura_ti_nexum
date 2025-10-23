# bll/ai_rewriter.py
import os, re, json, requests
from typing import Dict, Any, Tuple, Literal
from dal import analytics_dal as dal

def _html_to_text(html: str) -> str:
    s = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", html or "")
    s = re.sub(r"(?is)<br\s*/?>", "\n", s)
    s = re.sub(r"(?is)</(p|div|li|h[1-6]|section|article)>", "\n", s)
    s = re.sub(r"(?is)<li\b[^>]*>", "- ", s)
    s = re.sub(r"(?is)<[^>]+>", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()

def _render_html_from_json(j: Dict[str, Any]) -> str:
    def ul(items): 
        return "" if not items else "<ul>" + "".join(f"<li>{str(x)}</li>" for x in items) + "</ul>"
    title = j.get("title") or "Resumen del proyecto"
    resumen = j.get("executive_summary") or ""
    return f"""
    <section class="card">
      <h2>{title}</h2>
      <p>{resumen}</p>
      <h3>Puntos clave</h3>{ul(j.get("takeaways") or [])}
      <h3>Próximas acciones</h3>{ul(j.get("actions") or [])}
      <h3>Riesgos</h3>{ul(j.get("risks") or [])}
      <h3>KPIs</h3>{ul(j.get("kpis") or [])}
    </section>
    """
def _coerce_json(raw: str) -> dict:
    """Convierte texto 'casi JSON' en JSON: quita ```json, comillas curvas y comas colgantes."""
    s = (raw or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, flags=re.I)
    if m:
        s = m.group(1).strip()
    if not (s.startswith("{") and s.endswith("}")):
        m2 = re.search(r"\{[\s\S]*\}", s)
        if m2:
            s = m2.group(0)
    s = s.replace("“", "\"").replace("”", "\"").replace("’", "'")
    s = re.sub(r",\s*([}\]])", r"\1", s)  # ,} o ,]
    return json.loads(s)

def _normalize_lists(obj: dict) -> dict:
    """Convierte listas de dicts a bullets legibles."""
    def to_list(val):
        if isinstance(val, list):
            out = []
            for it in val:
                if isinstance(it, dict):
                    t = str(it.get("title", "")).strip()
                    d = str(it.get("description", "")).strip()
                    s = (t + (": " if t and d else "") + d).strip(": ").strip()
                    if s: out.append(s)
                else:
                    out.append(str(it))
            return out
        return [] if val is None else [str(val)]
    for k in ("takeaways","actions","risks","kpis"):
        obj[k] = to_list(obj.get(k))
    return obj


def _ollama_rewrite(texto: str, audiencia: str) -> Dict[str, Any]:
    host = os.getenv("OLLAMA_HOST", "http://172.18.73.188:11434").rstrip("/")
    model = os.getenv("AI_MODEL", "phi3:latest")

    # ======= KNOBS por entorno =======
    max_chars    = int(os.getenv("IA_MAX_CHARS", "12000"))   # tamaño máx del texto de entrada
    num_ctx      = int(os.getenv("IA_NUM_CTX", "8192"))      # contexto del modelo (si tu build lo soporta)
    num_predict  = int(os.getenv("IA_NUM_PREDICT", "-1"))    # -1 = ilimitado (hasta EOS/stop)
    timeout_sec  = int(os.getenv("IA_TIMEOUT", "600"))       # timeout HTTP
    # =================================

    if len(texto) > max_chars:
        texto = texto[:max_chars]

    system = ("Eres un revisor PMO. Reescribe el informe para que sea claro y accionable, "
              "sin inventar datos (conserva números/fechas). Devuelve SOLO JSON válido sin ```.")
    schema = {
        "title": "string",
        "audience": audiencia,
        "executive_summary": "string",
        "takeaways": ["string"],
        "actions": ["string"],
        "risks": ["string"],
        "kpis": ["string"],
        "improved_html": "string"
    }
    prompt = (
        f"{system}\n\n"
        f"Responde EXACTAMENTE un único objeto JSON con estas claves, sin texto extra:\n"
        f"{json.dumps(schema, ensure_ascii=False)}\n"
        f"- Español neutro, frases cortas. Máx 6 acciones y 5 riesgos.\n"
        f"- No encierres el objeto JSON en comillas. No uses ```.\n\n"
        f"INFORME ORIGINAL (TEXTO):\n{texto}\n"
    )

    session = requests.Session()
    session.trust_env = False  # ignora HTTP(S)_PROXY del sistema

    def _call_llm(pmt: str) -> str:
        r = session.post(
            f"{host}/api/generate",
            headers={"Content-Type":"application/json"},
            json={
                "model": model,
                "prompt": pmt,
                "stream": False,
                "format": "json",
                "options": {
                    "num_ctx": num_ctx,
                    "num_predict": num_predict,   # ← ilimitado si pones -1
                    "temperature": 0.2
                }
            },
            timeout=timeout_sec,
            proxies={"http": None, "https": None}
        )
        r.raise_for_status()
        return r.json().get("response", "")

    # 1) Primer intento (JSON completo)
    raw = _call_llm(prompt)
    try:
        obj = _coerce_json(raw)          # usa tu helper tolerante
    except Exception:
        # 2) Auto-continuación si parece cortado (faltan llaves de cierre)
        #    - Busca el último '{' y el balance de '{' vs '}'.
        open_braces = raw.count("{")
        close_braces = raw.count("}")
        if open_braces > close_braces:
            cont_prompt = (
                "Continúa EXACTAMENTE el JSON anterior desde el último carácter, "
                "sin repetir nada y sin agregar texto fuera del objeto. "
                "No uses ```.\n"
                "Debes cerrar correctamente todas las llaves y corchetes."
            )
            continuation = _call_llm(cont_prompt)
            raw = raw + continuation  # concatenar continuación e intentar parsear de nuevo
        # Reintenta parseo (si falla, devolvemos texto bruto como antes)
        try:
            obj = _coerce_json(raw)
        except Exception:
            return {
                "title": "Resumen del proyecto",
                "audience": audiencia,
                "executive_summary": raw,
                "takeaways": [], "actions": [], "risks": [], "kpis": [],
                "parse_warning": "La IA no devolvió JSON estricto; se incluyó texto bruto (con posible continuación)."
            }

    # Normalización mínima
    for k in ("takeaways","actions","risks","kpis"):
        obj.setdefault(k, [])
    obj = _normalize_lists(obj)  # tu helper: convierte objetos {title,description} a bullets
    obj.setdefault("title", "Resumen del proyecto")
    return obj






def rewrite_run_report(run_id: int,
                       audiencia: Literal["ejecutiva","operativa","ambas"]="ejecutiva"
                      ) -> Tuple[Dict[str,Any], str]:
    """
    No persiste nada (Plan B). Toma el HTML existente, pide reescritura a Ollama y devuelve (json, html_final).
    """
    # 1) HTML original desde tu DAL
    original_html = dal.get_informe_html(run_id)  # 👈 existe en tu DAL
    # 2) Enviar a IA
    texto = _html_to_text(original_html)
    j = _ollama_rewrite(texto, audiencia=audiencia)
    improved_html = j.get("improved_html") or _render_html_from_json(j)

    # 3) (Opcional) incrustar al inicio del informe original
    final_html = original_html.replace(
        '<div class="wrap">', '<div class="wrap">\n<section class="card"><h2>Versión IA</h2>'
        + improved_html + "</section>\n", 1
    ) if '<div class="wrap">' in original_html else improved_html

    return j, final_html
