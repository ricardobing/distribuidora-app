# 05 — Plan de Migración

**Origen:** Google Sheets + Apps Script (~18.500 líneas JS)  
**Destino:** FastAPI + PostgreSQL/PostGIS + Next.js  
**Deploy:** Railway (backend + DB) + Vercel (frontend)

---

## 5.1 Estructura Completa de Carpetas (proyecto unificado)

```
molymarket/
│
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── 001_initial_schema.py
│   │   │   ├── 002_seed_carriers.py
│   │   │   └── 003_seed_config.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── remito.py
│   │   │   ├── carrier.py
│   │   │   ├── pedido_listo.py
│   │   │   ├── ruta.py
│   │   │   ├── geo_cache.py
│   │   │   ├── historico.py
│   │   │   ├── audit_log.py
│   │   │   ├── billing.py
│   │   │   ├── config.py
│   │   │   ├── usuario.py
│   │   │   └── distance_cache.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── remito.py
│   │   │   ├── carrier.py
│   │   │   ├── ruta.py
│   │   │   ├── geocode.py
│   │   │   ├── config.py
│   │   │   ├── auth.py
│   │   │   └── common.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── remitos.py
│   │   │   │   ├── carriers.py
│   │   │   │   ├── rutas.py
│   │   │   │   ├── qr.py
│   │   │   │   ├── entregados.py
│   │   │   │   ├── historico.py
│   │   │   │   ├── config.py
│   │   │   │   ├── geocode.py
│   │   │   │   ├── pedidos_listos.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── dashboard.py
│   │   │   │   └── billing.py
│   │   │   └── router.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── remito_service.py
│   │   │   ├── carrier_service.py
│   │   │   ├── geocode_service.py
│   │   │   ├── address_service.py
│   │   │   ├── route_service.py
│   │   │   ├── route_optimizer.py
│   │   │   ├── distance_matrix_service.py
│   │   │   ├── window_service.py
│   │   │   ├── delivery_service.py
│   │   │   ├── ai_service.py
│   │   │   ├── pedidos_listos_service.py
│   │   │   ├── billing_service.py
│   │   │   └── export_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── haversine.py
│   │       ├── address_normalization.py
│   │       ├── mendoza_bbox.py
│   │       └── gmaps_link_builder.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_remito_service.py
│   │   ├── test_carrier_service.py
│   │   ├── test_geocode_service.py
│   │   ├── test_route_optimizer.py
│   │   ├── test_window_service.py
│   │   ├── test_address_normalization.py
│   │   ├── test_qr_endpoint.py
│   │   └── test_delivery_flow.py
│   ├── scripts/
│   │   ├── migrate_from_sheets.py       # Script one-shot: importa datos de Sheets
│   │   └── seed_demo.py                 # Seed de datos de prueba
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── .env.example
│
├── frontend/
│   ├── public/
│   │   ├── icons/
│   │   │   ├── marker-default.svg
│   │   │   ├── marker-urgente.svg
│   │   │   ├── marker-prioridad.svg
│   │   │   ├── marker-depot.svg
│   │   │   └── marker-entregado.svg
│   │   └── favicon.ico
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── login/page.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── remitos/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── [id]/page.tsx
│   │   │   │   └── ingest/page.tsx
│   │   │   ├── rutas/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── generar/page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── reporte/page.tsx
│   │   │   ├── historico/page.tsx
│   │   │   ├── carriers/page.tsx
│   │   │   ├── config/page.tsx
│   │   │   ├── billing/page.tsx
│   │   │   └── qr/page.tsx
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── PageContainer.tsx
│   │   │   ├── remitos/
│   │   │   │   ├── RemitosTable.tsx
│   │   │   │   ├── RemitoDetail.tsx
│   │   │   │   ├── RemitoStatusBadge.tsx
│   │   │   │   ├── IngestForm.tsx
│   │   │   │   ├── AddressCorrection.tsx
│   │   │   │   └── RemitoTimeline.tsx
│   │   │   ├── rutas/
│   │   │   │   ├── RouteMap.tsx
│   │   │   │   ├── RouteStopsList.tsx
│   │   │   │   ├── RouteStopCard.tsx
│   │   │   │   ├── RouteExcludedList.tsx
│   │   │   │   ├── RouteConfigForm.tsx
│   │   │   │   ├── RouteStats.tsx
│   │   │   │   └── GMapsLinks.tsx
│   │   │   ├── reporte/
│   │   │   │   ├── ReporteTable.tsx
│   │   │   │   ├── ArmadoCheckbox.tsx
│   │   │   │   └── EntregadoCheckbox.tsx
│   │   │   ├── map/
│   │   │   │   ├── MapContainer.tsx
│   │   │   │   ├── RouteLayer.tsx
│   │   │   │   ├── StopMarker.tsx
│   │   │   │   ├── DepotMarker.tsx
│   │   │   │   └── HeatmapLayer.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── StatsCards.tsx
│   │   │   │   ├── DeliveryChart.tsx
│   │   │   │   ├── CarrierDistribution.tsx
│   │   │   │   └── PendingAlerts.tsx
│   │   │   ├── qr/
│   │   │   │   ├── QRScanner.tsx
│   │   │   │   ├── QRManualInput.tsx
│   │   │   │   └── QRResult.tsx
│   │   │   └── ui/
│   │   │       ├── Button.tsx
│   │   │       ├── Input.tsx
│   │   │       ├── Select.tsx
│   │   │       ├── Checkbox.tsx
│   │   │       ├── Badge.tsx
│   │   │       ├── Modal.tsx
│   │   │       ├── Toast.tsx
│   │   │       ├── DataTable.tsx
│   │   │       ├── LoadingSpinner.tsx
│   │   │       ├── EmptyState.tsx
│   │   │       └── ConfirmDialog.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useRemitos.ts
│   │   │   ├── useRutas.ts
│   │   │   ├── useReporte.ts
│   │   │   ├── useConfig.ts
│   │   │   ├── useDashboard.ts
│   │   │   └── useQR.ts
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   ├── constants.ts
│   │   │   ├── formatters.ts
│   │   │   ├── map-utils.ts
│   │   │   └── types.ts
│   │   ├── context/
│   │   │   └── AuthContext.tsx
│   │   └── middleware.ts
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── .env.local.example
│
├── docs/
│   └── migration/
│       ├── 00-INDICE-MIGRACION.md
│       ├── 01-SISTEMA-ACTUAL.md
│       ├── 02-MODELO-BASE-DE-DATOS.md
│       ├── 03-ARQUITECTURA-API-FASTAPI.md
│       ├── 04-ARQUITECTURA-FRONTEND-NEXTJS.md
│       └── 05-PLAN-MIGRACION.md
│
├── .gitignore
└── README.md
```

---

## 5.2 Plan de Migración por Fases

### Fase 0 — Fundación (Semana 1)

**Objetivo:** Tener el esqueleto del proyecto corriendo en local y deployado en Railway/Vercel vacío.

| Paso | Acción | Criterio de aceptación |
|------|--------|------------------------|
| 0.1 | Crear repos (o monorepo) con la estructura de carpetas | `backend/` y `frontend/` existen |
| 0.2 | Configurar PostgreSQL 16 + PostGIS 3.4 en Railway | `SELECT PostGIS_Version()` retorna 3.4.x |
| 0.3 | Crear `app/main.py` con FastAPI, health check `GET /health` | Responde `{"status": "ok"}` |
| 0.4 | Configurar Alembic, crear migración 001 (schema completo) | `alembic upgrade head` crea todas las tablas |
| 0.5 | Deploy backend en Railway | URL pública responde `/health` |
| 0.6 | `npx create-next-app@latest frontend` con TypeScript + Tailwind | `npm run dev` levanta en localhost:3000 |
| 0.7 | Deploy frontend en Vercel | URL pública muestra página default |
| 0.8 | Conectar frontend → backend (CORS, env vars) | Fetch a `/health` desde frontend funciona |

### Fase 1 — Módulo Carriers + Remitos (Semana 2)

**Objetivo:** Poder ingestar remitos, clasificarlos y geocodificarlos.

| Paso | Acción | Dependencias |
|------|--------|-------------|
| 1.1 | **Carrier Service:** implementar `detect_carrier()` con las 16 regex del sistema actual | Seed de carriers (migración 002) |
| 1.2 | **AI Service:** wrapper OpenAI para clasificación fallback | API key configurada |
| 1.3 | **Address Service:** normalización (`normalizeAddress()`) portando la lógica NFD + abreviaciones | Ninguna |
| 1.4 | **Geocode Service:** multi-provider (ORS → Google → Mapbox) con cache en DB | Tabla `geo_cache` |
| 1.5 | **Window Service:** parseo de observaciones con cascade de 7 pasos | AI Service |
| 1.6 | **Remito Service:** pipeline completo `process_remito()` (7 pasos del `processRowByIndex`) | Pasos 1.1-1.5 |
| 1.7 | **Endpoints:** `POST /remitos/ingest`, `GET /remitos`, `GET /remitos/{id}` | Remito Service |
| 1.8 | **Frontend:** `/remitos` (tabla), `/remitos/{id}` (detalle con mapa), `/remitos/ingest` | API funcionando |
| 1.9 | **Test E2E:** ingestar 10 remitos reales, verificar clasificación y geocodificación | Todo lo anterior |

**Correspondencia con código original:**
- `carrier_service.py` ← `detectarTransporte_()` (code.js ~L1600-1800) + regex patterns (L1400-1600)
- `address_service.py` ← `normalizeAddress_()` (code.js ~L6200-6400)
- `geocode_service.py` ← `geocodificarDireccion_()` (code.js ~L2200-2600) + `buscarEnCacheGeo_()` (L2000-2200)
- `window_service.py` ← `interpretarObservacionUnificado_()` (code.js ~L2700-3100)
- `remito_service.py` ← `processRowByIndex()` (funciones_auxiliares.js ~L393-700)

### Fase 2 — Módulo Rutas (Semana 3)

**Objetivo:** Poder generar rutas optimizadas igual que el sistema actual.

| Paso | Acción | Dependencias |
|------|--------|-------------|
| 2.1 | **Haversine + BBOX:** funciones geográficas | Ninguna |
| 2.2 | **Distance Matrix Service:** NxN blocks (10×10), multi-provider, cache | Geocode Service |
| 2.3 | **Route Optimizer:** implementar `sweep_algorithm()` + `two_opt_improve()` + `tsp_nearest_neighbor()` | Haversine |
| 2.4 | **Filtros:** ventana horaria, saltos iterativos (fixpoint), vuelta al depósito | Distance Matrix Service |
| 2.5 | **Route Service:** orquestador (`generate_route()`) que ejecuta la pipeline completa | 2.1-2.4 |
| 2.6 | **Google Maps Link Builder:** fragmentar en tramos de max 10 waypoints | Ninguna |
| 2.7 | **GeoJSON endpoint:** `GET /rutas/{id}/geojson` | Route Service |
| 2.8 | **Frontend:** `/rutas/generar` (config form), `/rutas/{id}` (mapa Leaflet + lista) | API funcionando |
| 2.9 | **Test E2E:** generar ruta con 30 puntos, comparar resultado con sistema actual | Todo lo anterior |

**Correspondencia con código original:**
- `route_optimizer.py` ← `sweepAlgorithm_()` (code.js ~L8800-8900), `twoOptImprove_()` (L8900-9000), `tspNearestNeighbor_()` (L9000-9100)
- `distance_matrix_service.py` ← `computeNxNMatrix_()` (code.js ~L5200-5600)
- `route_service.py` ← `generarRutaDesdeFraccionados_()` (code.js ~L7200-7400) + sub-funciones
- Filtros ← `filtrarPorVentanaHoraria_()` (L8200-8400), `filtrarSaltosYVuelta_()` (L8400-8800)

### Fase 3 — Módulo Entregas + QR (Semana 4)

**Objetivo:** Flujo completo de ARMADO → ENTREGADO → HISTÓRICO.

| Paso | Acción | Dependencias |
|------|--------|-------------|
| 3.1 | **QR Endpoint:** `GET /qr/scan` + `POST /qr/scan-batch` | Remito Service |
| 3.2 | **Delivery Service:** `mark_armado()`, `process_entregados()`, `move_to_historico()` | Remito model |
| 3.3 | **Validaciones:** ENTREGADO requiere ARMADO, ARMADO requiere estado "enviar" | Delivery Service |
| 3.4 | **Reporte endpoint:** `GET /reporte/transportes` agrupado por carrier | Carrier Service |
| 3.5 | **Frontend:** `/qr` (escáner móvil), `/reporte` (tabla con checkboxes) | API funcionando |
| 3.6 | **Frontend:** botón "Procesar Entregados" con confirmación | Delivery Service |
| 3.7 | **Histórico:** `GET /historico`, export XLSX, cierre mensual | Delivery Service |
| 3.8 | **Frontend:** `/historico` (tabla con filtros y export) | API funcionando |

**Correspondencia con código original:**
- QR ← `doGet()` (code.js ~L16347-16407)
- Delivery ← `procesarEntregadosDesdeMenu()` (code.js ~L12718-12900)
- Reporte ← `generarVistaCliente_()` (code.js ~L3127-3400)

### Fase 4 — Módulo Dashboard + Billing + Config (Semana 5)

| Paso | Acción |
|------|--------|
| 4.1 | **Dashboard Service:** estadísticas agregadas (counts, charts) |
| 4.2 | **Config CRUD:** `GET/PUT /config` para parámetros de ruta |
| 4.3 | **Billing Service:** registrar costos de cada API call |
| 4.4 | **Auth:** login, JWT, middleware, roles (admin/operador/viewer) |
| 4.5 | **Frontend:** `/dashboard`, `/config`, `/billing`, `/login` |
| 4.6 | **Sidebar + Layout:** navegación completa |

### Fase 5 — Migración de Datos + Cutover (Semana 6)

| Paso | Acción |
|------|--------|
| 5.1 | **Script `migrate_from_sheets.py`:** leer Sheets via API, mapear a tablas PostgreSQL |
| 5.2 | Migrar FRACCIONADOS → tabla `remitos` |
| 5.3 | Migrar Transportes → tabla `remitos` (merge por número) |
| 5.4 | Migrar HISTÓRICO_ENTREGADOS → tabla `historico_entregados` |
| 5.5 | Migrar CACHE_GEO → tabla `geo_cache` |
| 5.6 | Migrar CONFIG_RUTA → tabla `config_ruta` |
| 5.7 | Migrar carriers (seed ya existente, verificar contra datos reales) |
| 5.8 | Validar integridad: contar filas origen vs destino |
| 5.9 | **Cutover:** apuntar el dominio, desactivar triggers de Apps Script |
| 5.10 | **Monitoreo post-cutover:** 48 horas de operación paralela |

---

## 5.3 Estrategia de Convivencia con Google Sheets

Durante la migración, el sistema actual seguirá operando. La transición es por módulo:

```
Fase 1-4: Sheets sigue siendo el sistema principal
           Backend nuevo se desarrolla y testea en paralelo
           Se usa datos reales exportados para testing

Fase 5:   Cutover — se migran datos y se apaga Sheets
```

### ¿Por qué NO convivencia simultánea?

1. El sistema actual tiene triggers (`onEdit`, `onChangeInstallable`) que escriben en cascada en múltiples hojas. Sincronizar en tiempo real con PostgreSQL sería un sistema de doble escritura extremadamente frágil.
2. La complejidad de mantener consistencia bidireccional supera el beneficio.
3. El sistema se puede migrar en un solo corte porque:
   - No hay datos que tarden semanas en migrar (son pocas centenas de filas activas)
   - El sistema nuevo se puede testear completamente con datos exportados
   - El rollback es simple: volver a activar los triggers de Apps Script

### Checklist pre-cutover

- [ ] Todos los tests E2E pasan con datos reales
- [ ] Pipeline de 50 remitos procesado correctamente (clasificación, geocodificación, ruta)
- [ ] QR scan funciona desde celular
- [ ] Export XLSX produce el mismo formato que el cierre mensual actual
- [ ] Performance: ruta de 30 puntos se genera en < 60 segundos
- [ ] Backup: snapshot de todas las hojas en Google Drive antes de cortar

---

## 5.4 Reutilización de Código

### Código que se porta 1:1 (lógica idéntica, traducida a Python)

| Módulo Original (JS) | Destino (Python) | Notas |
|----------------------|-------------------|-------|
| `sweepAlgorithm_()` | `route_optimizer.py::sweep()` | atan2 + sort. Traducción directa. |
| `twoOptImprove_()` | `route_optimizer.py::two_opt()` | Delta check con -1e-6. Idéntico. |
| `tspNearestNeighbor_()` | `route_optimizer.py::nearest_neighbor()` | Greedy. Trivial. |
| `haversine_()` | `utils/haversine.py::haversine()` | Fórmula estándar. |
| `normalizeAddress_()` | `utils/address_normalization.py` | NFD + regex + abreviaciones. Directo. |
| `isMendozaBBOX_()` | `utils/mendoza_bbox.py` | Comparaciones lat/lng. Trivial. |
| Regex patterns de carriers | Seed data en `002_seed_carriers.py` | 16 patrones literales. |
| `buildGMapsRouteLink_()` | `utils/gmaps_link_builder.py` | String interpolation. Directo. |

### Código que se refactoriza (misma lógica, diferente estructura)

| Módulo Original | Destino | Cambios |
|----------------|---------|---------|
| `processRowByIndex()` (7 pasos secuenciales) | `remito_service.py::process_remito()` | Mismos pasos pero con DB transactions en lugar de escrituras a hoja |
| `detectarTransporte_()` (monolítica) | `carrier_service.py::detect()` | Split en detect_by_regex + detect_by_ai + finalize_category |
| `geocodificarDireccion_()` (4 capas de cache + 3 providers) | `geocode_service.py` | Cache simplificado (solo DB, no memory/CacheService/Properties) |
| `interpretarObservacionUnificado_()` (7 pasos) | `window_service.py::parse_window()` | Misma cascade, mejor separación de concerns |
| `computeNxNMatrix_()` (monolítica) | `distance_matrix_service.py` | Async con httpx, DB cache |
| `generarRutaDesdeFraccionados_()` (orquestador) | `route_service.py::generate()` | Misma pipeline, cada paso como método separado |
| `generarVistaCliente_()` | SQL View `v_reporte_transportes` | GROUP BY carrier en SQL, no en código |
| `onEdit()` con 9 sub-handlers | Endpoints REST individuales | Cada sub-handler se convierte en un endpoint PUT |

### Código que se elimina (ya no necesario)

| Módulo Original | Razón de eliminación |
|----------------|---------------------|
| `findFirstEmptyRowInColB_()` | No hay getLastRow() inflado por checkboxes — PostgreSQL no tiene este problema |
| `CacheService` / `Properties` cache layers | PostgreSQL cache table es suficiente (más rápida y sin límites de tamaño) |
| `SpreadsheetApp.*` calls | No hay Sheets |
| `Utilities.sleep()` para throttling | httpx rate limiting + async |
| `writeRowResult_()` / `writeObsEntrega_()` / `writeLatLng_()` | UPDATE SQL directo |
| `syncPedidosListos_()` (neutered) | Ya estaba desactivada |
| `getTriggerById_()` / `createTimeDrivenTrigger_()` | No hay triggers de Apps Script |
| Todas las funciones de manejo de triggers | No aplica |
| `doPost()` para ingesta desde Sheets | Ingesta es endpoint REST directo |

---

## 5.5 Variables de Entorno

### Railway (Backend)

```env
# === Base de Datos ===
DATABASE_URL=postgresql+asyncpg://postgres:<password>@<host>.railway.app:5432/molymarket
# Railway provee esta variable automáticamente al linkear el servicio de PostgreSQL
# PostGIS ya viene habilitado si se usa la imagen "PostGIS" en Railway

# === Autenticación ===
JWT_SECRET_KEY=<generar con: openssl rand -hex 64>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# === APIs Externas ===
GOOGLE_MAPS_API_KEY=<misma key que usa el sistema actual en ScriptProperties>
ORS_API_KEY=<misma key de OpenRouteService>
MAPBOX_API_KEY=<misma key de Mapbox>
OPENAI_API_KEY=<misma key de OpenAI>

# === Configuración ===
ENVIRONMENT=production
LOG_LEVEL=info
CORS_ORIGINS=["https://molymarket.vercel.app"]

# === Depósito (constantes geográficas) ===
DEPOT_LAT=-32.91973
DEPOT_LNG=-68.81829
DEPOT_ADDRESS=Elpidio González 2753, Guaymallén, Mendoza

# === Mendoza BBOX ===
MENDOZA_LAT_MIN=-33.5
MENDOZA_LAT_MAX=-32.0
MENDOZA_LNG_MIN=-69.5
MENDOZA_LNG_MAX=-68.0

# === Rate Limiting ===
GEOCODE_REQUESTS_PER_SECOND=5
DISTANCE_MATRIX_REQUESTS_PER_SECOND=2
OPENAI_REQUESTS_PER_MINUTE=60

# === Defaults del pipeline ===
AI_MODEL=gpt-4o-mini
GEOCODE_PRIMARY_PROVIDER=ors
DISTANCE_MATRIX_PRIMARY_PROVIDER=ors
```

### Railway — PostgreSQL (configuración del servicio)

```
Imagen: postgis/postgis:16-3.4
Puerto: 5432
Database name: molymarket
```

> **PostGIS en Railway:** Railway soporta custom Docker images. Seleccionar la imagen `postgis/postgis:16-3.4` al crear el servicio de base de datos, o usar un Dockerfile:

```dockerfile
FROM postgis/postgis:16-3.4
# Railway maneja el resto automáticamente
```

Alternativamente, si Railway solo ofrece PostgreSQL vanilla, habilitar PostGIS post-deploy:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

### Vercel (Frontend)

```env
# === API Backend ===
NEXT_PUBLIC_API_URL=https://molymarket-backend.railway.app/api/v1

# === Configuración ===
NEXT_PUBLIC_APP_NAME=MolyMarket
NEXT_PUBLIC_MAP_CENTER_LAT=-32.91973
NEXT_PUBLIC_MAP_CENTER_LNG=-68.81829
NEXT_PUBLIC_MAP_DEFAULT_ZOOM=13
```

### Local Development (`.env.local`)

```env
# Backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/molymarket
JWT_SECRET_KEY=dev-secret-key-do-not-use-in-production
GOOGLE_MAPS_API_KEY=<tu key>
ORS_API_KEY=<tu key>
MAPBOX_API_KEY=<tu key>
OPENAI_API_KEY=<tu key>
ENVIRONMENT=development
LOG_LEVEL=debug
CORS_ORIGINS=["http://localhost:3000"]
DEPOT_LAT=-32.91973
DEPOT_LNG=-68.81829

# Frontend (.env.local en /frontend)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 5.6 Configuración PostGIS

### Instalación Local (desarrollo)

```bash
# Windows (con PostgreSQL ya instalado)
# PostGIS viene como extension pack en el installer de PostgreSQL
# Verificar en Stack Builder o reinstalar con PostGIS habilitado

# Docker (recomendado para desarrollo)
docker run -d \
  --name molymarket-db \
  -e POSTGRES_DB=molymarket \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgis/postgis:16-3.4
```

### Habilitación en la Base de Datos

```sql
-- Ya incluido en migración 001 de Alembic
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verificar
SELECT PostGIS_Version();
-- Esperado: "3.4 ..."
```

### Uso en SQLAlchemy (GeoAlchemy2)

```python
# app/models/remito.py
from geoalchemy2 import Geometry
from sqlalchemy import Column, Float

class Remito(Base):
    __tablename__ = "remitos"
    
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    ubicacion = Column(
        Geometry("POINT", srid=4326),
        nullable=True,
        comment="Computed from lat/lng. Index GIST para consultas espaciales."
    )
```

### Trigger para auto-calcular `ubicacion`

```sql
-- Incluido en migración 001
CREATE OR REPLACE FUNCTION update_ubicacion()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.lat IS NOT NULL AND NEW.lng IS NOT NULL THEN
        NEW.ubicacion = ST_SetSRID(ST_MakePoint(NEW.lng, NEW.lat), 4326);
    ELSE
        NEW.ubicacion = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_ubicacion
    BEFORE INSERT OR UPDATE OF lat, lng ON remitos
    FOR EACH ROW EXECUTE FUNCTION update_ubicacion();
```

### Índice Espacial

```sql
CREATE INDEX idx_remitos_ubicacion ON remitos USING GIST (ubicacion);
CREATE INDEX idx_geo_cache_ubicacion ON geo_cache USING GIST (ubicacion);
```

### Consultas Espaciales Útiles

```sql
-- Remitos dentro de N km del depósito
SELECT * FROM remitos
WHERE ST_DWithin(
    ubicacion::geography,
    ST_SetSRID(ST_MakePoint(-68.81829, -32.91973), 4326)::geography,
    15000  -- 15 km
);

-- Distancia al depósito en metros
SELECT numero, 
       ST_Distance(
           ubicacion::geography,
           ST_SetSRID(ST_MakePoint(-68.81829, -32.91973), 4326)::geography
       ) as distancia_m
FROM remitos
WHERE ubicacion IS NOT NULL
ORDER BY distancia_m;

-- Validar que está en Mendoza BBOX
SELECT * FROM remitos
WHERE NOT is_in_mendoza(lat, lng);
```

---

## 5.7 Deployment Detallado

### Backend en Railway

```
1. Crear proyecto en Railway
2. Agregar servicio "PostgreSQL" → seleccionar imagen postgis/postgis:16-3.4
3. Agregar servicio "Web Service" → conectar con repo Git
   - Root directory: /backend
   - Build command: pip install -r requirements.txt
   - Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
4. Variables de entorno: copiar del bloque 5.5
5. Linkear PostgreSQL → Backend (Railway auto-inyecta DATABASE_URL)
6. Custom domain (opcional): api.molymarket.com
```

**Dockerfile del backend:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dependencias de sistema para psycopg2 y geoalchemy2
RUN apt-get update && apt-get install -y \
    libpq-dev gcc libgeos-dev libproj-dev gdal-bin \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ejecutar migraciones al iniciar
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Frontend en Vercel

```
1. Conectar repo Git con Vercel
2. Root directory: /frontend
3. Framework preset: Next.js (auto-detectado)
4. Variables de entorno: copiar del bloque 5.5 (Vercel)
5. Custom domain (opcional): molymarket.vercel.app o app.molymarket.com
```

---

## 5.8 Orden Recomendado de Implementación (Módulo por Módulo)

Para quien implemente el sistema, el orden óptimo de archivos a crear es:

### Día 1: Infraestructura
```
1. backend/app/config.py           → Settings con todas las env vars
2. backend/app/database.py         → Engine + AsyncSession
3. backend/app/main.py             → App + CORS + health check
4. backend/app/models/*.py         → Todos los modelos ORM (en orden del doc 02)
5. alembic/versions/001_*.py       → Migración inicial
6. alembic/versions/002_*.py       → Seed carriers
7. alembic/versions/003_*.py       → Seed config
```

### Día 2: Utilities + Core Services
```
8.  backend/app/utils/haversine.py
9.  backend/app/utils/mendoza_bbox.py
10. backend/app/utils/address_normalization.py
11. backend/app/utils/gmaps_link_builder.py
12. backend/app/services/ai_service.py
13. backend/app/services/carrier_service.py
14. backend/app/services/address_service.py
15. backend/app/services/geocode_service.py
16. backend/app/services/window_service.py
```

### Día 3: Pipeline de Remitos
```
17. backend/app/services/remito_service.py     → process_remito() pipeline
18. backend/app/schemas/remito.py
19. backend/app/api/v1/remitos.py              → CRUD + ingest
20. backend/app/api/v1/auth.py                 → Login/JWT
21. backend/app/dependencies.py                → get_db, get_current_user
22. backend/app/api/router.py                  → Agrupa routers
```

### Día 4: Rutas
```
23. backend/app/services/distance_matrix_service.py
24. backend/app/services/route_optimizer.py
25. backend/app/services/route_service.py
26. backend/app/schemas/ruta.py
27. backend/app/api/v1/rutas.py
```

### Día 5: Entregas + QR
```
28. backend/app/services/delivery_service.py
29. backend/app/api/v1/qr.py
30. backend/app/api/v1/entregados.py
31. backend/app/api/v1/historico.py
```

### Día 6: Complementarios
```
32. backend/app/services/billing_service.py
33. backend/app/services/export_service.py
34. backend/app/api/v1/dashboard.py
35. backend/app/api/v1/config.py
36. backend/app/api/v1/billing.py
37. backend/app/api/v1/pedidos_listos.py
```

### Día 7-10: Frontend
```
38. frontend/src/lib/types.ts                 → Types/interfaces
39. frontend/src/lib/api.ts                   → HTTP client
40. frontend/src/context/AuthContext.tsx       → Auth provider
41. frontend/src/middleware.ts                 → Auth redirect
42. frontend/src/app/layout.tsx               → Root layout + sidebar
43. frontend/src/components/ui/*.tsx           → Componentes genéricos
44. frontend/src/app/login/page.tsx
45. frontend/src/app/dashboard/page.tsx
46. frontend/src/app/remitos/page.tsx
47. frontend/src/app/remitos/[id]/page.tsx
48. frontend/src/components/map/*.tsx          → Leaflet (dynamic import!)
49. frontend/src/app/rutas/generar/page.tsx
50. frontend/src/app/rutas/[id]/page.tsx
51. frontend/src/app/qr/page.tsx
52. frontend/src/app/reporte/page.tsx
53. frontend/src/app/historico/page.tsx
54. Resto de páginas secundarias
```

---

## 5.9 Mapeo Completo de Feature Flags

Las 80+ feature flags actuales del sistema Apps Script se migran así:

### Flags que se convierten en parámetros de CONFIG_RUTA (DB)

| Flag Original | Parámetro DB | Default |
|---------------|-------------|---------|
| `ENABLE_WINDOW_FILTER` | `utilizar_ventana` | `true` |
| `TIEMPO_ESPERA_MIN` | `tiempo_espera_min` | `10` |
| `HORA_DESDE_RUTA` | `hora_desde` | `09:00` |
| `HORA_HASTA_RUTA` | `hora_hasta` | `14:00` |
| `EVITAR_SALTOS_MIN` | `evitar_saltos_min` | `25` |
| `VUELTA_GALPON_MIN` | `vuelta_galpon_min` | `25` |
| `PROVEEDOR_MATRIX` | `proveedor_matrix` | `ors` |
| `VELOCIDAD_KMH` | `velocidad_kmh` | `35` |
| `MARGEN_HAVERSINE` | `margen_haversine` | `1.5` |
| `MAX_PASES_FILTER` | `max_pases_filter` | `2` |

### Flags que se convierten en Settings del backend (env vars)

| Flag Original | Env Var | Razón |
|--------------|---------|-------|
| `GOOGLE_MAPS_API_KEY` | `GOOGLE_MAPS_API_KEY` | Secreto |
| `ORS_API_KEY` | `ORS_API_KEY` | Secreto |
| `MAPBOX_API_KEY` | `MAPBOX_API_KEY` | Secreto |
| `OPENAI_API_KEY` | `OPENAI_API_KEY` | Secreto |
| `AI_MODEL` | `AI_MODEL` | Infraestructura |

### Flags que se eliminan

| Flag | Razón |
|------|-------|
| `HABILITAR_PREPROCESAMIENTO` | Siempre habilitado en el nuevo sistema |
| `ENABLE_DEFERRED_PROCESSING` | No hay triggers, todo es por endpoint |
| `USE_CACHE_SERVICE` | Cache es siempre DB |
| `WRITE_LAT_LNG_TO_SHEET` | No hay Sheets |
| `ENABLE_BILLING_TRACE` | Siempre habilitado |
| `ENABLE_SYNC_PEDIDOS_LISTOS` | Reemplazado por endpoint |
| Todas las flags `_DEBUG`, `_LOG` | Reemplazadas por `LOG_LEVEL` |

---

## 5.10 Testing

### Estrategia de Tests

```
backend/tests/
├── conftest.py                    # Fixtures: test DB, test client, sample data
├── unit/
│   ├── test_haversine.py          # Fórmula haversine con casos conocidos
│   ├── test_address_normalization.py  # NFD, abreviaciones, edge cases
│   ├── test_mendoza_bbox.py       # Puntos dentro/fuera de Mendoza
│   ├── test_carrier_regex.py      # 16 patrones contra strings reales
│   ├── test_sweep_algorithm.py    # Algoritmo sweep con puntos conocidos
│   ├── test_two_opt.py            # 2-opt mejora ruta subóptima
│   └── test_window_parser.py      # Parseo de observaciones con cascade
├── integration/
│   ├── test_remito_pipeline.py    # Pipeline completo con DB real
│   ├── test_route_generation.py   # Generación de ruta E2E
│   ├── test_delivery_flow.py      # ARMADO → ENTREGADO → HISTÓRICO
│   └── test_qr_scan.py           # Scan QR con validaciones
└── fixtures/
    ├── sample_remitos.json        # 20 remitos reales anonimizados
    ├── sample_addresses.json      # Direcciones de Mendoza para geocodificación
    └── expected_routes.json       # Rutas esperadas para comparación
```

### Datos de Test (extraídos del sistema actual)

Los datos de prueba deben extraerse de las hojas actuales antes del cutover. Script sugerido:

```python
# scripts/extract_test_data.py
"""
Conecta a la API WebApp actual y extrae datos para fixtures de testing.
Ejecutar ANTES del cutover para tener golden data.
"""
import json
import requests

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbz.../exec"

# Extraer remitos (anonimizar nombres)
# Extraer rutas generadas (para comparación de algoritmo)
# Extraer geocodificaciones exitosas (para cache seed)
```

---

## 5.11 Resumen de Decisiones Arquitectónicas

| Decisión | Justificación |
|----------|---------------|
| **PostgreSQL** (no MongoDB) | Datos altamente relacionales (remito → carrier, ruta → paradas). Transacciones ACID necesarias para el flujo de entrega. |
| **PostGIS** | Mendoza BBOX, distancias, queries espaciales, polar angle para sweep. Nativo en SQL. |
| **FastAPI** (no Django) | Async para Distance Matrix calls paralelos. Schemas Pydantic nativos. Swagger auto. |
| **SQLAlchemy 2.0** (no raw SQL) | ORM tipado, migraciones con Alembic, GeoAlchemy2 para PostGIS. |
| **httpx** (no requests) | Async. Múltiples geocode/DM calls en paralelo sin bloquear. |
| **Next.js App Router** (no Pages) | Server Components, layouts, loading states. Estándar 2026. |
| **Leaflet** (no Google Maps JS) | Gratis, OpenStreetMap tiles, sin API key para el mapa. Google Maps solo para enlaces de navegación. |
| **Railway** (no AWS/GCP) | Simplicidad. PostgreSQL + PostGIS en un click. Deploy desde Git. Sin DevOps overhead. |
| **Vercel** | Deploy nativo de Next.js. CDN global. Preview deployments por branch. |
| **JWT en httpOnly cookie** (no localStorage) | Seguridad: protege contra XSS. Funciona con CORS credentials. |
| **Corte limpio** (no dual-write) | Menor complejidad. Datos activos son pocos. Rollback simple. |

---

*Documento 05 de 05 — Serie Migración MolyMarket*
