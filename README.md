# VigIA — Analizador de Logs con Inteligencia Artificial

Sistema de analisis de logs de servidores Linux con IA para deteccion automatica de anomalias y ataques de seguridad. Genera alertas en tiempo real y reportes ejecutivos PDF.

## Arquitectura

```
[Archivos de Log del Host]
        | (montados read-only)
        v
[Ingester] -- watchdog --> detecta cambios en tiempo real
        |
        v
[Parser] -- regex multi-formato --> extrae campos estructurados
        |
        v
[Normalizer] --> JSON unificado (schema LogEvent)
        |
        v
[Enricher] --> GeoIP + reputacion IP (AbuseIPDB)
        |
        v
[Detector] --> Isolation Forest + Random Forest (ML) + reglas heuristicas
        |
        +---> [PostgreSQL] --> persiste LogEvent
        |
        +---> [Alert Engine] --> evalua reglas de seguridad
        |       |
        |       +---> [PostgreSQL] --> persiste Alert
        |       +---> [Redis] --> contadores con TTL
        |       +---> [WebSocket] --> push al dashboard
        |
        +---> [Sequence Analyzer] --> deteccion de ataques multi-paso
```

## Stack Tecnologico

| Capa | Tecnologia |
|------|-----------|
| Backend / API | Python 3.11 + FastAPI |
| Autenticacion | JWT (python-jose + passlib/bcrypt) |
| Machine Learning | scikit-learn (Isolation Forest + Random Forest) |
| Base de datos | PostgreSQL 16 + Redis 7 |
| Frontend | Vue 3 + Pinia + Tailwind CSS |
| Reportes PDF | ReportLab |
| Contenedores | Docker Compose |
| Rate Limiting | slowapi |
| Testing | pytest + pytest-asyncio (83% cobertura) |

## Requisitos

- Docker + Docker Compose v2
- Git
- Servidor Linux con logs en `/var/log/`

## Instalacion

```bash
# 1. Clonar repositorio
git clone https://github.com/jzambranor-dev/vigIA.git
cd vigIA

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con credenciales seguras (SECRET_KEY, POSTGRES_PASSWORD, ADMIN_PASSWORD)

# 3. Construir y levantar
docker compose build
docker compose up -d

# 4. Ejecutar migraciones
docker compose exec backend alembic upgrade head

# El usuario admin se crea automaticamente al iniciar el backend
```

## Puertos (por defecto, solo 127.0.0.1)

| Servicio | Puerto |
|----------|--------|
| PostgreSQL | 5434 |
| Redis | 6380 |
| Backend (FastAPI) | 8002 |
| Frontend (Vue 3) | 3010 |
| Nginx (reverse proxy) | 8088 |

> Todos los puertos estan bindeados a `127.0.0.1` por seguridad. Se accede a traves de Apache como reverse proxy con SSL.

## Autenticacion

El sistema usa JWT (JSON Web Tokens) para proteger todos los endpoints de la API.

```bash
# Login
curl -X POST /api/auth/login -d '{"username":"admin","password":"tu_password"}'
# Respuesta: {"access_token":"eyJ...", "token_type":"bearer", "username":"admin", "is_admin":true}

# Usar token en peticiones
curl -H "Authorization: Bearer eyJ..." /api/events/
```

| Endpoint | Metodo | Auth | Descripcion |
|----------|--------|------|-------------|
| `/api/auth/login` | POST | No | Autenticar y obtener JWT |
| `/api/auth/me` | GET | Si | Datos del usuario actual |
| `/api/auth/users` | POST | Admin | Crear nuevo usuario |
| `/api/auth/users` | GET | Admin | Listar usuarios |

## API REST

Todos los endpoints (excepto auth/login y health) requieren JWT Bearer token.

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/` | GET | Info del proyecto |
| `/api/health` | GET | Health check |
| `/api/events/` | GET | Listar eventos (filtros: event_type, source_ip, is_anomaly) |
| `/api/events/{id}` | GET | Detalle de un evento |
| `/api/alerts/` | GET | Listar alertas (filtros: severity, alert_type, acknowledged) |
| `/api/alerts/{id}` | GET | Detalle de una alerta |
| `/api/alerts/{id}/acknowledge` | PATCH | Reconocer alerta |
| `/api/stats/summary` | GET | Estadisticas generales |
| `/api/reports/pdf` | GET | Descargar reporte PDF (rate limit: 20/hora) |
| `/api/ml/status` | GET | Estado de modelos ML |
| `/api/ml/retrain` | POST | Re-entrenar modelos (admin, rate limit: 5/hora) |
| `/api/ml/predict` | POST | Predecir anomalia en evento |
| `/ws/events` | WS | Stream en tiempo real (requiere token en query param) |

## Tipos de Eventos Detectados

- `ssh_login_accepted` — Login SSH exitoso
- `ssh_login_failed` — Intento de login SSH fallido
- `ssh_invalid_user` — Intento con usuario inexistente
- `sudo_command` — Comando ejecutado con sudo
- `apache_access` — Acceso HTTP (Apache Combined Log Format)
- `syslog` — Eventos genericos de syslog

## Reglas de Alerta

| Regla | Condicion | Severidad |
|-------|-----------|-----------|
| Fuerza bruta SSH | >= 5 fallos misma IP en 60s | HIGH / CRITICAL (>= 20) |
| Fuerza bruta Web | >= 10 errores 401/403 misma IP en 60s | HIGH |
| Directory Traversal | URL con `../`, `etc/passwd` | CRITICAL |
| SQL Injection | URL con `UNION SELECT`, `OR 1=1`, etc. | CRITICAL |
| Sudo a Root | Comando sudo hacia root | MEDIUM |
| Ataque Multi-paso | Secuencia: recon -> brute force -> acceso | CRITICAL |

## Modelo de Machine Learning

**Dual ML Pipeline:**

1. **Isolation Forest** — Deteccion no supervisada de anomalias
2. **Random Forest** — Clasificacion supervisada de tipos de ataque

**Feature Engineering** (15 dimensiones):
- Severidad, tipo SSH, nivel de error, status HTTP
- Entropia del mensaje, patrones temporales (hora/dia)
- Longitud de URL, caracteres especiales, profundidad de path
- Frecuencia por IP, diversidad de endpoints

Cuando no hay modelo entrenado, el sistema usa deteccion por reglas heuristicas como fallback.

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
│   │   ├── api/          # Routers REST (auth, events, alerts, stats, reports, ml)
│   │   ├── core/         # Parser, detector, alert engine, ingester, sequence analyzer
│   │   ├── ml/           # Isolation Forest + Random Forest trainer/predictor
│   │   ├── models/       # SQLAlchemy (LogEvent, Alert, User)
│   │   ├── schemas/      # Pydantic validation (event, alert, auth)
│   │   ├── utils/        # Logger, PDF generator
│   │   ├── websocket/    # WebSocket manager
│   │   ├── auth.py       # JWT auth module (passlib + jose)
│   │   └── config.py     # Settings con pydantic-settings
│   ├── tests/            # 98 tests, 83% cobertura
│   └── alembic/          # Migraciones DB
├── frontend/             # Vue 3 + Pinia + Tailwind CSS
│   └── src/
│       ├── views/        # Login, Home, Events, Reports
│       ├── components/   # Dashboard, EventsTable, AlertsPanel, StatsChart, SeverityChart
│       ├── stores/       # Pinia (auth, events, alerts)
│       └── router/       # Vue Router con auth guards
├── nginx/                # Reverse proxy config
├── scripts/              # Utilidades (seed, train, generate logs)
├── docker-compose.yml    # Orquestacion con health checks
└── .env.example          # Variables de entorno
```

## Seguridad

- Autenticacion JWT con tokens expirables (8 horas por defecto)
- Contraseñas hasheadas con bcrypt
- CORS configurable via variable de entorno
- Rate limiting en endpoints costosos (PDF, ML retrain)
- Puertos Docker solo en 127.0.0.1 (no expuestos a internet)
- Apache reverse proxy con SSL (Let's Encrypt)
- WebSocket protegido con token
- Endpoints de ML restringidos a administradores

## Comandos Utiles

```bash
# Levantar todo
docker compose up -d

# Ver logs del backend
docker compose logs -f backend

# Ejecutar migraciones
docker compose exec backend alembic upgrade head

# Re-entrenar modelo ML (requiere eventos en DB)
curl -X POST -H "Authorization: Bearer TOKEN" /api/ml/retrain

# Generar logs de prueba
python3 scripts/generate_sample_logs.py

# Correr tests
cd backend && python3 -m pytest tests/ -v --cov=app
```

## Autor

**J. Zambrano R.** — Proyecto de Titulacion

## Licencia

Uso academico y educativo.
