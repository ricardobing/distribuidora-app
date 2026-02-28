# MolyMarket — Sistema de Distribución Logística

Sistema completo de gestión de reparto para distribuidora de alimentos en Mendoza, Argentina.  
Migración desde Google Sheets + Apps Script a **FastAPI + PostgreSQL/PostGIS + Next.js 15**.

---

## 📦 Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend API | Python 3.12 · FastAPI 0.115 · SQLAlchemy 2.0 async |
| Base de datos | PostgreSQL 16 · PostGIS 3.4 |
| Migraciones | Alembic 1.14 |
| Frontend | Next.js 15 (App Router) · TypeScript · Tailwind CSS |
| Mapas | Leaflet 1.9 · react-leaflet |
| Gráficos | Recharts |
| QR | html5-qrcode |
| Auth | JWT (python-jose · passlib/bcrypt) |
| Deploy | Railway (backend + DB) · Vercel (frontend) |

---

## 🗂️ Estructura del Proyecto

```
molyapp/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # 12 routers FastAPI
│   │   ├── core/            # utils, security, validators
│   │   ├── models/          # 11 modelos SQLAlchemy
│   │   ├── schemas/         # 7 módulos Pydantic v2
│   │   ├── services/        # 13 servicios de negocio
│   │   ├── config.py        # Settings (pydantic-settings)
│   │   ├── database.py      # Engine async + session factory
│   │   ├── dependencies.py  # get_db, get_current_user
│   │   └── main.py          # FastAPI app + CORS + routers
│   ├── alembic/
│   │   └── versions/
│   │       ├── 001_initial_schema.py
│   │       ├── 002_seed_carriers.py
│   │       └── 003_seed_config.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/             # 13 páginas Next.js App Router
│   │   ├── components/      # AppLayout, Sidebar, RutaMap
│   │   ├── context/         # AuthContext
│   │   └── lib/             # api, types, auth, formatters
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Inicio Rápido — Docker (Recomendado)

### 1. Clonar y configurar entorno

```bash
git clone https://github.com/ricardobing/distribuidora-app.git
cd distribuidora-app

# Copiar y editar variables de entorno
cp .env.example .env
# Editar .env con tus claves reales (ver sección Variables de Entorno)
```

### 2. Levantar todos los servicios

```bash
docker compose up --build
```

Esto automáticamente:
- Levanta PostgreSQL 16 + PostGIS 3.4
- Ejecuta `alembic upgrade head` (crea tablas + seeds)
- Inicia el backend FastAPI en `http://localhost:8000`
- Inicia el frontend Next.js en `http://localhost:3000`

### 3. Acceder a la aplicación

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |

**Credenciales por defecto:**
- Email: `admin@molymarket.com`
- Password: `admin1234`

> ⚠️ Cambiar la contraseña inmediatamente en producción.

---

## 🛠️ Desarrollo Local sin Docker

### Backend

```bash
cd backend

# Crear y activar virtualenv
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp ../.env.example .env
# Editar .env con tu DATABASE_URL de PostgreSQL local

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor con hot-reload
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install --legacy-peer-deps

# Configurar entorno
cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Iniciar servidor de desarrollo
npm run dev
```

---

## 🌐 Variables de Entorno

### Backend / docker-compose

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `DATABASE_URL` | PostgreSQL async URL | ✅ |
| `SECRET_KEY` | Clave JWT (mín. 32 chars) | ✅ |
| `GOOGLE_MAPS_API_KEY` | Geocodificación Google | ⚠️ Opcional |
| `OPENAI_API_KEY` | Clasificación AI de remitos | ⚠️ Opcional |
| `ORS_API_KEY` | OpenRouteService (ruteo) | ⚠️ Opcional |
| `MAPBOX_TOKEN` | Mapbox alternativo | ⚠️ Opcional |
| `ALLOWED_ORIGINS` | CORS (separado por coma) | ✅ |
| `ENVIRONMENT` | `development` \| `production` | ✅ |

### Frontend

| Variable | Descripción |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | URL base del backend (ej: `https://api.molymarket.com/api/v1`) |

---

## 🚂 Deploy en Railway (Backend + DB)

### 1. Base de datos PostgreSQL

1. En Railway → **New Project** → **PostgreSQL**
2. Esperar que levante y copiar `DATABASE_URL`
3. En la DB, conectar y ejecutar:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   CREATE EXTENSION IF NOT EXISTS postgis_topology;
   ```

### 2. Backend FastAPI

1. **New Service** → **GitHub Repo** → seleccionar `distribuidora-app`
2. Root directory: `backend`
3. Variables de entorno en Railway:
   ```
   DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<host>:5432/<db>
   SECRET_KEY=<clave-segura-min-32-chars>
   GOOGLE_MAPS_API_KEY=<tu-clave>
   OPENAI_API_KEY=<tu-clave>
   ORS_API_KEY=<tu-clave>
   ALLOWED_ORIGINS=https://tu-app.vercel.app
   ENVIRONMENT=production
   ```
4. Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Deploy → obtener URL pública (ej: `https://molymarket-backend.up.railway.app`)

---

## ▲ Deploy en Vercel (Frontend)

1. Ir a [vercel.com/new](https://vercel.com/new) → importar `distribuidora-app`
2. Root directory: `frontend`
3. Framework: **Next.js** (autodetectado)
4. Variables de entorno:
   ```
   NEXT_PUBLIC_API_URL=https://molymarket-backend.up.railway.app/api/v1
   ```
5. Deploy

---

## 📱 Funcionalidades Principales

### Remitos
- Ingesta por número (validación + geocodificación automática)
- Clasificación por carrier via regex + IA (OpenAI fallback)
- Corrección manual de dirección con re-geocodificación
- Vista detallada con estado del ciclo de vida

### Optimización de Rutas
- Generación automática por carrier con ventanas de entrega
- Visualización en mapa Leaflet con marcadores numerados
- Links Google Maps para conductores
- GeoJSON export para análisis externo

### Escaneo QR
- Modo cámara (html5-qrcode)
- Modo manual
- Escaneo por lotes

### Facturación
- Trazabilidad por remito
- Resumen mensual por carrier

### Histórico
- Cierre mensual
- Export XLSX
- Restauración de registros

### Dashboard
- KPIs en tiempo real
- Gráfico de costos por carrier
- Estado de entregas del día

---

## 🗄️ Migraciones

```bash
# Aplicar todas las migraciones
alembic upgrade head

# Ver estado actual
alembic current

# Crear nueva migración
alembic revision --autogenerate -m "descripcion"

# Rollback una versión
alembic downgrade -1
```

---

## 🧪 API Reference

La documentación interactiva está disponible en `/docs` (Swagger UI) y `/redoc`.

### Endpoints principales

```
POST   /api/v1/auth/login
GET    /api/v1/auth/me

POST   /api/v1/remitos/ingest
GET    /api/v1/remitos
GET    /api/v1/remitos/pendientes
GET    /api/v1/remitos/{numero}
PUT    /api/v1/remitos/{numero}/direccion

POST   /api/v1/rutas/generar
GET    /api/v1/rutas/{id}/geojson
GET    /api/v1/rutas/{id}/gmaps-links

POST   /api/v1/qr/scan
POST   /api/v1/entregados/marcar

GET    /api/v1/dashboard/stats
GET    /api/v1/historico/export/{mes}
```

---

## 🤝 Contribuir

1. Fork del repositorio
2. Crear rama: `git checkout -b feat/nueva-funcionalidad`
3. Commit: `git commit -m "feat: descripcion"`
4. Push: `git push origin feat/nueva-funcionalidad`
5. Pull Request

---

## 📄 Licencia

MIT — Ver [LICENSE](LICENSE) para más detalles.

---

*MolyMarket — Distribuidora Moly, Mendoza, Argentina*
