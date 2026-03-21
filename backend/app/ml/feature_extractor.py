"""Feature engineering avanzado para modelos de ML."""

import math
import re
from collections import Counter
from datetime import datetime


# Patrones sospechosos en URLs
SUSPICIOUS_URL_PATTERNS = [
    r"\.\./",           # directory traversal
    r"etc/passwd",
    r"etc/shadow",
    r"proc/self",
    r"union\s+select",  # SQL injection
    r"or\s+1\s*=\s*1",
    r"drop\s+table",
    r"<script",         # XSS
    r"javascript:",
    r"%3[cC]script",
    r"cmd=",            # command injection
    r"exec\(",
    r"system\(",
    r"\.php\?",         # PHP probing
    r"wp-admin",
    r"phpmyadmin",
    r"\.env",           # sensitive file access
    r"\.git/",
    r"\.ssh/",
]
SUSPICIOUS_RE = re.compile("|".join(SUSPICIOUS_URL_PATTERNS), re.IGNORECASE)

# Event types de alto riesgo
HIGH_RISK_EVENTS = {"ssh_login_failed", "ssh_invalid_user"}
MEDIUM_RISK_EVENTS = {"sudo_command"}


def compute_entropy(text: str) -> float:
    """Calcula la entropía de Shannon de un string (bits)."""
    if not text:
        return 0.0
    freq = Counter(text)
    length = len(text)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in freq.values()
    )


def extract_features(event: dict) -> list[float]:
    """Extrae un vector de features numéricas de un evento.

    Features (15 dimensiones):
    0.  severity_score           - Score de severidad original (0-1)
    1.  is_high_risk_event       - 1 si es ssh_failed/invalid_user
    2.  is_medium_risk_event     - 1 si es sudo_command
    3.  is_error_level           - 1 si log_level es ERROR/CRITICAL
    4.  is_warning_level         - 1 si log_level es WARNING
    5.  has_source_ip            - 1 si tiene IP de origen
    6.  hour_sin                 - Componente seno de la hora (patrón circadiano)
    7.  hour_cos                 - Componente coseno de la hora
    8.  is_night                 - 1 si es entre 00:00-06:00 (actividad sospechosa)
    9.  is_weekend               - 1 si es sábado/domingo
    10. http_status_normalized   - Código HTTP normalizado (0-1), 0 si no aplica
    11. url_length_normalized    - Longitud de URL normalizada, 0 si no aplica
    12. url_suspicious_score     - Cantidad de patrones sospechosos en URL
    13. message_entropy          - Entropía de Shannon del mensaje raw
    14. has_username             - 1 si tiene username
    """
    parsed = event.get("message_parsed") or {}
    event_type = event.get("event_type", "")
    log_level = event.get("log_level", "INFO")
    timestamp = event.get("timestamp_utc")

    # Features básicas
    severity = float(event.get("severity_score", 0.0))
    is_high_risk = 1.0 if event_type in HIGH_RISK_EVENTS else 0.0
    is_medium_risk = 1.0 if event_type in MEDIUM_RISK_EVENTS else 0.0
    is_error = 1.0 if log_level in ("ERROR", "CRITICAL") else 0.0
    is_warning = 1.0 if log_level == "WARNING" else 0.0
    has_ip = 1.0 if event.get("source_ip") else 0.0
    has_username = 1.0 if event.get("username") else 0.0

    # Features temporales (patrón circadiano)
    hour = 12.0  # default mediodía
    is_night = 0.0
    is_weekend = 0.0
    if isinstance(timestamp, datetime):
        hour = timestamp.hour + timestamp.minute / 60.0
        is_night = 1.0 if 0 <= timestamp.hour < 6 else 0.0
        is_weekend = 1.0 if timestamp.weekday() >= 5 else 0.0

    # Codificación cíclica de la hora (sin, cos)
    hour_sin = math.sin(2 * math.pi * hour / 24.0)
    hour_cos = math.cos(2 * math.pi * hour / 24.0)

    # Features HTTP
    status = parsed.get("status", 0)
    http_status_norm = float(status) / 600.0 if status else 0.0

    url = parsed.get("url", "")
    url_length_norm = min(len(url) / 500.0, 1.0) if url else 0.0

    # Score de URL sospechosa
    url_suspicious = 0.0
    if url:
        matches = SUSPICIOUS_RE.findall(url)
        url_suspicious = min(len(matches) / 3.0, 1.0)  # normalizado a 0-1

    # Entropía del mensaje
    message_raw = event.get("message_raw", "")
    entropy = compute_entropy(message_raw)
    entropy_norm = min(entropy / 6.0, 1.0)  # log2(128) ≈ 7, normalizamos

    return [
        severity,            # 0
        is_high_risk,        # 1
        is_medium_risk,      # 2
        is_error,            # 3
        is_warning,          # 4
        has_ip,              # 5
        hour_sin,            # 6
        hour_cos,            # 7
        is_night,            # 8
        is_weekend,          # 9
        http_status_norm,    # 10
        url_length_norm,     # 11
        url_suspicious,      # 12
        entropy_norm,        # 13
        has_username,        # 14
    ]


FEATURE_NAMES = [
    "severity_score",
    "is_high_risk_event",
    "is_medium_risk_event",
    "is_error_level",
    "is_warning_level",
    "has_source_ip",
    "hour_sin",
    "hour_cos",
    "is_night",
    "is_weekend",
    "http_status_normalized",
    "url_length_normalized",
    "url_suspicious_score",
    "message_entropy",
    "has_username",
]

N_FEATURES = len(FEATURE_NAMES)
