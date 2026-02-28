# 01 — Sistema Actual: Análisis Completo

**Proyecto:** MolyMarket — Sistema de distribución de alimentos  
**Ubicación:** Mendoza, Argentina  
**Stack actual:** Google Sheets + Google Apps Script (V8) + Python (auxiliar)

---

## 1.1 Arquitectura General

```
┌──────────────────┐     HTTP POST/GET      ┌────────────────────────┐
│   Python Scripts  │ ──────────────────────►│  Apps Script WebApp    │
│   (auxiliares)    │                        │  doGet() / doPost()    │
└──────────────────┘                        └───────────┬────────────┘
                                                        │
┌──────────────────┐     onEdit / onChange    ┌──────────▼────────────┐
│  Usuario (manual) │ ─────────────────────►│  Google Sheets (12+)   │
│  Escaneo QR       │                        │  Base de datos         │
└──────────────────┘                        └───────────┬────────────┘
                                                        │
                                            ┌───────────▼────────────┐
                                            │  APIs Externas         │
                                            │  • Google Maps         │
                                            │  • OpenRouteService    │
                                            │  • Mapbox              │
                                            │  • OpenAI (gpt-4o-mini)│
                                            └────────────────────────┘
```

**Codebase:**
- `code.js` — ~16,945 líneas, monolítico, contiene toda la lógica de negocio
- `funciones_auxiliares.js` — ~1,587 líneas, helpers, triggers, pipeline de procesamiento
- `dev_keys.js` — API keys para desarrollo
- 6 scripts Python — testing y verificación (NO procesan datos)

---

## 1.2 Hojas de Google Sheets (Base de Datos)

### FRACCIONADOS (Hoja de entrada)
| Col | Campo | Tipo | Descripción |
|-----|-------|------|-------------|
| A | Fecha | Date | Fecha de ingreso (automática) |
| B | Remito | Text | **PRIMARY KEY** — Número de remito |
| C | Domicilio_normalizado | Text | Dirección procesada por IA/geocoding |
| D | Estado | Text | `Enviar`, `Corregir`, `Retiro sospechado`, `Transporte externo`, `No encontrado`, `Excluido` |
| E | Motivo | Text | Detalle del estado (razón) |
| F | Prioridad | Checkbox | Prioridad para la ruta |
| G | Obs planificación | Text | Observaciones para planificación de ruta |
| H | Urgente | Checkbox | Máxima prioridad (se procesa primero) |
| I+ | lat, lng, mapSearch | Number/Text | Coordenadas geocodificadas (columnas dinámicas por header) |

**Columnas dinámicas:** Se detectan por regex en el header (ej: `/^lat(itud)?$/i`, `/^lng$|^long(itud)?$/i`).

### Transportes (Backend plano — tabla central)
| Col | # | Campo | Tipo | Descripción |
|-----|---|-------|------|-------------|
| A | 1 | Remito | Text | **FK** a FRACCIONADOS.B |
| B | 2 | Cliente | Text | Nombre del cliente (de Pedidos Listos) |
| C | 3 | checkbox_title | Boolean | Checkbox en filas de título de grupo |
| D | 4 | Domicilio | Text | Dirección normalizada |
| E | 5 | Provincia | Text | Provincia del destino |
| F | 6 | Observaciones | Text | Observaciones de entrega (ventana horaria, etc.) |
| G | 7 | Transporte/Categoría | Text | Categoría asignada (carrier o tipo) |
| H | 8 | Tipo_fila | Text | `titulo` o vacío (data row) |
| I | 9 | seq_id | Text | ID secuencial para trazabilidad |
| J | 10 | Motivo_exclusion | Text | Razón de exclusión de ruta |
| K | 11 | Estado | Text | `INGRESADO`, `ARMADO`, `DESPACHADO` |
| L | 12 | Lat | Number | Latitud geocodificada |
| M | 13 | Lng | Number | Longitud geocodificada |
| N | 14 | Urgente | Boolean | Flag urgente |
| O | 15 | Prioridad | Boolean | Flag prioridad |
| P | 16 | Obs_entrega | Text | Observaciones de entrega formateadas |
| Q | 17 | TRANSP_JSON | Text | JSON serializado con datos completos |

**Estructura mixta:** Contiene filas de datos Y filas de cabecera de grupo (carrier), identificadas por `col H = "titulo"`.

### REPORTE_Transportes (Vista operativa — SOLO LECTURA derivada)
| Col | # | Campo | Tipo | Descripción |
|-----|---|-------|------|-------------|
| A | 1 | Remito | Text | De Transportes.A |
| B | 2 | Cliente | Text | De Transportes.B |
| C | 3 | ¿Armado? | Checkbox | De Transportes.K (Estado=ARMADO) |
| D | 4 | ¿Entregado? | Checkbox | Manual, siempre inicia en FALSE |
| E | 5 | Domicilio | Text | De Transportes.D |
| F | 6 | Observaciones | Text | De Transportes.J (Motivo) |

**Regenerada** completamente por `generarVistaCliente_()`. No se edita directamente excepto checkboxes C y D.

### Hoja 1 (Intermedia — candidatos para ruta)
| Col | # | Campo | Tipo | Descripción |
|-----|---|-------|------|-------------|
| A | 1 | Remito | Text | Número de remito |
| B | 2 | Dirección | Text | Dirección normalizada |
| C | 3 | Lat | Number | Latitud |
| D | 4 | Lng | Number | Longitud |
| E | 5 | Tiempo | Number | Tiempo estimado (min) — de Distance Matrix |
| F | 6 | Distancia | Number | Distancia estimada (km) |
| G | 7 | Observaciones | Text | Obs de entrega formateadas |
| H | 8 | Tiempo_parada | Number | Minutos de parada individual |

### Ruta (Salida — ruta optimizada final)
| Col | # | Campo | Tipo | Descripción |
|-----|---|-------|------|-------------|
| A | 1 | Orden | Number | Posición en la ruta (1, 2, 3...) |
| B | 2 | Cliente | Text | Nombre del cliente |
| C | 3 | Dirección | Text | Dirección de entrega |
| D | 4 | Min_anterior | Number | Minutos desde el punto anterior |
| E | 5 | Espera | Number | Tiempo de espera/parada (min) |
| F | 6 | Min_acumulados | Number | Minutos acumulados desde el inicio |
| G | 7 | Observaciones | Text | Obs de entrega |
| H | 8 | Links Google Maps | Text | URL de navegación fragmentada |

### Ruta_excluidos (Puntos excluidos de la ruta)
| Col | # | Campo | Tipo | Descripción |
|-----|---|-------|------|-------------|
| A | 1 | Remito | Text | Número de remito |
| B | 2 | Cliente | Text | Nombre del cliente |
| C | 3 | Dirección | Text | Dirección |
| D | 4 | Lat | Number | Latitud |
| E | 5 | Lng | Number | Longitud |
| F | 6 | Motivo | Text | Razón de exclusión |
| G | 7 | Observaciones | Text | Obs de entrega |
| H | 8 | Distancia_km | Number | Distancia al depósito |

### CONFIG_RUTA (Configuración)
| Fila | Parámetro | Default | Descripción |
|------|-----------|---------|-------------|
| 2 | Tiempo_espera_min | 10 | Minutos por parada |
| 3 | Usar_deposito | SI | Usar depósito como origen/destino |
| 4 | Direccion_deposito | Elpidio González 2753... | Dirección del depósito |
| 5 | Hora_desde | 09:00 | Inicio de ventana operativa |
| 6 | Hora_hasta | 14:00 | Fin de ventana operativa |
| 7 | Evitar_saltos_min | 25 | Umbral de salto (minutos) |
| 8 | Vuelta_al_galpon_min | 25 | Máximo tiempo de regreso |
| 9 | Proveedor_matrix | google | Proveedor de Distance Matrix |
| 10 | Utilizar Ventana | YES | Activar filtro por ventana horaria |

### CACHE_GEO (Cache persistente de geocodificación)
| Col | Campo | Tipo | Descripción |
|-----|-------|------|-------------|
| A | key | Text | Hash normalizado de la dirección |
| B | q_original | Text | Dirección original consultada |
| C | formatted | Text | Dirección formateada por el geocoder |
| D | lat | Number | Latitud |
| E | lng | Number | Longitud |
| F | hasStreetNumber | Boolean | Si tiene número de calle |
| G | ts | Number | Timestamp de la entrada |

### HISTÓRICO_ENTREGADOS (Archivo de entregas)
Misma estructura que Transportes (17 columnas A-Q), más filas separadoras con fecha `--- YYYY-MM-DD ---`.

### LOG_FRACC (Log de auditoría)
| Col | Campo | Tipo |
|-----|-------|------|
| A | Fecha | Timestamp ISO |
| B | Etapa | Text (tag) |
| C | Remito | Text |
| D | Detalle | Text (JSON) |

### BILLING_TRACE (Costos de API)
| Col | Campo | Tipo |
|-----|-------|------|
| A | timestamp | Timestamp |
| B | run_id | Text |
| C | stage | Text |
| D | service | Text |
| E | sku | Text |
| F | units | Number |
| G | response_code | Number |
| H | latency_ms | Number |
| I | url_length | Number |
| J-N | Reservados | — |

### Pedidos Listos (Spreadsheet externo)
| Campo requerido | Descripción |
|-----------------|-------------|
| Remito / Nro Remito / N° Remito | Número de remito (**PRIMARY KEY**) |
| Cliente / Nombre | Nombre del cliente |
| Domicilio / Dirección / Direccion | Dirección de entrega |
| Localidad / Ciudad | Localidad |
| Provincia | Provincia |
| Observaciones / Obs / Notas | Observaciones de entrega |
| Transporte | Transportista asignado |
| Fecha Remito / Fecha | Fecha del remito |

Se accede vía `SpreadsheetApp.openById(PEDIDOS_LISTOS_SPREADSHEET_ID)`.

---

## 1.3 Flujo Completo: Remito → Entrega

### Fase 1: Ingreso del Remito

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│ 1. Python POST  │     │ 2. Pegado manual │     │ 3. Sync PL (OFF)  │
│ doPost() →      │     │ onEdit col B →   │     │ syncPedidosListos_│
│ recibirRemitos  │     │ processRowByIdx  │     │ (DESACTIVADO v3)  │
│ Fraccionados_() │     │                  │     │                   │
└────────┬────────┘     └────────┬─────────┘     └───────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRACCIONADOS (col B)                      │
│  Triple deduplicación: Transportes + HISTÓRICO + FRACCIONADOS│
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  processRowByIndex(sh, row)                  │
│  Pipeline de 7 pasos ejecutado por cada remito nuevo         │
└─────────────────────────────────────────────────────────────┘
```

### Fase 2: Pipeline de Procesamiento (`processRowByIndex`)

```
PASO 0 — Leer fila base (B=remito, C=domicilio, F=prioridad)
    │
PASO 0.5 — preprocessRemitoIngress_() → AI canonización + geocoding temprano
    │
PASO 0.7 — lookupPedidosListos_() → buscar en PL externo
    │         → syncToTransportes_() → crear/actualizar fila en Transportes
    │
PASO 1 — ¿Es RETIRO? (regex RE_PICKUP → AI pickupDetection_)
    │         → SÍ: estado = "Retiro sospechado", RETURN
    │
PASO 2 — ¿Es TRANSPORTE EXTERNO? (regex → AI)
    │         → SÍ: estado = "Transporte externo", RETURN
    │
PASO 3 — Validación de dirección
    │   3a. ¿Localidad genérica? → "Corregir", RETURN
    │   3b. ¿Falta localidad en Mendoza? → "Corregir", RETURN
    │
PASO 4 — Normalización AI + completado de dirección
    │   4.1 ¿Formato "calle, localidad, MENDOZA"? → si no, "Corregir"
    │   4.2 ¿Calle coincide con geocoded? → si no, "Corregir"
    │
PASO 5 — Geocodificación (4 capas de cache → API cascade)
    │         → Sin número de calle? → "Corregir", RETURN
    │
PASO 6 — Observaciones de entrega (parseo de ventana horaria)
    │
PASO 7 — Estado final = "Enviar" ✅
```

### Fase 3: Armado (QR o Manual)

```
┌──────────────────┐         ┌──────────────────┐
│ Escaneo QR       │         │ Manual: checkbox  │
│ GET/POST WebApp  │         │ REPORTE col C     │
│ ?remito=X&token=Y│         │ onEdit handler    │
└────────┬─────────┘         └────────┬──────────┘
         │                            │
         ▼                            ▼
┌─────────────────────────────────────────────────┐
│  Transportes col K: INGRESADO → ARMADO          │
│  (Idempotente: re-escaneo = "Ya estaba ARMADO") │
│  (DESPACHADO no retrocede)                      │
└─────────────────────────────────────────────────┘
```

### Fase 4: Generación de Ruta

```
generarRutaDesdeFraccionados_() — Orquestador principal
    │
    ├─ TAREA 1: exportarAHoja1_()
    │    └─ Lee FRACCIONADOS, filtra Estado=ARMADO en Transportes
    │    └─ Resuelve coordenadas (CACHE_GEO → Transportes precalc → API)
    │    └─ Escribe en "Hoja 1" (candidatos)
    │
    ├─ TAREA 1.2: filtrarPorVentanaHoraria_()
    │    └─ Parsea observaciones → extrae rangos horarios
    │    └─ Intersecta con ventana CONFIG_RUTA (Hora_desde, Hora_hasta)
    │    └─ Excluye los que no caen en la ventana
    │    └─ URGENTE siempre pasa
    │
    ├─ TAREA 1.5: filtrarSaltosYVuelta_()
    │    └─ SUB 1: Vuelta al galpón (Haversine depot→punto, excluir si > umbral)
    │    └─ SUB 2: Duración total estimada (Haversine, 40km/h, poda por anillos)
    │    └─ SUB 3: Saltos iterativos (Haversine pre-filtro → DM API verificación)
    │    └─ URGENTE/PRIORIDAD nunca se excluyen de vuelta/duración
    │
    ├─ TAREA 2: geocodificarHoja1_()
    │    └─ Cache → pre-calc → API cascade (ORS → Mapbox → Google)
    │    └─ Validación: Mendoza bbox, calle, localidad
    │
    ├─ TAREA 3: calcularMatrizNxN_() + tspNearestNeighbor_()
    │    └─ Distance Matrix API en bloques de 10×10
    │    └─ TSP Nearest Neighbor como pre-orden
    │
    ├─ TAREA 4: generarRutaConDatos_() — OPTIMIZADOR PRINCIPAL
    │    └─ Clasificar: URGENTE / PRIORIDAD_AM / PRIORIDAD_PM / NORMAL_AM / NORMAL_PM
    │    └─ Sweep algorithm (ángulo polar desde depósito)
    │    └─ 2-opt solo para URGENTES
    │    └─ Orden final: URG → AM_PRI → AM_NORM → PM_PRI → PM_NORM
    │    └─ fixpointFilterJumps_() post-optimización
    │    └─ Google Maps links (fragmentados, max 10 waypoints)
    │    └─ Escribir en hojas "Ruta" y "Ruta_excluidos"
    │
    └─ POST: Logging, billing summary
```

### Fase 5: Entrega y Cierre

```
┌──────────────────────────────┐
│ 1. Marcar ENTREGADO          │
│    REPORTE col D (checkbox)  │
│    Requiere ARMADO en col C  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 2. Menú "Procesar Entregados"│
│    procesarEntregadosDesdeMenu()│
│    Valida ARMADO para cada uno│
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 3. Mover a HISTÓRICO         │
│    17 columnas + TRANSP_JSON │
│    Eliminar de Transportes   │
│    Eliminar de REPORTE       │
│    Compactar filas vacías     │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 4. Cierre mensual automático │
│    Exportar XLSX a Drive     │
│    Limpiar HISTÓRICO          │
│    Trigger: día 31 a 23:00   │
└──────────────────────────────┘
```

---

## 1.4 Lógica de Clasificación de Transporte

### Cascade de decisión (en orden de prioridad)

| # | Fuente | Test | Resultado |
|---|--------|------|-----------|
| 1 | Regex: `RE_PICKUP` | RETIRA/RETIRO en observaciones | `RETIRO EN COMERCIAL` |
| 2 | Regex: `detectarTransporteRegex_()` | 16 patrones prioritarios | Carrier detectado (VIA CARGO, ANDREANI, etc.) |
| 3 | AI: `classifyTransportAI_()` | GPT-4o-mini con confirmación regex | Carrier + confianza |
| 4 | Regla: `determinarCategoriaFinal_()` | Carrier conocido | Usar carrier |
| 5 | Regla: texto contiene RETIRA/RETIRO | Sin carrier | `RETIRO EN COMERCIAL` |
| 6 | Regla: provincia ≠ Mendoza | Sin carrier | `DESCONOCIDO` |
| 7 | Regla: provincia = Mendoza, sin carrier | Default local | `ENVÍO PROPIO (MOLLY MARKET)` |
| 8 | Fallback | Todo lo demás | `DESCONOCIDO` |

### Carriers conocidos (14+)

| Carrier | Variantes regex |
|---------|----------------|
| VIA CARGO | `VIA\s*CARGO`, `VIACARGO` |
| ANDREANI | `ANDREANI`, `TRANSPORTE ANDREANI` |
| ANDESMAR | `ANDESMAR` |
| BUS PACK | `BUS\s*PACK` |
| OCASA | `OCASA` |
| OCA | `\bOCA\b` (word boundary para no matchear "OCASA") |
| URBANO | `URBANO` |
| CRUZ DEL SUR | `CRUZ\s*DEL\s*SUR` |
| VIA BARILOCHE | `VIA\s*BARILOCHE` |
| ACORDIS | `ACORDIS` |
| VELOX | `VELOX` |
| TRANSPORTE VESRPINI | `VE?S[PR]+INI` (múltiples variantes ortográficas) |
| EXPRESO \<X\> | `EXPRESO\s+([A-ZÁÉÍÓÚÑ]+)` (genérico con sufijo) |
| TRANSPORTE \<X\> | `TRANSPORTE\s+([A-ZÁÉÍÓÚÑ]+)` (genérico con sufijo) |

### Normalización de nombres de carrier

Mapa de aliases → nombre canónico. Ejemplo:
- `VIACARGO`, `VIA  CARGO`, `VIA CARGO` → `VIA CARGO`
- `ENVIO PROPIO`, `MOLLY MARKET`, `TRANSPORTE MOLLY MARKET`, `MOLLY` → `ENVÍO PROPIO (MOLLY MARKET)`
- `RETIRA`, `RETIRO`, `RETIRA EN COMERCIAL`, etc. → `RETIRO EN COMERCIAL`

---

## 1.5 Sistema de Geocodificación

### Cache de 4 capas

```
Consulta
  │
  ├─ 1. Memoria (var _geoMemo = {})     → TTL: sesión (6 min max)
  │
  ├─ 2. CacheService                     → TTL: 21,600s (6h)
  │      key: "GEO_" + normalizedKey
  │
  ├─ 3. ScriptProperties                 → TTL: permanente
  │      key: "GEO_PROP_" + normalizedKey
  │
  └─ 4. Hoja CACHE_GEO                   → TTL: permanente
         Dedup por key + proximidad (<0.0001° ≈ 10m)
```

Cada capa se valida con `validateCachedGeo_()` antes de aceptar:
- Coordenadas dentro de Mendoza bbox
- No es un centro genérico conocido (5 ciudades)
- Localidad coincide con la consulta
- No es texto genérico (sin calle específica)

### Cascade de proveedores (API)

| Orden | Proveedor | Endpoint | Rate limit |
|-------|-----------|----------|------------|
| 1 | ORS | `api.openrouteservice.org/geocode/search` | Configurable |
| 2 | Mapbox | `api.mapbox.com/geocoding/v5/mapbox.places/` | Configurable |
| 3 | Google | `maps.googleapis.com/maps/api/geocode/json` | Billing |

Todos biased a Mendoza bbox: lat -33.5 a -32.0, lng -69.5 a -68.0.

### Validación de resultado geocodificado

`validateGeoResult_()`:
1. Coordenadas no nulas y no (0,0)
2. Dentro de Mendoza bounds ampliados
3. No es nombre genérico de localidad
4. Localidad del resultado coincide con la consulta
5. No es coordenada de centro conocido (±0.001° ≈ 100m de tolerancia)

### Normalización de direcciones

`normalizarDireccion_()`:
1. NFD decomposition → strip diacríticos
2. Lowercase
3. Expandir abreviaturas: av→avenida, dpto→departamento, bv→boulevard, cjal→concejal, etc.
4. Colapsar espacios múltiples

---

## 1.6 Algoritmo de Ruta Óptima

### Sweep + 2-opt (algoritmo principal)

**Sweep:** Ordena los puntos por ángulo polar desde el depósito.

$$\theta_i = \text{atan2}(\text{lat}_i - \text{lat}_{dep},\ \text{lng}_i - \text{lng}_{dep})$$

Orden: ascendente por $\theta$ (counter-clockwise desde el eje este).

**2-opt:** Mejora local por intercambio de aristas. Solo para URGENTES.

$$\Delta = [d(A,C) + d(B,D)] - [d(A,B) + d(C,D)]$$

Si $\Delta < -10^{-6}$ → invertir segmento $[i..k]$. Iterar hasta convergencia.

**Nearest Neighbor (TSP):** Heurístico greedy — seleccionar siempre el punto no visitado más cercano.

### Pipeline de optimización

1. Clasificar puntos: URGENTE / PRIORIDAD / NORMAL × AM / PM
2. Urgentes: Sweep + 2-opt completo
3. Prioridad AM/PM: Sweep only
4. Normales AM/PM: Sweep only
5. Concatenar: URG → AM_PRI → AM_NORM → PM_PRI → PM_NORM
6. `fixpointFilterJumps_()`: post-optimización iterativa de saltos
7. Generar links Google Maps (max 10 waypoints por link)

### Filtros de exclusión

| Filtro | Método | Umbral | Bypass |
|--------|--------|--------|--------|
| Ventana horaria | Intersección de rangos | CONFIG_RUTA.Hora_desde/hasta | URGENTE |
| Vuelta al galpón | Haversine depot→punto | CONFIG_RUTA.Vuelta_al_galpon_min | URGENTE, PRIORIDAD |
| Duración total | Haversine 40km/h | CONFIG_RUTA total estimado | URGENTE, PRIORIDAD |
| Saltos | Haversine pre + DM API | CONFIG_RUTA.Evitar_saltos_min × 1.5 | URGENTE, PRIORIDAD |
| Distancia máxima | Haversine | 45 km del depósito | Ninguno |

### Depósito (hardcoded + configurable)

- **Default:** lat -32.91973, lng -68.81829 (Elpidio González 2753, Guaymallén)
- **Override:** CONFIG_RUTA → Direccion_deposito (geocodificado)

---

## 1.7 Sistema de Ventana Horaria

### Ventanas duras

| ID | Desde | Hasta | Orden |
|----|-------|-------|-------|
| AM | 09:00 | 13:00 | 1 |
| PM | 14:00 | 18:00 | 2 |
| SIN_HORARIO | — | — | 99 |

### Parseo de observaciones → ventana

Cascade de interpretación (`interpretarObservacionUnificado_()`):
1. Regex RETIRA/RETIRO → tipo PICKUP
2. Keyword carrier → tipo CARRIER
3. Formato explícito HH:MM-HH:MM → tipo VENTANA
4. "DESDE LAS HH:MM" → tipo VENTANA (desde hasta fin del día)
5. "HASTA LAS HH:MM" → tipo VENTANA (desde 00:00 hasta hora)
6. Palabras vagas: MAÑANA→08-13, TARDE→16-21, HORARIO COMERCIAL→09-18
7. OpenAI fallback → tipo VENTANA

### Asignación AM/PM

```
Si todos los rangos del remito caen en AM → AM
Si todos caen en PM → PM
Si hay overlap → usar el primer rango que intersecta con la ventana config
Si no hay ventana → SIN_HORARIO (se incluye en ambas)
```

---

## 1.8 APIs Externas

| API | Uso | Costo estimado |
|-----|-----|----------------|
| Google Maps Geocoding | Geocodificación de direcciones (último recurso) | ~$5/1000 requests |
| Google Maps Distance Matrix | Matriz NxN de tiempos/distancias | ~$5/1000 elements |
| OpenRouteService (ORS) | Geocodificación + Distance Matrix (primario) | Freemium |
| Mapbox | Geocodificación + Distance Matrix (secundario) | Freemium |
| OpenAI (gpt-4o-mini) | Clasificación de transporte, normalización de direcciones, parseo de ventanas horarias, resolución de POIs | ~$0.15/1M tokens |

### Keys almacenadas en ScriptProperties

| Key | Servicio |
|-----|----------|
| `GOOGLE_MAPS_API_KEY` | Google Maps |
| `OPENAI_API_KEY` | OpenAI |
| `ORS_API_KEY` | OpenRouteService |
| `MAPBOX_TOKEN` | Mapbox |
| `PEDIDOS_LISTOS_SPREADSHEET_ID` | ID del spreadsheet externo |
| `QR_TOKEN` | Token para autenticación QR |

---

## 1.9 Triggers y Automatizaciones

| Trigger | Tipo | Función | Estado |
|---------|------|---------|--------|
| `onEdit` | Simple | Router de eventos de edición | ✅ Activo |
| `onChangeInstallable` | Instalable (onChange) | Rescán de FRACCIONADOS pendientes | ✅ Activo |
| `cierreMensualAutomatico` | Instalable (time, día 31 23:00) | Export mensual XLSX | ✅ Activo |
| `processPendientes_` | Era minutely | Rescán idéntico a onChange | ⛔ Desactivado v3 |
| `syncPedidosListos_` | Era minutely | Sync desde PL externo | ⛔ Desactivado v3 |
| `runHistoricoEntregados_` | Era time-based | Procesamiento de entregas | ⛔ Reemplazado por menú |

---

## 1.10 WebApp API (doGet / doPost)

### GET — Escaneo QR

```
GET /exec?remito={remito}&token={token}

Response (JSON):
{
  "ok": true|false,
  "remito": "123456",
  "message": "Marcado como ARMADO (antes: INGRESADO)",
  "CODE_VERSION": "v3.1-26feb2026-1300"
}
```

**Batch:** `?remito=R1,R2,R3` (hasta 50, separados por coma)

### POST — Ingesta de remitos

```
POST /exec
Content-Type: application/json

{
  "action": "ingest_remitos",
  "token": "TOKEN",
  "remitos": ["R1", "R2", "R3"]
}

Response:
{
  "ok": true,
  "message": "Ingesta completada",
  "total": 3,
  "nuevos": 2,
  "duplicados": 1,
  "CODE_VERSION": "v3.1-26feb2026-1300"
}
```

### POST — QR (sin action)

```
POST /exec
{
  "remito": "123456",
  "token": "TOKEN"
}
→ Mismo comportamiento que GET QR
```

---

## 1.11 Máquina de Estados del Remito

```
                    ┌─────────────┐
        Ingreso ──► │  INGRESADO  │
                    └──────┬──────┘
                           │
               QR scan ó   │
               checkbox C  │
                           ▼
                    ┌─────────────┐
                    │   ARMADO    │
                    └──────┬──────┘
                           │
               checkbox D  │ (requiere ARMADO)
               + Menú      │
                           ▼
                    ┌─────────────┐
                    │  ENTREGADO  │ (transitorio, col D de REPORTE)
                    └──────┬──────┘
                           │
               Menú        │
               "Procesar"  │
                           ▼
                    ┌─────────────┐
                    │  HISTÓRICO  │ (archivo permanente)
                    └─────────────┘
```

Estados en FRACCIONADOS col D:
- `Enviar` — Listo para incluir en ruta
- `Corregir` — Dirección necesita corrección manual
- `Retiro sospechado` — Posible pickup, pendiente confirmación
- `Transporte externo` — Asignado a carrier externo
- `No encontrado` — Error en procesamiento
- `Excluido` — Excluido manualmente

Estados en Transportes col K:
- `INGRESADO` — Recién ingresado
- `ARMADO` — Paquete preparado
- `DESPACHADO` — En camino (no se usa actualmente en el flujo visible)

---

*Documento 01 de 05 — Serie Migración MolyMarket*
