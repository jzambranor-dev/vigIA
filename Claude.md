# CLAUDE.md — Analizador de Logs con IA (Proyecto 4.8)

## Descripción del Proyecto

Sistema de análisis de logs de servidores Linux con Inteligencia Artificial para detección automática de anomalías y ataques de seguridad. Genera alertas en tiempo real y reportes ejecutivos PDF para administradores de sistemas.

**Repositorio:** `github.com/jzambranor-dev/log-analyzer-ai`
**Entorno objetivo:** Servidores Debian GNU/Linux 11/12 (Bullseye/Bookworm)

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend / API | Python 3.11 + FastAPI 0.110+ |
| Machine Learning | scikit-learn 1.4 + pandas 2.0 + numpy 1.26 |
| Base de datos | PostgreSQL 16 + Redis 7 |
| Frontend | Vue 3 + Vite + Tailwind CSS 3 |
| Reportes PDF | ReportLab 4.0 |
| Contenedores | Docker Compose 2.24 |
| Testing | pytest 8.0 + pytest-asyncio |

---

## Estructura de Carpetas Objetivo

```
log-analyzer-ai/
├── CLAUDE.md                  ← este archivo
├── README.md
├── docker-compose.yml         ← orquestación principal
├── docker-compose.dev.yml     ← overrides para desarrollo
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py            ← entrypoint FastAPI
│   │   ├── config.py          ← settings con pydantic-settings
│   │   ├── database.py        ← conexión PostgreSQL async
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── event.py       ← modelo LogEvent
│   │   │   └── alert.py       ← modelo Alert
│   │   ├── schemas/
│   │   │   ├── event.py       ← schemas Pydantic
│   │   │   └── alert.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── events.py      ← GET /api/events
│   │   │   ├── alerts.py      ← GET /api/alerts
│   │   │   ├── stats.py       ← GET /api/stats/summary
│   │   │   └── reports.py     ← GET /api/reports/pdf
│   │   ├── core/
│   │   │   ├── ingester.py    ← watchdog file watcher
│   │   │   ├── parser.py      ← regex engine multi-formato
│   │   │   ├── normalizer.py  ← JSON schema unificado
│   │   │   ├── enricher.py    ← GeoIP + AbuseIPDB
│   │   │   ├── detector.py    ← Isolation Forest + reglas
│   │   │   └── alert_engine.py← Motor de alertas
│   │   ├── ml/
│   │   │   ├── trainer.py     ← entrenamiento de modelos
│   │   │   ├── predictor.py   ← inferencia en tiempo real
│   │   │   └── models/        ← modelos .pkl serializados
│   │   ├── websocket/
│   │   │   └── manager.py     ← WS /ws/events
│   │   └── utils/
│   │       ├── logger.py
│   │       └── pdf_generator.py
│   └── tests/
│       ├── conftest.py
│       ├── test_parser.py
│       ├── test_detector.py
│       └── test_api.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js
│       ├── stores/            ← Pinia stores
│       │   ├── events.js
│       │   └── alerts.js
│       ├── components/
│       │   ├── Dashboard.vue
│       │   ├── EventsTable.vue
│       │   ├── AlertsPanel.vue
│       │   └── StatsChart.vue
│       └── views/
│           ├── HomeView.vue
│           ├── EventsView.vue
│           └── ReportsView.vue
│
├── nginx/
│   └── nginx.conf             ← reverse proxy hacia FastAPI y Vue
│
└── scripts/
    ├── generate_sample_logs.py ← genera logs de prueba con ataques simulados
    ├── train_model.py          ← script standalone para entrenar modelos
    └── seed_db.py              ← datos iniciales para demo
```

---

## Primera Tarea: Esqueleto Base

**Genera todo lo siguiente en orden:**

### 1. `docker-compose.yml`

```yaml
# Servicios requeridos:
# - postgres:16-alpine  → puerto 5432, volumen persistente
# - redis:7-alpine      → puerto 6379
# - backend             → build ./backend, puerto 8000, depende de postgres y redis
# - frontend            → build ./frontend, puerto 3000
# - nginx               → puerto 80, reverse proxy a backend:8000 y frontend:3000

# Variables de entorno desde .env
# Red interna: app-network (bridge)
# Healthchecks en postgres y redis
```

### 2. `.env.example`

```
# PostgreSQL
POSTGRES_DB=loganalyzer
POSTGRES_USER=loguser
POSTGRES_PASSWORD=changeme
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# FastAPI
SECRET_KEY=changeme-in-production
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Logs a monitorear (separados por coma)
LOG_PATHS=/var/log/auth.log,/var/log/syslog,/var/log/apache2/access.log

# Alertas por email (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ALERT_EMAIL_TO=

# AbuseIPDB (opcional, enriquecimiento de IPs)
ABUSEIPDB_API_KEY=
```

### 3. `backend/requirements.txt`

```
fastapi==0.110.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.29
asyncpg==0.29.0
alembic==1.13.1
pydantic-settings==2.2.1
redis==5.0.3
watchdog==4.0.0
scikit-learn==1.4.1.post1
pandas==2.2.1
numpy==1.26.4
joblib==1.3.2
reportlab==4.1.0
httpx==0.27.0
python-multipart==0.0.9
websockets==12.0
pytest==8.0.2
pytest-asyncio==0.23.6
pytest-cov==5.0.0
```

### 4. `backend/Dockerfile`

```dockerfile
# Base: python:3.11-slim
# Instala dependencias del sistema para ReportLab y asyncpg
# WORKDIR /app
# Copia requirements.txt primero (cache de capas)
# RUN pip install --no-cache-dir -r requirements.txt
# Copia el resto del código
# CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. `backend/app/main.py`

```python
# FastAPI app con:
# - CORS habilitado para http://localhost:3000
# - Routers incluidos: events, alerts, stats, reports
# - Endpoint GET / → {"status": "ok", "project": "Log Analyzer AI"}
# - Endpoint WS /ws/events → stream de eventos en tiempo real
# - Lifespan: conectar a DB al iniciar, cerrar al apagar
```

### 6. `backend/app/config.py`

```python
# Clase Settings con pydantic-settings
# Lee todas las variables del .env
# DATABASE_URL construida desde variables POSTGRES_*
# Singleton: settings = Settings()
```

### 7. `backend/app/database.py`

```python
# SQLAlchemy async engine con asyncpg
# AsyncSessionLocal como async_sessionmaker
# Base declarativa para modelos
# Función get_db() como dependency de FastAPI
```

### 8. `backend/app/models/event.py`

```python
# Tabla: log_events
# Campos:
#   id (UUID, PK)
#   timestamp_utc (DateTime, indexed)
#   source_file (String)
#   log_level (String)           # INFO, WARNING, ERROR, CRITICAL
#   event_type (String, indexed) # ssh_login, brute_force, apache_access, sudo, etc.
#   source_ip (String, indexed, nullable)
#   username (String, nullable)
#   message_raw (Text)
#   message_parsed (JSON)
#   severity_score (Float)       # 0.0 a 1.0
#   is_anomaly (Boolean, default False)
#   created_at (DateTime, server_default=now())
```

### 9. `backend/app/models/alert.py`

```python
# Tabla: alerts
# Campos:
#   id (UUID, PK)
#   event_id (UUID, FK → log_events.id)
#   severity (String)            # CRITICAL, HIGH, MEDIUM, LOW
#   alert_type (String)          # brute_force, sql_injection, directory_traversal, etc.
#   description (Text)
#   source_ip (String, nullable)
#   acknowledged (Boolean, default False)
#   acknowledged_at (DateTime, nullable)
#   created_at (DateTime, server_default=now())
```

### 10. `backend/app/core/parser.py`

```python
# Clase LogParser con patrones regex compilados para:
#
# AUTH.LOG:
#   - SSH login exitoso: "Accepted password for {user} from {ip} port {port}"
#   - SSH login fallido: "Failed password for {user} from {ip}"
#   - SSH invalid user: "Invalid user {user} from {ip}"
#   - sudo: "sudo: {user} : TTY={tty} ; PWD={pwd} ; USER=root ; COMMAND={cmd}"
#
# APACHE ACCESS.LOG (Combined Log Format):
#   - {ip} - {user} [{timestamp}] "{method} {url} HTTP/{version}" {status} {bytes}
#
# SYSLOG:
#   - Formato estándar: {month} {day} {time} {host} {process}[{pid}]: {message}
#
# Método parse(line: str, source_file: str) → dict | None
# Retorna None si la línea no coincide con ningún patrón
```

### 11. `backend/app/core/alert_engine.py`

```python
# Clase AlertEngine con reglas:
#
# BRUTE_FORCE_SSH:
#   - Condición: >= 5 "Failed password" de la misma IP en 60 segundos
#   - Severidad: HIGH (>= 5) / CRITICAL (>= 20)
#
# BRUTE_FORCE_WEB:
#   - Condición: >= 10 respuestas 401/403 de la misma IP en 60 segundos
#   - Severidad: HIGH
#
# DIRECTORY_TRAVERSAL:
#   - Condición: URL contiene "../" o "..%2F" o "etc/passwd"
#   - Severidad: CRITICAL
#
# SQL_INJECTION:
#   - Condición: URL contiene patterns SQL (UNION SELECT, OR 1=1, DROP TABLE, etc.)
#   - Severidad: CRITICAL
#
# SUDO_ROOT:
#   - Condición: comando sudo hacia root por usuario no habitual
#   - Severidad: MEDIUM
#
# Usa Redis para contadores con TTL (ventana de tiempo)
# Método evaluate(event: dict) → Alert | None
```

### 12. `frontend/package.json`

```json
{
  "dependencies": ["vue@^3.4", "vue-router@^4.3", "pinia@^2.1", "axios@^1.6", "chart.js@^4.4", "vue-chartjs@^5.3"],
  "devDependencies": ["vite@^5.2", "@vitejs/plugin-vue@^5.0", "tailwindcss@^3.4", "autoprefixer@^10.4"]
}
```

### 13. `nginx/nginx.conf`

```nginx
# upstream backend → backend:8000
# upstream frontend → frontend:3000
# server listen 80:
#   /api/ → proxy_pass backend
#   /ws/  → proxy_pass backend (upgrade WebSocket)
#   /     → proxy_pass frontend
```

### 14. `scripts/generate_sample_logs.py`

```python
# Genera un archivo sample_logs.log con:
# - 500 líneas de acceso normal Apache
# - 50 líneas de fuerza bruta SSH (misma IP, usuario root)
# - 10 líneas de directory traversal
# - 5 líneas de SQL injection en URL
# - 20 líneas de auth.log normal (logins exitosos)
# Útil para testing y demostración del proyecto de titulación
```

---

## Flujo de Datos (referencia para implementación)

```
[Archivo de Log]
      │
      ▼
[ingester.py] ──watchdog──► detecta cambios en tiempo real
      │
      ▼
[parser.py] ──regex──► extrae campos estructurados
      │
      ▼
[normalizer.py] ──► JSON unificado (schema LogEvent)
      │
      ▼
[enricher.py] ──► agrega GeoIP, reputación IP (async)
      │
      ▼
[detector.py] ──► Isolation Forest + motor de reglas
      │
      ├──► [PostgreSQL] ──► persiste LogEvent
      │
      └──► [alert_engine.py] ──► crea Alert si corresponde
                │
                ├──► [PostgreSQL] ──► persiste Alert
                ├──► [Redis] ──► actualiza contadores
                └──► [WebSocket] ──► push al dashboard Vue 3
```

---

## Convenciones de Código

- **Python:** PEP8 estricto, type hints en todas las funciones, docstrings en clases y métodos públicos
- **Async:** Usar `async/await` en todos los accesos a DB y operaciones I/O
- **Errores:** Nunca silenciar excepciones; loggear con `logging` estándar de Python
- **Variables de entorno:** Siempre desde `config.settings`, nunca `os.environ` directo
- **Vue 3:** Composition API con `<script setup>`, Pinia para estado global
- **Commits:** Convención `feat:`, `fix:`, `docs:`, `test:` (Conventional Commits)

---

## Comandos de Desarrollo

```bash
# Levantar todo el stack
docker compose up -d

# Solo backend en modo desarrollo (con hot reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up backend

# Ejecutar migraciones
docker compose exec backend alembic upgrade head

# Correr tests con cobertura
docker compose exec backend pytest --cov=app tests/ -v

# Generar logs de prueba
docker compose exec backend python scripts/generate_sample_logs.py

# Ver logs del backend en tiempo real
docker compose logs -f backend
```

---

## Contexto del Entorno de Producción

- **OS:** Debian GNU/Linux 11 (Bullseye) / 12 (Bookworm)
- **Servidor:** VPS con Nginx como reverse proxy externo
- **Logs reales disponibles:** `/var/log/auth.log`, `/var/log/syslog`, `/var/log/apache2/access.log`
- **Aplicaciones en producción generando logs:** Moodle (PHP), WordPress, Laravel CRM
- **Volúmenes Docker:** Los logs del host se montan como read-only dentro del contenedor backend

```yaml
# En docker-compose.yml, el servicio backend debe montar:
volumes:
  - /var/log:/host/logs:ro   # logs del host, solo lectura
```

---

## Estado Actual del Proyecto

- [ ] Esqueleto base (docker-compose + estructura) → **PRIMERA TAREA**
- [ ] Módulo de ingesta y parser (ingester.py + parser.py)
- [ ] Modelos DB + migraciones Alembic
- [ ] Motor de reglas (alert_engine.py)
- [ ] Modelo Isolation Forest (detector.py + trainer.py)
- [ ] API REST (events, alerts, stats, reports)
- [ ] WebSocket de tiempo real
- [ ] Dashboard Vue 3
- [ ] Generador de reportes PDF
- [ ] Tests unitarios (cobertura >= 80%)
- [ ] Documentación técnica completa
