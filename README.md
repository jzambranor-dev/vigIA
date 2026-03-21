# VigIA — Analizador de Logs con Inteligencia Artificial

Sistema de análisis de logs de servidores Linux con IA para detección automática de anomalías y ataques de seguridad. Genera alertas en tiempo real y reportes ejecutivos PDF.

## Arquitectura

```
[Archivos de Log del Host]
        │ (montados read-only)
        ▼
[Ingester] ── watchdog ──► detecta cambios en tiempo real
        │
        ▼
[Parser] ── regex multi-formato ──► extrae campos estructurados
        │
        ▼
[Normalizer] ──► JSON unificado (schema LogEvent)
        │
        ▼
[Enricher] ──► GeoIP + reputación IP (AbuseIPDB)
        │
        ▼
[Detector] ──► Isolation Forest (ML) + reglas heurísticas
        │
        ├──► [PostgreSQL] ──► persiste LogEvent
        │
        └──► [Alert Engine] ──► evalúa reglas de seguridad
                │
                ├──► [PostgreSQL] ──► persiste Alert
                ├──► [Redis] ──► contadores con TTL
                └──► [WebSocket] ──► push al dashboard
```

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend / API | Python 3.11 + FastAPI |
| Machine Learning | scikit-learn (Isolation Forest) |
| Base de datos | PostgreSQL 16 + Redis 7 |
| Frontend | Vue 3 + Tailwind CSS / Flask + Jinja2 |
| Reportes PDF | ReportLab |
| Contenedores | Docker Compose |
| Testing | pytest + pytest-asyncio (83% cobertura) |

## Requisitos

- Docker + Docker Compose v2
- Git
- Servidor Linux con logs en `/var/log/`

## Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/jzambranor-dev/log-analyzer-ai.git
cd log-analyzer-ai

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con credenciales reales

# 3. Construir y levantar
docker compose build
docker compose up -d

# 4. Ejecutar migraciones
docker compose exec backend alembic upgrade head

# 5. (Opcional) Cargar datos de ejemplo
docker compose exec backend python -c "
import sys; sys.path.insert(0, '/app')
# ... seed script
"
```

## Puertos (por defecto)

| Servicio | Puerto |
|----------|--------|
| PostgreSQL | 5434 |
| Redis | 6380 |
| Backend (FastAPI) | 8002 |
| Frontend (Vue 3) | 3010 |
| Nginx (reverse proxy) | 8088 |
| Dashboard Flask | 5050 |

## API REST

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/events/` | GET | Listar eventos (filtros: event_type, source_ip, is_anomaly) |
| `/api/events/{id}` | GET | Detalle de un evento |
| `/api/alerts/` | GET | Listar alertas (filtros: severity, alert_type, acknowledged) |
| `/api/alerts/{id}` | GET | Detalle de una alerta |
| `/api/alerts/{id}/acknowledge` | PATCH | Reconocer alerta |
| `/api/stats/summary` | GET | Estadísticas generales |
| `/api/reports/pdf` | GET | Descargar reporte PDF |
| `/ws/events` | WS | Stream de eventos en tiempo real |

## Tipos de Eventos Detectados

- `ssh_login_accepted` — Login SSH exitoso
- `ssh_login_failed` — Intento de login SSH fallido
- `ssh_invalid_user` — Intento con usuario inexistente
- `sudo_command` — Comando ejecutado con sudo
- `apache_access` — Acceso HTTP (Apache Combined Log Format)
- `syslog` — Eventos genéricos de syslog

## Reglas de Alerta

| Regla | Condición | Severidad |
|-------|-----------|-----------|
| Fuerza bruta SSH | >= 5 fallos misma IP en 60s | HIGH / CRITICAL (>= 20) |
| Fuerza bruta Web | >= 10 errores 401/403 misma IP en 60s | HIGH |
| Directory Traversal | URL con `../`, `etc/passwd` | CRITICAL |
| SQL Injection | URL con `UNION SELECT`, `OR 1=1`, etc. | CRITICAL |
| Sudo a Root | Comando sudo hacia root | MEDIUM |

## Modelo de Machine Learning

**Isolation Forest** entrenado con 1050 muestras (1000 normales + 50 anómalas).

Features:
1. `severity_score` — Score de severidad del evento (0.0 - 1.0)
2. `is_ssh_failed` — Si es un intento SSH fallido
3. `is_error_level` — Si el nivel es ERROR o CRITICAL
4. `status_normalized` — Código HTTP normalizado
5. `has_ip` — Si tiene IP de origen

Cuando no hay modelo entrenado, el sistema usa detección por reglas heurísticas como fallback.

## Tests

```bash
# Ejecutar todos los tests
cd backend
python3 -m pytest tests/ -v

# Con cobertura
python3 -m pytest tests/ --cov=app --cov-config=.coveragerc --cov-report=term-missing

# Cobertura actual: 83% (98 tests)
```

## Estructura del Proyecto

```
vigIA/
├── backend/              # API FastAPI + ML + Core
│   ├── app/
│   │   ├── api/          # Routers REST (events, alerts, stats, reports)
│   │   ├── core/         # Parser, detector, alert engine, ingester
│   │   ├── ml/           # Isolation Forest trainer/predictor
│   │   ├── models/       # SQLAlchemy (LogEvent, Alert)
│   │   ├── schemas/      # Pydantic validation
│   │   ├── utils/        # Logger, PDF generator
│   │   └── websocket/    # WebSocket manager
│   ├── tests/            # 98 tests, 83% cobertura
│   └── alembic/          # Migraciones DB
├── frontend/             # Vue 3 + Tailwind CSS
├── dashboard/            # Flask dashboard (server-side rendering)
├── nginx/                # Reverse proxy config
├── scripts/              # Utilidades (seed, train, generate logs)
├── docker-compose.yml    # Orquestación de servicios
└── .env.example          # Variables de entorno
```

## Comandos Útiles

```bash
# Levantar todo
docker compose up -d

# Ver logs del backend
docker compose logs -f backend

# Ejecutar migraciones
docker compose exec backend alembic upgrade head

# Entrenar modelo ML
docker compose exec backend python -c "exec(open('train_inline.py').read())"

# Generar logs de prueba
python3 scripts/generate_sample_logs.py

# Correr tests
cd backend && python3 -m pytest tests/ -v --cov=app
```

## Autor

**J. Zambrano R.** — Proyecto de Titulación

## Licencia

Uso académico y educativo.
