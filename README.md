# VigIA — Analizador de Logs con Inteligencia Artificial

## Finalidad

VigIA es una herramienta de ciberseguridad disenada para **monitorear, analizar y proteger servidores Linux en tiempo real**. Su objetivo principal es detectar de forma automatica amenazas de seguridad, intentos de intrusion y comportamientos anomalos en los logs del sistema operativo, aplicaciones web y servicios de red.

### Problema que resuelve

Los administradores de sistemas enfrentan un volumen masivo de logs diarios (cientos de miles de lineas) que es imposible revisar manualmente. Los ataques de fuerza bruta, inyecciones SQL, escaneos de puertos y accesos no autorizados pueden pasar desapercibidos entre el ruido normal del servidor. VigIA automatiza este proceso usando **Inteligencia Artificial** para:

- **Detectar anomalias** que escapan a las reglas tradicionales, mediante modelos de Machine Learning (Isolation Forest) que aprenden el comportamiento normal del servidor y alertan cuando algo se desvía.
- **Clasificar ataques** automaticamente usando Random Forest, categorizando amenazas en tipos como fuerza bruta SSH, SQL injection, directory traversal, entre otros.
- **Analizar secuencias de ataque multi-paso**, identificando patrones como reconocimiento seguido de fuerza bruta seguido de acceso.
- **Alertar en tiempo real** via WebSocket, permitiendo respuesta inmediata ante incidentes.
- **Generar reportes ejecutivos PDF** con estadisticas de seguridad para documentacion y auditoria.

### Casos de uso

- Monitoreo de seguridad en servidores de produccion (VPS, dedicados, cloud)
- Deteccion de intentos de fuerza bruta SSH y ataques web
- Auditoria de comandos sudo y accesos privilegiados
- Dashboard centralizado de seguridad para equipos de infraestructura
- Herramienta de apoyo para proyectos academicos de ciberseguridad e IA aplicada

---

## Arquitectura

```
[Archivos de Log del Host]
        | (montados read-only)
        v
[Ingester] -- watchdog --> detecta cambios en tiempo real
        |
        v
[Parser] -- regex multi-formato --> extrae campos estructurados
        |       (soporta formato clasico y ISO 8601 de rsyslog)
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
- Servidor Linux con logs en `/var/log/` (rsyslog recomendado para generar auth.log y syslog)

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

> **Nota:** En servidores Debian 12+ que usan solo systemd journal, es necesario instalar rsyslog (`apt install rsyslog`) para que se generen los archivos `/var/log/auth.log` y `/var/log/syslog` que VigIA monitorea.

## Puertos (por defecto, solo 127.0.0.1)

| Servicio | Puerto |
|----------|--------|
| PostgreSQL | 5434 |
| Redis | 6380 |
| Backend (FastAPI) | 8002 |
| Frontend (Vue 3) | 3010 |
| Nginx (reverse proxy) | 8088 |

> Todos los puertos estan bindeados a `127.0.0.1` por seguridad. Se accede a traves de Apache/Nginx externo como reverse proxy con SSL.

## Dashboard y Vistas

| Vista | Ruta | Descripcion |
|-------|------|-------------|
| Dashboard | `/` | Tarjetas de estadisticas, grafico de eventos por tipo, grafico de severidad, alertas recientes |
| Eventos | `/events` | Tabla de eventos con filtros (tipo, IP, anomalia) y paginacion |
| Reportes | `/reports` | Descarga de reportes ejecutivos en PDF |
| Machine Learning | `/ml` | Estado de los modelos (Isolation Forest + Random Forest), feature engineering, distribucion de eventos, re-entrenamiento |
| Login | `/login` | Autenticacion con JWT |

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
- `ssh_connection_closed` — Conexion SSH cerrada (escaneos, fuerza bruta)
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

1. **Isolation Forest** — Deteccion no supervisada de anomalias. Aprende el comportamiento normal del servidor y marca como anomalo cualquier evento que se desvie significativamente del patron aprendido.
2. **Random Forest Classifier** — Clasificacion supervisada de tipos de ataque. Categoriza eventos sospechosos en clases como fuerza bruta, SQL injection, directory traversal, acceso normal, etc.

**Feature Engineering** (15 dimensiones):

| Feature | Descripcion |
|---------|-------------|
| severity_score | Score de severidad del evento (0.0 - 1.0) |
| is_high_risk_event | Evento de alto riesgo (SSH fallido, usuario invalido) |
| is_medium_risk_event | Evento de riesgo medio (sudo, SSH cerrado) |
| is_error_level | Nivel ERROR o CRITICAL |
| is_warning_level | Nivel WARNING |
| has_source_ip | Tiene IP de origen |
| hour_sin / hour_cos | Patron temporal ciclico de la hora |
| is_night | Evento nocturno (22:00 - 06:00) |
| is_weekend | Evento en fin de semana |
| http_status_normalized | Codigo HTTP normalizado |
| url_length_normalized | Longitud de URL normalizada |
| url_suspicious_score | Score de sospecha en URL (traversal, SQLi) |
| message_entropy | Entropia del mensaje (complejidad) |
| has_username | Tiene nombre de usuario asociado |

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
│       ├── views/        # Login, Home, Events, Reports, ML
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
- Contrasenas hasheadas con bcrypt
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
