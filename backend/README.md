# MolyMarket Backend

API REST para el sistema de distribución logística MolyMarket (Mendoza, Argentina).

## Stack

- **FastAPI 0.115** + Python 3.12
- **PostgreSQL 16 + PostGIS 3.4** (geometría espacial)
- **SQLAlchemy 2.0 async** + asyncpg
- **Alembic** (migraciones)
- **JWT** (python-jose + passlib/bcrypt)
- **httpx** (cliente async para APIs externas: ORS, Mapbox, Google, OpenAI)

## Setup local

### Pre-requisitos

- Python 3.12+
- PostgreSQL 16 con extensión PostGIS 3.4
- (Opcional) Docker y docker-compose

### 1. Instalar dependencias

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con las API keys reales
```

Variables requeridas mínimas:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/molymarket
SECRET_KEY=cambia-esta-clave-en-produccion
```

### 3. Crear base de datos

```bash
psql -U postgres -c "CREATE DATABASE molymarket;"
```

### 4. Ejecutar migraciones

```bash
alembic upgrade head
```

Esto crea todas las tablas, habilita PostGIS, e inserta:
- 15 carriers predefinidos (Andreani, OCA, Correo Argentino, etc.)
- 15 parámetros de configuración con defaults
- Usuario administrador: `admin@molymarket.com` / `admin1234`

### 5. Iniciar servidor de desarrollo

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API disponible en: http://localhost:8000  
Documentación: http://localhost:8000/docs

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Autenticación |
| POST | `/api/v1/remitos/ingest` | Ingesta masiva de remitos |
| GET | `/api/v1/remitos` | Listar remitos con filtros |
| POST | `/api/v1/rutas/generar` | Generar ruta optimizada del día |
| GET | `/api/v1/rutas/{id}/geojson` | GeoJSON para mapa |
| GET | `/api/v1/rutas/{id}/gmaps-links` | Links Google Maps fragmentados |
| GET | `/api/v1/qr/scan?numero=X` | Escanear QR de remito |
| POST | `/api/v1/entregados/marcar` | Marcar como entregados |
| GET | `/api/v1/historico/export/{mes}` | Exportar XLSX mensual |
| GET | `/api/v1/dashboard/stats` | Estadísticas del sistema |
| GET | `/api/v1/geocode/cache/stats` | Estado del caché de geocodificación |

## Pipeline de ingesta de remito

Cada remito pasa por 7 pasos automáticos:

1. **Normalización** de dirección (NFD, abreviaturas, aliases de ciudad)
2. **Lookup Pedidos Listos** — vincula datos de la planilla Google Sheets
3. **Detección de pickup** — regex sobre observaciones
4. **Detección de carrier** — regex DB → AI (OpenAI) → reglas por provincia
5. **Validación de dirección** — bbox Mendoza, no ciudad centro
6. **Geocodificación** — ORS → Mapbox → Google (con caché DB 30 días)
7. **Parsing de ventana horaria** — 7 patrones en cascada

## Algoritmo de ruta

1. Carga remitos `estado_clasificacion=enviar`
2. Filtra por distancia máxima (radio 45km desde depósito)
3. Filtra por ventana horaria (si `utilizar_ventana=true`)
4. Filtra por tiempo de retorno al galpón
5. Calcula matriz NxN de distancias (ORS, Google o Mapbox)
6. Optimiza con **Sweep + 2-opt** por grupo (URGENTE → PRI_AM → PRI_PM → NORM_AM → NORM_PM)
7. Aplica filtro de saltos (`fixpoint_filter_jumps`)
8. Calcula tiempos acumulados
9. Genera links Google Maps (máx. 10 waypoints por URL)
10. Guarda Ruta + RutaParada + RutaExcluido

## Deploy en Railway

```bash
# Variables de entorno en Railway:
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=...
GOOGLE_MAPS_API_KEY=...
OPENAI_API_KEY=...
ORS_API_KEY=...
MAPBOX_TOKEN=...
ALLOWED_ORIGINS=https://tu-frontend.vercel.app
```

Railway detecta el `Dockerfile` automáticamente.

## Tests

```bash
pytest tests/ -v
```
