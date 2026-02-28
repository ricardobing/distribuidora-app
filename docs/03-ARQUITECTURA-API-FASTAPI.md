# 03 — Arquitectura API (FastAPI)

**Stack:** Python 3.12 + FastAPI + SQLAlchemy 2.0 + GeoAlchemy2  
**Deploy:** Railway  
**Auth:** JWT (jose) + bcrypt

---

## 3.1 Estructura de Carpetas del Backend

```
backend/
├── alembic/
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_seed_carriers.py
│   │   └── 003_seed_config.py
│   └── env.py
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app, middleware, startup
│   ├── config.py                        # Settings (Pydantic BaseSettings)
│   ├── database.py                      # SQLAlchemy engine + session
│   ├── dependencies.py                  # Dependency injection (get_db, get_current_user)
│   │
│   ├── models/                          # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── remito.py                    # Remito model
│   │   ├── carrier.py                   # Carrier model
│   │   ├── pedido_listo.py              # PedidoListo model
│   │   ├── ruta.py                      # Ruta + RutaParada models
│   │   ├── geo_cache.py                 # GeoCache model
│   │   ├── historico.py                 # HistoricoEntregado model
│   │   ├── audit_log.py                 # AuditLog model
│   │   ├── billing.py                   # BillingTrace model
│   │   ├── config.py                    # ConfigRuta model
│   │   ├── usuario.py                   # Usuario model
│   │   └── distance_cache.py            # DistanceMatrixCache model
│   │
│   ├── schemas/                         # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── remito.py
│   │   ├── carrier.py
│   │   ├── ruta.py
│   │   ├── geocode.py
│   │   ├── config.py
│   │   ├── auth.py
│   │   └── common.py                   # Pagination, ErrorResponse, etc.
│   │
│   ├── api/                             # Routers (endpoints)
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── remitos.py              # CRUD remitos + ingesta
│   │   │   ├── carriers.py             # CRUD carriers
│   │   │   ├── rutas.py                # Generación y gestión de rutas
│   │   │   ├── qr.py                   # Escaneo QR (ARMADO)
│   │   │   ├── entregados.py           # Flujo de entrega
│   │   │   ├── historico.py            # Consulta y export histórico
│   │   │   ├── config.py               # CRUD configuración
│   │   │   ├── geocode.py              # Endpoints de geocodificación
│   │   │   ├── pedidos_listos.py       # Sync Pedidos Listos
│   │   │   ├── auth.py                 # Login, JWT, users
│   │   │   ├── dashboard.py            # Stats y métricas
│   │   │   └── billing.py              # Consulta costos API
│   │   └── router.py                   # Agrupa todos los routers v1
│   │
│   ├── services/                        # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── remito_service.py           # Ingesta, clasificación, pipeline
│   │   ├── carrier_service.py          # Detección y clasificación de transporte
│   │   ├── geocode_service.py          # Geocodificación multi-provider + cache
│   │   ├── address_service.py          # Normalización de direcciones
│   │   ├── route_service.py            # Generación de rutas (orquestador)
│   │   ├── route_optimizer.py          # Sweep, 2-opt, TSP, filtros
│   │   ├── distance_matrix_service.py  # Matrix API multi-provider
│   │   ├── window_service.py           # Parseo de ventanas horarias
│   │   ├── delivery_service.py         # Armado, entrega, histórico
│   │   ├── ai_service.py              # Wrapper OpenAI (clasificación, normalización)
│   │   ├── billing_service.py          # Tracking de costos
│   │   ├── export_service.py           # Export XLSX mensual
│   │   └── pedidos_listos_service.py   # Sync con PL externo
│   │
│   ├── core/                            # Utilidades core
│   │   ├── __init__.py
│   │   ├── security.py                 # JWT, password hashing
│   │   ├── haversine.py                # Cálculo de distancia Haversine
│   │   ├── constants.py                # Constantes del negocio (bbox, carriers, etc.)
│   │   ├── exceptions.py               # Excepciones custom
│   │   └── validators.py               # Validadores de Mendoza bbox, etc.
│   │
│   └── tasks/                           # Background tasks
│       ├── __init__.py
│       ├── process_pending.py           # Equivalente a onChangeInstallable
│       └── monthly_close.py             # Cierre mensual automático
│
├── tests/
│   ├── conftest.py
│   ├── test_remitos.py
│   ├── test_carriers.py
│   ├── test_routes.py
│   ├── test_geocode.py
│   ├── test_qr.py
│   └── test_windows.py
│
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## 3.2 Configuración (`app/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@host:port/db
    
    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 horas
    ALGORITHM: str = "HS256"
    
    # API Keys
    GOOGLE_MAPS_API_KEY: str
    OPENAI_API_KEY: str
    ORS_API_KEY: str
    MAPBOX_TOKEN: str
    
    # QR Token
    QR_TOKEN: str
    
    # Geocoding
    GEOCODE_PROVIDER_ORDER: list[str] = ["ors", "mapbox", "google"]
    MENDOZA_LAT_MIN: float = -33.5
    MENDOZA_LAT_MAX: float = -32.0
    MENDOZA_LNG_MIN: float = -69.5
    MENDOZA_LNG_MAX: float = -68.0
    
    # Distance Matrix
    DM_BLOCK_SIZE: int = 10
    DM_CACHE_TTL_SECONDS: int = 21600  # 6h
    DM_MAX_DESTINATIONS: int = 25
    
    # Route
    DEFAULT_DEPOT_LAT: float = -32.91973
    DEFAULT_DEPOT_LNG: float = -68.81829
    MAX_DISTANCE_KM: float = 45.0
    URBAN_SPEED_KMH: float = 40.0
    
    # OpenAI
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.0
    AI_CONFIDENCE_THRESHOLD: float = 0.99
    AI_CANON_THRESHOLD: float = 0.92
    
    # Legacy compat
    PEDIDOS_LISTOS_SPREADSHEET_ID: str = ""
    
    # App
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    
    class Config:
        env_file = ".env"
```

---

## 3.3 Listado Completo de Endpoints

### Auth (`/api/v1/auth`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| POST | `/login` | `{email, password}` | `{access_token, token_type, user}` | Login, retorna JWT |
| POST | `/register` | `{email, nombre, password, rol}` | `{id, email, nombre, rol}` | Crear usuario (admin only) |
| GET | `/me` | — | `{id, email, nombre, rol}` | Datos del usuario autenticado |
| PUT | `/me/password` | `{old_password, new_password}` | `{ok: true}` | Cambiar contraseña |

### Remitos (`/api/v1/remitos`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| GET | `/` | `?estado=&lifecycle=&carrier=&page=&size=` | `{items: Remito[], total, page, pages}` | Listar remitos con filtros |
| GET | `/{id}` | — | `Remito` | Detalle de un remito |
| GET | `/by-numero/{numero}` | — | `Remito` | Buscar por número de remito |
| POST | `/ingest` | `{remitos: string[], source: string}` | `{ok, total, nuevos, duplicados, errores}` | Ingesta batch (reemplaza doPost) |
| POST | `/ingest-single` | `{numero, domicilio?, observaciones?}` | `Remito` | Ingesta individual con datos opcionales |
| PUT | `/{id}` | `{domicilio_normalizado?, urgente?, prioridad?, ...}` | `Remito` | Actualizar remito |
| PUT | `/{id}/corregir-direccion` | `{direccion_nueva}` | `Remito` | Corregir dirección → re-geocodificar |
| PUT | `/{id}/clasificacion` | `{estado, motivo}` | `Remito` | Cambiar estado de clasificación |
| DELETE | `/{id}` | — | `{ok: true}` | Eliminar remito |
| POST | `/reprocess/{id}` | — | `Remito` | Re-ejecutar pipeline completo |
| GET | `/pendientes` | — | `Remito[]` | Remitos con domicilio vacío (pendientes) |
| POST | `/process-pending` | — | `{processed: int, errors: int}` | Procesar todos los pendientes |

### QR / ARMADO (`/api/v1/qr`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| GET | `/scan` | `?remito={num}&token={token}` | `{ok, remito, message, version}` | Escaneo QR individual (compat legacy) |
| POST | `/scan` | `{remito: string, token: string}` | `{ok, remito, message, version}` | Escaneo QR por POST |
| POST | `/scan-batch` | `{remitos: string[], token: string}` | `{ok, results: [{remito, ok, message}]}` | Escaneo QR batch |

### Entregas (`/api/v1/entregados`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| POST | `/marcar` | `{remito_ids: int[]}` | `{ok, procesados, rechazados: [{id, motivo}]}` | Marcar como entregados (valida ARMADO) |
| POST | `/procesar` | `{remito_ids: int[]}` | `{ok, movidos_historico, rechazados}` | Procesar entregados → mover a histórico |

### Histórico (`/api/v1/historico`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| GET | `/` | `?mes=&page=&size=` | `{items: Historico[], total, page, pages}` | Listar histórico con filtros |
| GET | `/export/{mes}` | — | Binary (XLSX) | Exportar mes como XLSX |
| POST | `/restaurar/{id}` | — | `Remito` | Restaurar de histórico a activo |
| POST | `/cierre-mensual` | — | `{ok, exportados, eliminados}` | Ejecutar cierre mensual |

### Rutas (`/api/v1/rutas`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| POST | `/generar` | `{config?: ConfigRuta}` | `Ruta` (con paradas y excluidos) | Generar ruta optimizada |
| GET | `/` | `?fecha=&estado=` | `Ruta[]` | Listar rutas |
| GET | `/{id}` | — | `Ruta` (completa con paradas, excluidos, geom) | Detalle de ruta |
| GET | `/{id}/gmaps-links` | — | `{links: string[]}` | Google Maps links fragmentados |
| GET | `/{id}/geojson` | — | `GeoJSON FeatureCollection` | Ruta como GeoJSON (para Leaflet) |
| PUT | `/{id}/estado` | `{estado}` | `Ruta` | Cambiar estado de ruta |
| DELETE | `/{id}` | — | `{ok: true}` | Eliminar ruta |
| PUT | `/{id}/paradas/{parada_id}/estado` | `{estado}` | `RutaParada` | Marcar parada (entregada, saltada, etc.) |

### Carriers (`/api/v1/carriers`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| GET | `/` | — | `Carrier[]` | Listar todos los carriers |
| POST | `/` | `{nombre_canonico, aliases, regex_pattern, es_externo}` | `Carrier` | Crear carrier |
| PUT | `/{id}` | `{nombre_canonico?, aliases?, ...}` | `Carrier` | Actualizar carrier |
| POST | `/detect` | `{texto}` | `{carrier, confidence, source}` | Detectar carrier en texto |

### Geocodificación (`/api/v1/geocode`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| POST | `/` | `{address, provider?}` | `{lat, lng, formatted, source, confidence}` | Geocodificar dirección |
| POST | `/batch` | `{addresses: string[]}` | `[{address, lat, lng, source}]` | Geocodificación batch |
| GET | `/cache/stats` | — | `{total, by_provider, hit_rate}` | Estadísticas del cache |
| DELETE | `/cache` | — | `{deleted: int}` | Purgar cache de geocodificación |
| POST | `/validate` | `{lat, lng}` | `{valid, in_mendoza, issues}` | Validar coordenadas |

### Configuración (`/api/v1/config`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| GET | `/` | — | `ConfigRuta[]` | Toda la configuración |
| GET | `/{key}` | — | `ConfigRuta` | Valor de una key |
| PUT | `/{key}` | `{value}` | `ConfigRuta` | Actualizar configuración |
| POST | `/reset` | — | `{ok: true}` | Reset a valores por defecto |

### Pedidos Listos (`/api/v1/pedidos-listos`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| POST | `/sync` | `{data: [{numero_remito, cliente, domicilio, ...}]}` | `{ok, total, nuevos, actualizados}` | Sync batch de datos PL |
| POST | `/upload-csv` | Multipart (CSV/XLSX) | `{ok, total, nuevos}` | Upload masivo de PL |
| GET | `/` | `?page=&size=` | `{items, total, page, pages}` | Listar datos PL |

### Dashboard (`/api/v1/dashboard`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| GET | `/stats` | — | `{remitos_hoy, pendientes, armados, rutas_activas, ...}` | Métricas en tiempo real |
| GET | `/stats/costos` | `?desde=&hasta=` | `{total_usd, by_service, by_stage}` | Costos de API |
| GET | `/stats/entregas` | `?desde=&hasta=` | `{total, por_carrier, por_dia}` | Estadísticas de entregas |

### Billing (`/api/v1/billing`)

| Método | Ruta | Request | Response | Descripción |
|--------|------|---------|----------|-------------|
| GET | `/` | `?desde=&hasta=&service=` | `BillingTrace[]` | Consultar trazas de billing |
| GET | `/summary` | `?run_id=` | `{total_units, by_service, estimated_cost}` | Resumen de un run |

---

## 3.4 Servicios — Migración de Lógica

### `remito_service.py` — Pipeline de procesamiento

Migra: `processRowByIndex()`, `recibirRemitosFraccionados_()`, `onChangeInstallable()`

```python
class RemitoService:
    async def ingest_batch(self, numeros: list[str], source: str) -> IngestResult:
        """
        Migra: recibirRemitosFraccionados_()
        1. Deduplicar contra DB (remitos + historico)
        2. Crear registros con estado 'pendiente'
        3. Para cada nuevo: ejecutar pipeline
        4. Retornar resultado
        """
    
    async def process_pipeline(self, remito_id: int) -> Remito:
        """
        Migra: processRowByIndex() (7 pasos)
        
        Paso 0.5: preprocessRemitoIngress_ → address_service.normalize()
        Paso 0.7: lookup PL → pedidos_listos_service.lookup()
        Paso 1: ¿Retiro? → carrier_service.detect_pickup()
        Paso 2: ¿Carrier externo? → carrier_service.detect_carrier()
        Paso 3: Validar dirección → address_service.validate()
        Paso 4: Normalizar AI → ai_service.normalize_address()
        Paso 5: Geocodificar → geocode_service.geocode()
        Paso 6: Ventana horaria → window_service.parse()
        Paso 7: Estado final = 'enviar'
        """
    
    async def process_pending(self) -> ProcessResult:
        """
        Migra: onChangeInstallable() + processPendientes_()
        SELECT * FROM remitos 
        WHERE domicilio_normalizado IS NULL 
          AND estado_clasificacion = 'pendiente'
        → process_pipeline() para cada uno
        """
```

### `carrier_service.py` — Clasificación de transporte

Migra: `classifyTransportRegex_()`, `classifyTransportAI_()`, `determinarCategoriaFinal_()`

```python
class CarrierService:
    async def detect(self, texto: str, provincia: str = None) -> CarrierDetection:
        """
        Cascade:
        1. Cargar carriers con regex_pattern de DB (ordenados por prioridad)
        2. Probar cada regex contra texto (case insensitive)
        3. Si no match → AI fallback (ai_service)
        4. determinarCategoriaFinal_ (Mendoza → Envío propio, etc.)
        """
    
    def detect_pickup(self, texto: str) -> bool:
        """Regex RE_PICKUP hardcoded (pickup es estable, no necesita DB)"""
    
    async def detect_carrier_regex(self, texto: str) -> Optional[Carrier]:
        """Carriers de DB con regex, ordenados por prioridad_regex ASC"""
    
    async def detect_carrier_ai(self, texto: str) -> Optional[CarrierDetection]:
        """OpenAI fallback → re-validate through detect_carrier_regex"""
    
    def determinar_categoria_final(
        self, carrier: Optional[str], provincia: Optional[str]
    ) -> str:
        """
        Rules:
        1. carrier conocido → retornar
        2. RETIRA/RETIRO → RETIRO EN COMERCIAL
        3. provincia ≠ Mendoza → DESCONOCIDO
        4. Mendoza + sin carrier → ENVÍO PROPIO (MOLLY MARKET)
        5. default → DESCONOCIDO
        """
```

### `geocode_service.py` — Geocodificación multi-provider

Migra: `geocodificar_()`, `geocodificadorCascade_()`, `validateGeoResult_()`

```python
class GeocodeService:
    async def geocode(self, address: str, provider: str = None) -> GeocodeResult:
        """
        1. Normalizar dirección (normalizarDireccion_)
        2. Buscar en geo_cache (DB → reemplaza 4 capas de cache)
        3. Si cache miss → cascade de proveedores
        4. Validar resultado (Mendoza bbox, no genérico, etc.)
        5. Guardar en cache
        """
    
    async def geocode_ors(self, address: str) -> RawGeocodeResult:
        """ORS: api.openrouteservice.org/geocode/search"""
    
    async def geocode_mapbox(self, address: str) -> RawGeocodeResult:
        """Mapbox: api.mapbox.com/geocoding/v5/mapbox.places/"""
    
    async def geocode_google(self, address: str) -> RawGeocodeResult:
        """Google: maps.googleapis.com/maps/api/geocode/json"""
    
    def validate_result(self, result: RawGeocodeResult, query: str) -> bool:
        """
        Validaciones:
        1. Coords no nulas y no (0,0)
        2. Dentro de Mendoza bounds (-33.5 a -32.0 lat, -69.5 a -68.0 lng)
        3. No es nombre genérico de localidad
        4. Localidad del resultado coincide con consulta
        5. No es coordenada de centro conocido (±0.001°)
        """
```

### `route_service.py` — Generación de rutas

Migra: `generarRutaDesdeFraccionados_()` (orquestador)

```python
class RouteService:
    async def generate(self, config: RouteConfig = None) -> Ruta:
        """
        Migra todo el pipeline:
        1. Cargar candidatos (enviar + armado + geom not null)
        2. Filtrar por ventana horaria
        3. Filtrar saltos, vuelta al galpón, distancia máxima
        4. Obtener Distance Matrix (NxN)
        5. Optimizar (Sweep + 2-opt)
        6. Generar Google Maps links
        7. Guardar ruta + paradas + excluidos
        8. Retornar ruta completa
        """
```

### `route_optimizer.py` — Algoritmos de optimización

Migra: `sweepAlgorithm_()`, `twoOptImprove_()`, `tspNearestNeighbor_()`

```python
class RouteOptimizer:
    @staticmethod
    def sweep(depot_lat: float, depot_lng: float, 
              points: list[Point]) -> list[int]:
        """
        Sweep algorithm: ángulo polar desde depósito.
        θ = atan2(lat_i - lat_dep, lng_i - lng_dep)
        Orden: ascendente por θ
        """
    
    @staticmethod
    def two_opt(order: list[int], matrix: list[list[float]],
                lock_start: bool = False, lock_end: bool = False) -> list[int]:
        """
        2-opt local search.
        Δ = [d(A,C) + d(B,D)] - [d(A,B) + d(C,D)]
        Si Δ < -1e-6 → invertir segmento [i..k]
        Iterar hasta convergencia.
        """
    
    @staticmethod
    def nearest_neighbor(matrix: list[list[float]], start: int,
                         fixed_end: int = -1) -> list[int]:
        """TSP nearest neighbor: siempre ir al no visitado más cercano."""
    
    def optimize(self, points: list[RoutePoint], 
                 matrix: list[list[float]], 
                 depot: Point) -> OptimizedRoute:
        """
        Pipeline completo:
        1. Clasificar: URGENTE / PRI_AM / PRI_PM / NORM_AM / NORM_PM
        2. URGENTES: sweep + 2-opt
        3. PRIORIDAD: sweep only
        4. NORMALES: sweep only
        5. Concat: URG → AM_PRI → AM_NORM → PM_PRI → PM_NORM
        6. fixpoint_filter_jumps post-optimización
        """
    
    @staticmethod
    def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Distancia haversine en km. R = 6371 km."""
    
    def fixpoint_filter_jumps(self, order: list[int], 
                               matrix: list[list[float]],
                               threshold_min: float) -> tuple[list[int], list[int]]:
        """
        Filtro iterativo de saltos post-optimización.
        Max 10 iteraciones. Excluye punto con mayor salto.
        """
```

### `distance_matrix_service.py` — Distance Matrix multi-provider

Migra: `getMatrix_()`, `calcularMatrizNxN_()`

```python
class DistanceMatrixService:
    async def get_matrix_nxn(self, points: list[Point]) -> list[list[float]]:
        """
        Construir matriz NxN en bloques de BLOCK_SIZE × BLOCK_SIZE.
        1. Verificar cache de pares (distance_matrix_cache)
        2. Para pares sin cache → llamar API
        3. Guardar en cache
        4. Fill diagonal con 0, missing con 9e9
        """
    
    async def get_matrix_1xn(self, origin: Point, 
                              destinations: list[Point]) -> list[float]:
        """1 origen × N destinos para filtro vuelta al galpón."""
    
    async def _call_ors(self, origins, destinations) -> MatrixResult:
        """ORS: POST /v2/matrix/driving-car"""
    
    async def _call_google(self, origins, destinations) -> MatrixResult:
        """Google: Distance Matrix API"""
    
    async def _call_mapbox(self, origins, destinations) -> MatrixResult:
        """Mapbox: directions-matrix/v1/mapbox/driving/"""
```

### `window_service.py` — Parseo de ventanas horarias

Migra: `interpretarObservacionUnificado_()`, `asignarVentana_()`

```python
class WindowService:
    def parse(self, observation_text: str) -> WindowResult:
        """
        Cascade:
        1. Regex RETIRA/RETIRO → tipo PICKUP
        2. Keyword carrier → tipo CARRIER
        3. Formato HH:MM-HH:MM → tipo VENTANA
        4. "DESDE LAS HH:MM" → VENTANA
        5. "HASTA LAS HH:MM" → VENTANA
        6. Palabras vagas: MAÑANA→08-13, TARDE→16-21, HORARIO COMERCIAL→09-18
        7. AI fallback (OpenAI)
        
        Returns: WindowResult(tipo, desde_min, hasta_min, raw_text)
        """
    
    def assign_am_pm(self, windows: list[WindowResult]) -> str:
        """
        AM: 09:00-13:00 (540-780 min)
        PM: 14:00-18:00 (840-1080 min)
        Retorna: 'AM', 'PM', o 'SIN_HORARIO'
        """
    
    def is_within_config_window(self, window: WindowResult,
                                 hora_desde: int, hora_hasta: int) -> bool:
        """Intersección de rangos para filtro de ventana."""
```

### `address_service.py` — Normalización de direcciones

Migra: `normalizarDireccion_()`, `reemplazarCiudadMendoza_()`, `extraerCalleBase_()`

```python
class AddressService:
    @staticmethod
    def normalize(address: str) -> str:
        """
        1. NFD decomposition → strip diacríticos
        2. Lowercase
        3. Expandir: av→avenida, dpto→departamento, bv→boulevard,
           cjal→concejal, gral→general, etc.
        4. Colapsar espacios
        """
    
    @staticmethod
    def fix_ciudad_mendoza(address: str) -> str:
        """CIUDAD, MENDOZA → MENDOZA, MENDOZA"""
    
    @staticmethod
    def extract_street_base(address: str) -> str:
        """Extraer nombre de calle sin números ni prefijos."""
    
    @staticmethod
    def reorder_components(address: str) -> str:
        """Reordenar: CALLE NUMERO, LOCALIDAD, MENDOZA"""
    
    KNOWN_LOCALITIES = [
        "GODOY CRUZ", "GUAYMALLÉN", "LAS HERAS", "LUJÁN DE CUYO",
        "MAIPÚ", "SAN RAFAEL", "CAPITAL", "CIUDAD", "MENDOZA",
        "TUNUYÁN", "SAN MARTÍN", "RIVADAVIA", "JUNÍN"
    ]
```

### `ai_service.py` — Wrapper OpenAI

Migra: todas las llamadas a OpenAI dispersas en el código

```python
class AIService:
    async def classify_transport(self, texto: str) -> AIClassification:
        """
        Model: gpt-4o-mini, temperature=0
        System: "Sos un clasificador de textos de logística en Argentina..."
        Returns: {transportista: str, confianza: float}
        """
    
    async def normalize_address(self, address: str) -> AINormalization:
        """
        Canonización de dirección.
        Returns: {direccion_normalizada, confianza, localidad}
        """
    
    async def resolve_poi(self, name: str, context: str = "Mendoza") -> POIResolution:
        """
        Resolver nombre de POI a dirección canónica.
        Returns: {direccion, lat, lng, confianza}
        """
    
    async def extract_time_window(self, texto: str) -> str:
        """
        Extraer ventana horaria de texto libre.
        Returns: "HH:MM-HH:MM" o "NONE"
        """
    
    async def validate_address(self, address: str) -> AIValidation:
        """
        Validar si una dirección es geocodificable.
        Returns: {geocodeable: bool, confianza: float}
        """
```

### `delivery_service.py` — Flujo de entrega

Migra: QR handlers, `procesarEntregadosDesdeMenu()`, histórico

```python
class DeliveryService:
    async def scan_qr(self, numero: str) -> QRResult:
        """
        Migra: _procesarUnRemito_()
        1. Buscar remito por número
        2. Si no existe → error
        3. Si ya ARMADO → "Ya estaba ARMADO"
        4. Si DESPACHADO → no retroceder
        5. Marcar ARMADO + timestamp
        """
    
    async def mark_entregado(self, remito_ids: list[int]) -> EntregadoResult:
        """
        Migra: procesarEntregadosDesdeMenu()
        1. Validar que todos estén ARMADO
        2. Rechazar los que no están ARMADO
        3. Marcar entregados
        """
    
    async def move_to_historico(self, remito_ids: list[int]) -> HistoricoResult:
        """
        Migra: movimiento a HISTÓRICO_ENTREGADOS
        1. Crear registro en historico_entregados (snapshot)
        2. Cambiar estado_lifecycle = 'historico'
        """
    
    async def restore_from_historico(self, historico_id: int) -> Remito:
        """Restaurar de histórico a estado activo."""
    
    async def monthly_close(self) -> CloseResult:
        """
        Migra: cierreMensualAutomatico()
        1. Seleccionar entregas del mes anterior
        2. Generar XLSX
        3. Archivar
        """
```

---

## 3.5 Schemas Pydantic (Request/Response)

### `schemas/remito.py`

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RemitoBase(BaseModel):
    numero: str
    cliente: Optional[str] = None
    domicilio_raw: Optional[str] = None
    observaciones_pl: Optional[str] = None
    urgente: bool = False
    prioridad: bool = False

class RemitoCreate(BaseModel):
    remitos: list[str]       # Lista de números de remito
    source: str = "manual"   # 'manual', 'python', 'pedidos_listos'

class RemitoUpdate(BaseModel):
    domicilio_normalizado: Optional[str] = None
    urgente: Optional[bool] = None
    prioridad: Optional[bool] = None
    observaciones_entrega: Optional[str] = None

class RemitoResponse(RemitoBase):
    id: int
    domicilio_normalizado: Optional[str]
    localidad: Optional[str]
    provincia: Optional[str]
    estado_clasificacion: str
    motivo_clasificacion: Optional[str]
    estado_lifecycle: str
    lat: Optional[float]
    lng: Optional[float]
    geocode_source: Optional[str]
    carrier_nombre: Optional[str]
    ventana_tipo: Optional[str]
    ventana_desde_min: Optional[int]
    ventana_hasta_min: Optional[int]
    fecha_ingreso: datetime
    fecha_armado: Optional[datetime]
    fecha_entregado: Optional[datetime]
    
    class Config:
        from_attributes = True

class IngestResponse(BaseModel):
    ok: bool
    total: int
    nuevos: int
    duplicados: int
    errores: list[str] = []
    version: str
```

### `schemas/ruta.py`

```python
class RouteConfig(BaseModel):
    tiempo_espera_min: int = 10
    deposito_lat: float = -32.91973
    deposito_lng: float = -68.81829
    hora_desde: str = "09:00"
    hora_hasta: str = "14:00"
    evitar_saltos_min: int = 25
    vuelta_galpon_min: int = 25
    proveedor_matrix: str = "ors"
    utilizar_ventana: bool = True

class RutaParadaResponse(BaseModel):
    id: int
    orden: int
    remito_numero: str
    cliente: str
    direccion: str
    lat: float
    lng: float
    minutos_desde_anterior: Optional[float]
    tiempo_espera_min: Optional[float]
    minutos_acumulados: Optional[float]
    observaciones: Optional[str]
    es_urgente: bool
    es_prioridad: bool
    ventana_tipo: Optional[str]
    estado: str

class RutaExcluidoResponse(BaseModel):
    remito_numero: str
    cliente: str
    direccion: str
    motivo: str
    distancia_km: Optional[float]

class RutaResponse(BaseModel):
    id: int
    fecha: str
    estado: str
    total_paradas: int
    total_excluidos: int
    duracion_estimada_min: Optional[int]
    distancia_total_km: Optional[float]
    gmaps_links: list[str]
    paradas: list[RutaParadaResponse]
    excluidos: list[RutaExcluidoResponse]
    config: RouteConfig
    api_cost_estimate: Optional[float]
    created_at: datetime

class RutaGeoJSON(BaseModel):
    """GeoJSON FeatureCollection para Leaflet"""
    type: str = "FeatureCollection"
    features: list[dict]  # Feature objects con Point/LineString
```

### `schemas/auth.py`

```python
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserResponse(BaseModel):
    id: int
    email: str
    nombre: str
    rol: str
```

---

## 3.6 Middleware y Startup

### `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verificar conexión DB, cargar carriers en cache
    yield
    # Shutdown: cerrar conexiones

app = FastAPI(
    title="MolyMarket API",
    version="1.0.0",
    description="Sistema de distribución de alimentos - Mendoza",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://molymarket.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
from app.api.router import api_router
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
```

### Background Tasks

```python
# app/tasks/process_pending.py
# Reemplaza onChangeInstallable — se ejecuta como background task
# después de cada ingesta, o como endpoint manual

async def process_pending_remitos(db: AsyncSession):
    """
    SELECT id FROM remitos 
    WHERE domicilio_normalizado IS NULL 
      AND estado_clasificacion = 'pendiente'
    
    Para cada uno → remito_service.process_pipeline(id)
    """
```

---

## 3.7 Dependencias (`requirements.txt`)

```
# Core
fastapi==0.115.*
uvicorn[standard]==0.34.*
python-dotenv==1.0.*

# Database
sqlalchemy[asyncio]==2.0.*
asyncpg==0.30.*
geoalchemy2==0.15.*
alembic==1.14.*

# Auth
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*

# HTTP Client (para APIs externas)
httpx==0.28.*

# Data
pydantic==2.10.*
pydantic-settings==2.7.*

# OpenAI
openai==1.61.*

# Export
openpyxl==3.1.*

# Utilities
unidecode==1.3.*       # Para normalización de direcciones (reemplazo de NFD manual)

# Testing
pytest==8.3.*
pytest-asyncio==0.25.*
httpx                  # TestClient
factory-boy==3.3.*
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# PostGIS client libraries (para GeoAlchemy2)
RUN apt-get update && apt-get install -y \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

*Documento 03 de 05 — Serie Migración MolyMarket*
