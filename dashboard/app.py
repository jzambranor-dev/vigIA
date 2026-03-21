"""Dashboard Flask para visualizar Log Analyzer AI."""

import httpx
from flask import Flask, render_template, Response
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_prefix=1)

# Prefijo para que funcione detrás de Apache en /vigia/
PREFIX = "/vigia"
API_BASE = "http://localhost:8002"


def api_get(endpoint: str, params: dict = None) -> dict | list | None:
    """Consulta la API de FastAPI."""
    try:
        r = httpx.get(f"{API_BASE}{endpoint}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error API {endpoint}: {e}")
        return None


@app.context_processor
def inject_prefix():
    """Inyecta PREFIX en todos los templates."""
    return {"PREFIX": PREFIX}


@app.route("/")
def dashboard():
    """Página principal con resumen."""
    stats = api_get("/api/stats/summary") or {}
    alerts = api_get("/api/alerts/", {"limit": 10}) or {"items": [], "total": 0}
    events = api_get("/api/events/", {"limit": 5}) or {"items": [], "total": 0}
    ml_status = api_get("/api/ml/status") or {}
    return render_template(
        "dashboard.html",
        stats=stats,
        alerts=alerts["items"],
        events=events["items"],
        total_events=events["total"],
        ml_status=ml_status,
    )


@app.route("/events")
def events_page():
    """Tabla completa de eventos."""
    events = api_get("/api/events/", {"limit": 100}) or {"items": [], "total": 0}
    return render_template("events.html", events=events["items"], total=events["total"])


@app.route("/alerts")
def alerts_page():
    """Panel de alertas."""
    alerts = api_get("/api/alerts/", {"limit": 100}) or {"items": [], "total": 0}
    return render_template("alerts.html", alerts=alerts["items"], total=alerts["total"])


@app.route("/ml")
def ml_page():
    """Estado y métricas de los modelos de ML."""
    ml_status = api_get("/api/ml/status") or {}
    return render_template("ml.html", ml_status=ml_status)


@app.route("/reports/pdf")
def download_pdf():
    """Descarga el reporte PDF."""
    try:
        r = httpx.get(f"{API_BASE}/api/reports/pdf", timeout=30)
        return Response(
            r.content,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=reporte_seguridad.pdf"},
        )
    except Exception as e:
        return f"Error generando PDF: {e}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
