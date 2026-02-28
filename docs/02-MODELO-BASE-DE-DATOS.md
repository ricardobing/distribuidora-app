# 02 — Modelo de Base de Datos (PostgreSQL + PostGIS)

**Stack:** PostgreSQL 16 + PostGIS 3.4  
**Deploy:** Railway (managed PostgreSQL con PostGIS habilitado)  
**ORM:** SQLAlchemy 2.0 + GeoAlchemy2

---

## 2.1 Diagrama Entidad-Relación

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│    carriers     │     │     remitos      │     │   pedidos_listos  │
│─────────────────│     │──────────────────│     │───────────────────│
│ id (PK)         │◄───┤ carrier_id (FK)  │     │ id (PK)           │
│ nombre_canonico │     │ id (PK)          │◄────┤ remito_id (FK)    │
│ aliases (JSONB) │     │ numero           │     │ cliente           │
│ es_externo      │     │ estado           │     │ domicilio_raw     │
│ activo          │     │ ...              │     │ localidad         │
└─────────────────┘     └──────┬───────────┘     │ provincia         │
                               │                 │ observaciones     │
┌─────────────────┐            │                 │ transporte_raw    │
│   geo_cache     │            │                 │ fecha_remito      │
│─────────────────│            │                 └───────────────────┘
│ id (PK)         │            │
│ key_normalizada │            │          ┌───────────────────┐
│ query_original  │            │          │    rutas          │
│ geom (POINT)    │            ├─────────►│───────────────────│
│ formatted       │            │          │ id (PK)           │
│ ...             │            │          │ fecha             │
└─────────────────┘            │          │ estado            │
                               │          │ config (JSONB)    │
┌─────────────────┐            │          │ total_paradas     │
│   config_ruta   │            │          │ ...               │
│─────────────────│            │          └────────┬──────────┘
│ id (PK)         │            │                   │
│ key             │            │          ┌────────▼──────────┐
│ value           │            │          │  ruta_paradas     │
│ updated_at      │            ├─────────►│───────────────────│
└─────────────────┘            │          │ id (PK)           │
                               │          │ ruta_id (FK)      │
┌─────────────────┐            │          │ remito_id (FK)    │
│  audit_log      │◄───────────┘          │ orden             │
│─────────────────│                       │ minutos_anterior  │
│ id (PK)         │                       │ ...               │
│ remito_id (FK)  │                       └───────────────────┘
│ accion          │
│ detalle (JSONB) │           ┌───────────────────┐
│ created_at      │           │  billing_trace    │
└─────────────────┘           │───────────────────│
                              │ id (PK)           │
┌─────────────────┐           │ run_id            │
│    usuarios     │           │ service           │
│─────────────────│           │ sku               │
│ id (PK)         │           │ units             │
│ email           │           │ ...               │
│ nombre          │           └───────────────────┘
│ rol             │
│ activo          │
└─────────────────┘
```

---

## 2.2 Scripts SQL de Creación

### Extensión PostGIS

```sql
-- Habilitar PostGIS (Railway soporta esta extensión)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Para búsqueda fuzzy de direcciones
```

### Tabla: carriers

```sql
CREATE TABLE carriers (
    id              SERIAL PRIMARY KEY,
    nombre_canonico VARCHAR(100) NOT NULL UNIQUE,
    aliases         JSONB NOT NULL DEFAULT '[]',
    -- aliases contiene: ["VIACARGO", "VIA  CARGO", "VIA CARGO"]
    regex_pattern   VARCHAR(500),
    -- regex para detección: 'VIA\s*CARGO|VIACARGO'
    es_externo      BOOLEAN NOT NULL DEFAULT TRUE,
    -- FALSE para "ENVÍO PROPIO (MOLLY MARKET)" y "RETIRO EN COMERCIAL"
    es_pickup       BOOLEAN NOT NULL DEFAULT FALSE,
    -- TRUE solo para "RETIRO EN COMERCIAL"
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    prioridad_regex INTEGER NOT NULL DEFAULT 50,
    -- Orden de evaluación del regex (menor = mayor prioridad)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Datos iniciales
INSERT INTO carriers (nombre_canonico, aliases, regex_pattern, es_externo, es_pickup, prioridad_regex) VALUES
('RETIRO EN COMERCIAL',           '["RETIRA EN COMERCIAL","RETIRO EN COMERC","RETIRA","RETIRO"]',
 '\b(?:RETIRA(?!R)(?:\s+POR|\s+EN)?\s*(?:COMERCIAL|DEPÓSITO|LOCAL|TIENDA|SUCURSAL)?|SE\s+RETIRA|RETIRO\s+CLIENTE|PASA\s+A\s+RETIRAR)\b',
 FALSE, TRUE, 1),
('ENVÍO PROPIO (MOLLY MARKET)',    '["ENVIO PROPIO","MOLLY MARKET","TRANSPORTE MOLLY MARKET","MOLLY","TRANSPORTE MOLLY","TRANSPORTES MOLLY MARKET"]',
 'TRANSPORTE\s*MOLLY\s*MARKET|ENV[IÍ]O\s*PROPIO',
 FALSE, FALSE, 3),
('VIA CARGO',                      '["VIACARGO","VIA  CARGO"]',
 'VIA\s*CARGO|VIACARGO', TRUE, FALSE, 4),
('BUS PACK',                       '[]', 'BUS\s*PACK', TRUE, FALSE, 5),
('VIA BARILOCHE',                  '[]', 'VIA\s*BARILOCHE', TRUE, FALSE, 6),
('CRUZ DEL SUR',                   '[]', 'CRUZ\s*DEL\s*SUR', TRUE, FALSE, 7),
('ANDESMAR',                       '[]', 'ANDESMAR', TRUE, FALSE, 8),
('ANDREANI',                       '["TRANSPORTE ANDREANI"]', 'ANDREANI', TRUE, FALSE, 9),
('OCASA',                          '[]', 'OCASA', TRUE, FALSE, 10),
('OCA',                            '[]', '\bOCA\b', TRUE, FALSE, 11),
('URBANO',                         '[]', 'URBANO', TRUE, FALSE, 12),
('ACORDIS',                        '[]', 'ACORDIS', TRUE, FALSE, 13),
('VELOX',                          '[]', 'VELOX', TRUE, FALSE, 14),
('TRANSPORTE VESRPINI',            '["TRANSPORTE VESPRINI","VESRPINI","VESPRINI","VSPRINI","VESPERINI"]',
 'VE?S[PR]+INI', TRUE, FALSE, 15),
('EXCLUIDO',                       '["EXCLUIDOS"]', 'EXCLU[IÍ]D[OA]S?', FALSE, FALSE, 2),
('DESCONOCIDO',                    '[]', NULL, FALSE, FALSE, 99);

CREATE INDEX idx_carriers_nombre ON carriers (nombre_canonico);
CREATE INDEX idx_carriers_activo ON carriers (activo) WHERE activo = TRUE;
```

### Tabla: remitos (tabla central)

```sql
CREATE TYPE remito_estado_fraccionados AS ENUM (
    'pendiente',        -- Ingresado, esperando procesamiento
    'enviar',           -- Listo para incluir en ruta
    'corregir',         -- Dirección necesita corrección manual
    'retiro_sospechado',-- Posible pickup
    'transporte_externo',-- Asignado a carrier externo
    'no_encontrado',    -- Error en procesamiento
    'excluido'          -- Excluido manualmente
);

CREATE TYPE remito_estado_lifecycle AS ENUM (
    'ingresado',   -- Recién ingresado al sistema
    'armado',      -- Paquete preparado (QR o manual)
    'despachado',  -- En camino
    'entregado',   -- Entrega confirmada
    'historico'    -- Archivado
);

CREATE TABLE remitos (
    id                      SERIAL PRIMARY KEY,
    numero                  VARCHAR(50) NOT NULL UNIQUE,
    -- Datos del remito
    cliente                 VARCHAR(255),
    domicilio_raw           TEXT,           -- Dirección original sin procesar
    domicilio_normalizado   TEXT,           -- Dirección procesada por IA/geocoding
    localidad               VARCHAR(100),
    provincia               VARCHAR(100),
    observaciones_pl        TEXT,           -- Observaciones de Pedidos Listos
    observaciones_entrega   TEXT,           -- Obs formateadas para la ruta
    transporte_raw          VARCHAR(255),   -- Transporte tal cual viene de PL
    -- Clasificación
    carrier_id              INTEGER REFERENCES carriers(id),
    estado_clasificacion    remito_estado_fraccionados NOT NULL DEFAULT 'pendiente',
    motivo_clasificacion    TEXT,           -- Razón del estado
    -- Ciclo de vida
    estado_lifecycle        remito_estado_lifecycle NOT NULL DEFAULT 'ingresado',
    -- Geocodificación
    geom                    GEOMETRY(Point, 4326),  -- PostGIS: lat/lng en SRID 4326
    geocode_formatted       TEXT,           -- Dirección formateada por geocoder
    geocode_has_street_num  BOOLEAN DEFAULT FALSE,
    geocode_source          VARCHAR(20),    -- 'cache', 'ors', 'mapbox', 'google'
    geocode_confidence      REAL,           -- Confianza 0.0-1.0
    -- Ventana horaria
    ventana_tipo            VARCHAR(20),    -- 'AM', 'PM', 'SIN_HORARIO'
    ventana_desde_min       INTEGER,        -- Minutos desde medianoche
    ventana_hasta_min       INTEGER,        -- Minutos desde medianoche
    ventana_raw             TEXT,           -- Texto original del horario
    llamar_antes            BOOLEAN DEFAULT FALSE,
    -- Flags de prioridad
    urgente                 BOOLEAN NOT NULL DEFAULT FALSE,
    prioridad               BOOLEAN NOT NULL DEFAULT FALSE,
    -- Metadata
    seq_id                  VARCHAR(50),    -- ID secuencial para trazabilidad
    source                  VARCHAR(20) NOT NULL DEFAULT 'manual',
    -- 'manual' (pegado), 'python' (WebApp POST), 'pedidos_listos' (sync)
    motivo_exclusion_ruta   TEXT,           -- Si fue excluido de la ruta, por qué
    transp_json             JSONB,          -- Snapshot completo (legacy compat)
    -- Timestamps
    fecha_ingreso           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_armado            TIMESTAMPTZ,
    fecha_entregado         TIMESTAMPTZ,
    fecha_historico         TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices principales
CREATE INDEX idx_remitos_numero ON remitos (numero);
CREATE INDEX idx_remitos_estado_class ON remitos (estado_clasificacion);
CREATE INDEX idx_remitos_estado_life ON remitos (estado_lifecycle);
CREATE INDEX idx_remitos_carrier ON remitos (carrier_id);
CREATE INDEX idx_remitos_fecha ON remitos (fecha_ingreso);
CREATE INDEX idx_remitos_urgente ON remitos (urgente) WHERE urgente = TRUE;
CREATE INDEX idx_remitos_prioridad ON remitos (prioridad) WHERE prioridad = TRUE;

-- Índice espacial PostGIS
CREATE INDEX idx_remitos_geom ON remitos USING GIST (geom);

-- Índice para búsqueda fuzzy de direcciones
CREATE INDEX idx_remitos_domicilio_trgm ON remitos USING GIN (domicilio_normalizado gin_trgm_ops);

-- Índice compuesto para la vista de ruta (filtrado rápido)
CREATE INDEX idx_remitos_ruta_candidates ON remitos (estado_clasificacion, estado_lifecycle)
    WHERE estado_clasificacion = 'enviar' AND estado_lifecycle = 'armado';
```

### Tabla: pedidos_listos (datos de referencia)

```sql
CREATE TABLE pedidos_listos (
    id              SERIAL PRIMARY KEY,
    remito_id       INTEGER REFERENCES remitos(id) ON DELETE SET NULL,
    numero_remito   VARCHAR(50) NOT NULL,
    cliente         VARCHAR(255),
    domicilio       TEXT,
    localidad       VARCHAR(100),
    provincia       VARCHAR(100),
    observaciones   TEXT,
    transporte      VARCHAR(255),
    fecha_remito    DATE,
    -- Metadata de sync
    source_row      INTEGER,           -- Fila original en el sheet
    synced_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_data        JSONB,             -- Fila completa original como JSON
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pl_numero ON pedidos_listos (numero_remito);
CREATE INDEX idx_pl_remito ON pedidos_listos (remito_id);
CREATE INDEX idx_pl_fecha ON pedidos_listos (fecha_remito);
CREATE UNIQUE INDEX idx_pl_unique_remito ON pedidos_listos (numero_remito);
```

### Tabla: geo_cache (cache de geocodificación)

```sql
CREATE TABLE geo_cache (
    id                  SERIAL PRIMARY KEY,
    key_normalizada     VARCHAR(500) NOT NULL UNIQUE,
    query_original      TEXT NOT NULL,
    geom                GEOMETRY(Point, 4326) NOT NULL,
    formatted_address   TEXT,
    has_street_number   BOOLEAN DEFAULT FALSE,
    provider            VARCHAR(20),     -- 'ors', 'mapbox', 'google'
    raw_response        JSONB,           -- Respuesta completa del geocoder
    score               REAL,            -- Score de calidad del resultado
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ      -- NULL = no expira
);

CREATE INDEX idx_geo_key ON geo_cache (key_normalizada);
CREATE INDEX idx_geo_geom ON geo_cache USING GIST (geom);
CREATE INDEX idx_geo_expires ON geo_cache (expires_at) WHERE expires_at IS NOT NULL;

-- Índice para deduplicación por proximidad
-- (se usa en queries: WHERE ST_DWithin(geom, ST_MakePoint(lng, lat)::geography, 10))
```

### Tabla: rutas (rutas generadas)

```sql
CREATE TYPE ruta_estado AS ENUM (
    'generando',   -- En proceso de generación
    'generada',    -- Lista para usar
    'en_curso',    -- Ruta activa (chofer en ruta)
    'completada',  -- Todas las entregas realizadas
    'cancelada'    -- Cancelada
);

CREATE TABLE rutas (
    id                  SERIAL PRIMARY KEY,
    fecha               DATE NOT NULL,
    estado              ruta_estado NOT NULL DEFAULT 'generando',
    -- Configuración usada para generar esta ruta
    config              JSONB NOT NULL,
    -- Ejemplo: {
    --   "tiempo_espera_min": 10,
    --   "deposito": {"lat": -32.91973, "lng": -68.81829, "direccion": "..."},
    --   "hora_desde": "09:00",
    --   "hora_hasta": "14:00",
    --   "evitar_saltos_min": 25,
    --   "vuelta_galpon_min": 25,
    --   "proveedor_matrix": "ors",
    --   "utilizar_ventana": true
    -- }
    -- Depósito como punto PostGIS
    deposito_geom       GEOMETRY(Point, 4326),
    -- Estadísticas
    total_paradas       INTEGER DEFAULT 0,
    total_excluidos     INTEGER DEFAULT 0,
    duracion_estimada_min INTEGER,
    distancia_total_km  REAL,
    -- Google Maps links (legacy compat)
    gmaps_links         TEXT[],
    -- Ruta como LineString PostGIS (para visualización)
    ruta_geom           GEOMETRY(LineString, 4326),
    -- Billing
    api_cost_estimate   REAL DEFAULT 0,
    billing_detail      JSONB,
    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rutas_fecha ON rutas (fecha);
CREATE INDEX idx_rutas_estado ON rutas (estado);
CREATE INDEX idx_rutas_geom ON rutas USING GIST (ruta_geom);
```

### Tabla: ruta_paradas (paradas de cada ruta)

```sql
CREATE TYPE parada_estado AS ENUM (
    'pendiente',   -- No visitada aún
    'en_camino',   -- Chofer en camino
    'entregada',   -- Entrega confirmada
    'fallida',     -- No se pudo entregar
    'saltada'      -- Saltada por el chofer
);

CREATE TABLE ruta_paradas (
    id                  SERIAL PRIMARY KEY,
    ruta_id             INTEGER NOT NULL REFERENCES rutas(id) ON DELETE CASCADE,
    remito_id           INTEGER NOT NULL REFERENCES remitos(id),
    -- Orden y tiempos
    orden               INTEGER NOT NULL,
    minutos_desde_anterior  REAL,
    tiempo_espera_min   REAL,
    minutos_acumulados  REAL,
    distancia_desde_anterior_km REAL,
    -- Snapshot de datos al momento de generar (inmutable)
    cliente_snapshot    VARCHAR(255),
    direccion_snapshot  TEXT,
    geom_snapshot       GEOMETRY(Point, 4326),
    observaciones_snapshot TEXT,
    -- Estado de la parada
    estado              parada_estado NOT NULL DEFAULT 'pendiente',
    -- Metadata
    es_urgente          BOOLEAN DEFAULT FALSE,
    es_prioridad        BOOLEAN DEFAULT FALSE,
    ventana_tipo        VARCHAR(20),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_paradas_ruta ON ruta_paradas (ruta_id, orden);
CREATE INDEX idx_paradas_remito ON ruta_paradas (remito_id);
CREATE INDEX idx_paradas_estado ON ruta_paradas (estado);
CREATE INDEX idx_paradas_geom ON ruta_paradas USING GIST (geom_snapshot);
```

### Tabla: ruta_excluidos (puntos excluidos de la ruta)

```sql
CREATE TABLE ruta_excluidos (
    id              SERIAL PRIMARY KEY,
    ruta_id         INTEGER NOT NULL REFERENCES rutas(id) ON DELETE CASCADE,
    remito_id       INTEGER NOT NULL REFERENCES remitos(id),
    motivo          TEXT NOT NULL,
    -- 'ventana_horaria', 'salto', 'vuelta_galpon', 'distancia_maxima', 'duracion_total'
    distancia_km    REAL,
    observaciones   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_excluidos_ruta ON ruta_excluidos (ruta_id);
CREATE INDEX idx_excluidos_remito ON ruta_excluidos (remito_id);
```

### Tabla: historico_entregados (archivo)

```sql
CREATE TABLE historico_entregados (
    id                  SERIAL PRIMARY KEY,
    remito_id           INTEGER NOT NULL REFERENCES remitos(id),
    -- Snapshot de los datos al momento de archivar
    numero_remito       VARCHAR(50) NOT NULL,
    cliente             VARCHAR(255),
    domicilio           TEXT,
    provincia           VARCHAR(100),
    observaciones       TEXT,
    carrier_nombre      VARCHAR(100),
    estado_al_archivar  VARCHAR(50),
    geom                GEOMETRY(Point, 4326),
    urgente             BOOLEAN DEFAULT FALSE,
    prioridad           BOOLEAN DEFAULT FALSE,
    obs_entrega         TEXT,
    transp_json         JSONB,
    -- Fechas del ciclo de vida
    fecha_ingreso       TIMESTAMPTZ,
    fecha_armado        TIMESTAMPTZ,
    fecha_entregado     TIMESTAMPTZ NOT NULL,
    fecha_archivado     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Metadata
    mes_cierre          VARCHAR(7),     -- '2026-02' para agrupación mensual
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_hist_remito ON historico_entregados (remito_id);
CREATE INDEX idx_hist_numero ON historico_entregados (numero_remito);
CREATE INDEX idx_hist_fecha ON historico_entregados (fecha_entregado);
CREATE INDEX idx_hist_mes ON historico_entregados (mes_cierre);
CREATE INDEX idx_hist_geom ON historico_entregados USING GIST (geom);
```

### Tabla: audit_log (log de auditoría)

```sql
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    remito_id       INTEGER REFERENCES remitos(id) ON DELETE SET NULL,
    accion          VARCHAR(100) NOT NULL,
    -- Acciones: 'INGRESO', 'CLASIFICACION', 'GEOCODE', 'ARMADO', 'ENTREGADO',
    --           'HISTORICO', 'RUTA_GENERADA', 'RUTA_EXCLUIDO', 'CORRECCION',
    --           'ENTREGADO_BLOCKED', 'QR_SCAN', etc.
    detalle         JSONB,
    ip_address      INET,
    user_agent      TEXT,
    user_id         INTEGER REFERENCES usuarios(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_remito ON audit_log (remito_id);
CREATE INDEX idx_audit_accion ON audit_log (accion);
CREATE INDEX idx_audit_fecha ON audit_log (created_at);
-- Índice parcial para acciones frecuentes
CREATE INDEX idx_audit_qr ON audit_log (created_at) WHERE accion = 'QR_SCAN';
```

### Tabla: billing_trace (costos de API)

```sql
CREATE TABLE billing_trace (
    id              BIGSERIAL PRIMARY KEY,
    run_id          VARCHAR(100),
    stage           VARCHAR(50),
    -- 'geocode', 'distance_matrix', 'ai_classify', 'ai_normalize', etc.
    service         VARCHAR(30) NOT NULL,
    -- 'google', 'ors', 'mapbox', 'openai'
    sku             VARCHAR(100),
    units           INTEGER NOT NULL DEFAULT 1,
    response_code   INTEGER,
    latency_ms      INTEGER,
    url_length      INTEGER,
    estimated_cost  REAL,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_billing_run ON billing_trace (run_id);
CREATE INDEX idx_billing_fecha ON billing_trace (created_at);
CREATE INDEX idx_billing_service ON billing_trace (service);
```

### Tabla: config_ruta (configuración del sistema)

```sql
CREATE TABLE config_ruta (
    id          SERIAL PRIMARY KEY,
    key         VARCHAR(100) NOT NULL UNIQUE,
    value       TEXT NOT NULL,
    tipo        VARCHAR(20) NOT NULL DEFAULT 'text',
    -- 'text', 'integer', 'float', 'boolean', 'time', 'json'
    descripcion TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Datos iniciales
INSERT INTO config_ruta (key, value, tipo, descripcion) VALUES
('tiempo_espera_min',    '10',     'integer', 'Minutos de parada por entrega'),
('usar_deposito',        'true',   'boolean', 'Usar depósito como origen/destino de ruta'),
('deposito_lat',         '-32.91973', 'float', 'Latitud del depósito'),
('deposito_lng',         '-68.81829', 'float', 'Longitud del depósito'),
('deposito_direccion',   'Elpidio González 2753, Guaymallén, Mendoza', 'text', 'Dirección del depósito'),
('hora_desde',           '09:00',  'time',    'Hora inicio ventana operativa'),
('hora_hasta',           '14:00',  'time',    'Hora fin ventana operativa'),
('evitar_saltos_min',    '25',     'integer', 'Umbral de salto en minutos'),
('vuelta_galpon_min',    '25',     'integer', 'Máximo tiempo de regreso al depósito'),
('proveedor_matrix',     'ors',    'text',    'Proveedor Distance Matrix: ors, mapbox, google'),
('proveedor_geocode',    'google', 'text',    'Proveedor geocoding primario'),
('utilizar_ventana',     'true',   'boolean', 'Activar filtro por ventana horaria'),
('distancia_max_km',     '45',     'float',   'Distancia máxima desde depósito en km'),
('velocidad_urbana_kmh', '40',     'float',   'Velocidad estimada urbana para Haversine'),
('max_waypoints_gmaps',  '10',     'integer', 'Máximo waypoints por link de Google Maps');
```

### Tabla: usuarios

```sql
CREATE TYPE user_rol AS ENUM (
    'admin',       -- Acceso total
    'operador',    -- Gestión de remitos y rutas
    'chofer',      -- Solo ver ruta asignada
    'viewer'       -- Solo lectura
);

CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    nombre          VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    rol             user_rol NOT NULL DEFAULT 'operador',
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usuarios_email ON usuarios (email);
CREATE INDEX idx_usuarios_activo ON usuarios (activo) WHERE activo = TRUE;
```

### Tabla: distance_matrix_cache

```sql
CREATE TABLE distance_matrix_cache (
    id              SERIAL PRIMARY KEY,
    origin_geom     GEOMETRY(Point, 4326) NOT NULL,
    dest_geom       GEOMETRY(Point, 4326) NOT NULL,
    duration_sec    INTEGER NOT NULL,
    distance_m      INTEGER,
    provider        VARCHAR(20) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL
);

-- Índice espacial compuesto para búsqueda de pares
CREATE INDEX idx_dm_cache_origin ON distance_matrix_cache USING GIST (origin_geom);
CREATE INDEX idx_dm_cache_dest ON distance_matrix_cache USING GIST (dest_geom);
CREATE INDEX idx_dm_cache_expires ON distance_matrix_cache (expires_at);

-- Para buscar un par específico con tolerancia:
-- WHERE ST_DWithin(origin_geom, ST_SetSRID(ST_MakePoint(lng1, lat1), 4326)::geography, 10)
--   AND ST_DWithin(dest_geom, ST_SetSRID(ST_MakePoint(lng2, lat2), 4326)::geography, 10)
--   AND expires_at > NOW()
```

---

## 2.3 Funciones PostGIS Útiles

```sql
-- Función: calcular distancia haversine entre dos puntos (metros)
-- Equivalente a haversineDistance_() del código actual
-- PostGIS lo hace nativamente:
SELECT ST_Distance(
    ST_SetSRID(ST_MakePoint(-68.81829, -32.91973), 4326)::geography,
    ST_SetSRID(ST_MakePoint(-68.85, -32.90), 4326)::geography
) / 1000 AS distancia_km;
-- Nota: ST_MakePoint usa (lng, lat), NO (lat, lng)

-- Función: verificar si un punto está dentro del bbox de Mendoza
CREATE OR REPLACE FUNCTION is_in_mendoza(geom GEOMETRY) RETURNS BOOLEAN AS $$
BEGIN
    RETURN ST_Within(
        geom,
        ST_MakeEnvelope(-69.5, -33.5, -68.0, -32.0, 4326)
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Función: calcular ángulo polar desde el depósito (para Sweep algorithm)
CREATE OR REPLACE FUNCTION polar_angle_from_depot(
    point_geom GEOMETRY,
    depot_lat DOUBLE PRECISION DEFAULT -32.91973,
    depot_lng DOUBLE PRECISION DEFAULT -68.81829
) RETURNS DOUBLE PRECISION AS $$
BEGIN
    RETURN atan2(
        ST_Y(point_geom) - depot_lat,
        ST_X(point_geom) - depot_lng
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Vista: remitos candidatos para ruta (reemplaza "Hoja 1")
CREATE OR REPLACE VIEW v_ruta_candidates AS
SELECT
    r.id,
    r.numero,
    r.cliente,
    r.domicilio_normalizado,
    ST_Y(r.geom) AS lat,
    ST_X(r.geom) AS lng,
    r.observaciones_entrega,
    r.ventana_tipo,
    r.ventana_desde_min,
    r.ventana_hasta_min,
    r.urgente,
    r.prioridad,
    r.llamar_antes,
    c.nombre_canonico AS carrier,
    polar_angle_from_depot(r.geom) AS angulo_polar,
    ST_Distance(
        r.geom::geography,
        ST_SetSRID(ST_MakePoint(-68.81829, -32.91973), 4326)::geography
    ) / 1000 AS distancia_deposito_km
FROM remitos r
LEFT JOIN carriers c ON r.carrier_id = c.id
WHERE r.estado_clasificacion = 'enviar'
  AND r.estado_lifecycle = 'armado'
  AND r.geom IS NOT NULL
ORDER BY r.urgente DESC, r.prioridad DESC;

-- Vista: reporte de transportes (reemplaza REPORTE_Transportes)
CREATE OR REPLACE VIEW v_reporte_transportes AS
SELECT
    r.id,
    r.numero AS remito,
    r.cliente,
    r.estado_lifecycle = 'armado' AS armado,
    r.estado_lifecycle = 'entregado' AS entregado,
    r.domicilio_normalizado AS domicilio,
    r.motivo_exclusion_ruta AS observaciones,
    c.nombre_canonico AS carrier,
    r.urgente,
    r.prioridad
FROM remitos r
LEFT JOIN carriers c ON r.carrier_id = c.id
WHERE r.estado_lifecycle IN ('ingresado', 'armado', 'despachado')
ORDER BY
    CASE c.nombre_canonico
        WHEN 'ENVÍO PROPIO (MOLLY MARKET)' THEN 1
        WHEN 'RETIRO EN COMERCIAL' THEN 2
        WHEN 'EXCLUIDO' THEN 97
        WHEN 'DESCONOCIDO' THEN 98
        ELSE 50
    END,
    c.nombre_canonico,
    CASE r.estado_lifecycle
        WHEN 'despachado' THEN 1
        WHEN 'armado' THEN 2
        WHEN 'ingresado' THEN 3
    END,
    r.numero;
```

---

## 2.4 Índices Recomendados (Resumen)

| Tabla | Índice | Tipo | Propósito |
|-------|--------|------|-----------|
| remitos | `idx_remitos_geom` | GiST | Queries espaciales (nearby, within) |
| remitos | `idx_remitos_ruta_candidates` | B-tree parcial | Filtro rápido de candidatos para ruta |
| remitos | `idx_remitos_domicilio_trgm` | GIN pg_trgm | Búsqueda fuzzy de direcciones |
| geo_cache | `idx_geo_geom` | GiST | Dedup por proximidad espacial |
| ruta_paradas | `idx_paradas_geom` | GiST | Visualización de ruta en mapa |
| distance_matrix_cache | `idx_dm_cache_origin/dest` | GiST | Lookup de pares origen-destino |
| audit_log | `idx_audit_fecha` | B-tree | Consultas por rango de fecha |
| historico_entregados | `idx_hist_geom` | GiST | Análisis geográfico de entregas |

---

## 2.5 Migraciones (Alembic)

La estructura de migraciones Alembic:

```
backend/
  alembic/
    versions/
      001_initial_schema.py      -- Todas las tablas base
      002_seed_carriers.py       -- Datos iniciales de carriers
      003_seed_config.py         -- Configuración por defecto
    env.py
  alembic.ini
```

**Comando de migración:**
```bash
alembic upgrade head
```

---

*Documento 02 de 05 — Serie Migración MolyMarket*
