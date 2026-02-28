# 04 — Arquitectura Frontend (Next.js)

**Stack:** Next.js 15 (App Router) + TypeScript + Tailwind CSS + Leaflet  
**Deploy:** Vercel  
**Auth:** JWT almacenado en httpOnly cookie

---

## 4.1 Estructura de Carpetas del Frontend

```
frontend/
├── public/
│   ├── icons/
│   │   ├── marker-default.svg
│   │   ├── marker-urgente.svg
│   │   ├── marker-prioridad.svg
│   │   ├── marker-depot.svg
│   │   └── marker-entregado.svg
│   └── favicon.ico
│
├── src/
│   ├── app/                              # App Router (páginas)
│   │   ├── layout.tsx                    # Layout raíz (sidebar, auth provider)
│   │   ├── page.tsx                      # Redirect → /dashboard
│   │   ├── login/
│   │   │   └── page.tsx                  # Página de login
│   │   ├── dashboard/
│   │   │   └── page.tsx                  # Dashboard con métricas
│   │   ├── remitos/
│   │   │   ├── page.tsx                  # Lista de remitos
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx             # Detalle de remito
│   │   │   └── ingest/
│   │   │       └── page.tsx             # Ingesta de remitos
│   │   ├── rutas/
│   │   │   ├── page.tsx                  # Lista de rutas
│   │   │   ├── generar/
│   │   │   │   └── page.tsx             # Generar nueva ruta
│   │   │   └── [id]/
│   │   │       └── page.tsx             # Detalle de ruta + mapa
│   │   ├── reporte/
│   │   │   └── page.tsx                  # REPORTE_Transportes (vista operativa)
│   │   ├── historico/
│   │   │   └── page.tsx                  # Histórico de entregas
│   │   ├── carriers/
│   │   │   └── page.tsx                  # Gestión de carriers
│   │   ├── config/
│   │   │   └── page.tsx                  # Configuración del sistema
│   │   ├── billing/
│   │   │   └── page.tsx                  # Costos de API
│   │   └── qr/
│   │       └── page.tsx                  # Escáner QR (mobile-friendly)
│   │
│   ├── components/                        # Componentes reutilizables
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx               # Sidebar de navegación
│   │   │   ├── Header.tsx                # Header con usuario y notificaciones
│   │   │   └── PageContainer.tsx         # Wrapper de página
│   │   │
│   │   ├── remitos/
│   │   │   ├── RemitosTable.tsx          # Tabla de remitos con filtros
│   │   │   ├── RemitoDetail.tsx          # Detalle de un remito
│   │   │   ├── RemitoStatusBadge.tsx     # Badge de estado con color
│   │   │   ├── IngestForm.tsx            # Formulario de ingesta batch
│   │   │   ├── AddressCorrection.tsx     # Corrección de dirección inline
│   │   │   └── RemitoTimeline.tsx        # Timeline del ciclo de vida
│   │   │
│   │   ├── rutas/
│   │   │   ├── RouteMap.tsx              # Mapa Leaflet con la ruta
│   │   │   ├── RouteStopsList.tsx        # Lista de paradas ordenadas
│   │   │   ├── RouteStopCard.tsx         # Card de una parada
│   │   │   ├── RouteExcludedList.tsx     # Lista de excluidos con motivo
│   │   │   ├── RouteConfigForm.tsx       # Formulario de configuración de ruta
│   │   │   ├── RouteStats.tsx            # Estadísticas de la ruta
│   │   │   └── GMapsLinks.tsx            # Links a Google Maps (fragmentados)
│   │   │
│   │   ├── reporte/
│   │   │   ├── ReporteTable.tsx          # Tabla operativa (ARMADO/ENTREGADO)
│   │   │   ├── ArmadoCheckbox.tsx        # Checkbox ARMADO con validación
│   │   │   └── EntregadoCheckbox.tsx     # Checkbox ENTREGADO con validación
│   │   │
│   │   ├── map/
│   │   │   ├── MapContainer.tsx          # Wrapper de Leaflet (dynamic import)
│   │   │   ├── RouteLayer.tsx            # LineString de la ruta
│   │   │   ├── StopMarker.tsx            # Marcador de parada con popup
│   │   │   ├── DepotMarker.tsx           # Marcador del depósito
│   │   │   └── HeatmapLayer.tsx          # Heatmap de entregas históricas
│   │   │
│   │   ├── dashboard/
│   │   │   ├── StatsCards.tsx            # Cards de métricas principales
│   │   │   ├── DeliveryChart.tsx         # Gráfico de entregas por día
│   │   │   ├── CarrierDistribution.tsx   # Pie chart de carriers
│   │   │   └── PendingAlerts.tsx         # Alertas de remitos pendientes
│   │   │
│   │   ├── qr/
│   │   │   ├── QRScanner.tsx            # Scanner de QR con cámara
│   │   │   ├── QRManualInput.tsx        # Input manual de remito
│   │   │   └── QRResult.tsx             # Resultado del escaneo
│   │   │
│   │   └── ui/                           # Componentes genéricos
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Select.tsx
│   │       ├── Checkbox.tsx
│   │       ├── Badge.tsx
│   │       ├── Modal.tsx
│   │       ├── Toast.tsx
│   │       ├── DataTable.tsx             # Tabla genérica con sort/filter/pagination
│   │       ├── LoadingSpinner.tsx
│   │       ├── EmptyState.tsx
│   │       └── ConfirmDialog.tsx
│   │
│   ├── hooks/                             # Custom hooks
│   │   ├── useAuth.ts                    # Auth context y helpers
│   │   ├── useRemitos.ts                 # CRUD remitos
│   │   ├── useRutas.ts                   # CRUD rutas
│   │   ├── useReporte.ts                 # Reporte transportes
│   │   ├── useConfig.ts                  # Configuración
│   │   ├── useDashboard.ts              # Métricas
│   │   └── useQR.ts                      # Escaneo QR
│   │
│   ├── lib/                               # Utilidades
│   │   ├── api.ts                        # Cliente HTTP (fetch wrapper)
│   │   ├── auth.ts                       # JWT helpers
│   │   ├── constants.ts                  # Constantes del frontend
│   │   ├── formatters.ts                 # Formateo de datos
│   │   ├── map-utils.ts                  # Utilidades de Leaflet
│   │   └── types.ts                      # TypeScript types/interfaces
│   │
│   ├── context/
│   │   └── AuthContext.tsx               # Context provider de autenticación
│   │
│   └── middleware.ts                      # Middleware Next.js (auth redirect)
│
├── tailwind.config.ts
├── next.config.ts
├── tsconfig.json
├── package.json
├── .env.local.example
└── README.md
```

---

## 4.2 Páginas y su Propósito

### `/login` — Autenticación

- Formulario email + contraseña
- Redirige a `/dashboard` al loguearse
- Almacena JWT en httpOnly cookie

### `/dashboard` — Panel principal

```
┌──────────────────────────────────────────────────────────┐
│  📊 Dashboard                                            │
├──────────┬──────────┬──────────┬────────────────────────┤
│ Remitos  │ Armados  │ Rutas    │ Entregas               │
│ Hoy: 45  │ 32       │ Activa: 1│ Hoy: 28                │
├──────────┴──────────┴──────────┴────────────────────────┤
│                                                          │
│  ┌─────────────────────────┐  ┌─────────────────────────┐│
│  │  Entregas por día (7d)  │  │  Distribución carriers  ││
│  │  ▄▅█▇▄▅▆               │  │  🟢 Envío Propio: 60%   ││
│  │                         │  │  🔵 VIA CARGO: 15%      ││
│  │                         │  │  🟡 Retiro: 10%         ││
│  └─────────────────────────┘  │  🟠 Otros: 15%          ││
│                               └─────────────────────────┘│
│  ⚠️ Alertas                                              │
│  • 3 remitos pendientes de geocodificación               │
│  • 5 remitos con estado "Corregir"                       │
│  • Costo API hoy: USD 1.23                               │
└──────────────────────────────────────────────────────────┘
```

### `/remitos` — Gestión de remitos

```
┌──────────────────────────────────────────────────────────┐
│  📦 Remitos                          [+ Ingestar batch]  │
├──────────────────────────────────────────────────────────┤
│  Filtros: [Estado ▼] [Lifecycle ▼] [Carrier ▼] [🔍 ]    │
├──────────────────────────────────────────────────────────┤
│  # │ Remito   │ Cliente      │ Estado   │ Lifecycle │ ⚡ │
│  1 │ 123456   │ Juan Pérez   │ ✅ Enviar│ ARMADO    │ 🔴 │
│  2 │ 123457   │ María López  │ 🔧 Corr  │ INGRESADO │    │
│  3 │ 123458   │ Carlos Ruiz  │ 🚛 Ext   │ INGRESADO │    │
│  ...                                                     │
│  Mostrando 1-20 de 145  [< 1 2 3 4 ... 8 >]            │
└──────────────────────────────────────────────────────────┘
```

- Click en fila → `/remitos/{id}` (detalle con mapa, timeline, edición)
- Botón "Ingestar batch" → `/remitos/ingest` (textarea para pegar lista de remitos)
- Filtros combinables por estado, lifecycle, carrier, urgente, prioridad
- Acciones masivas: marcar urgente/prioridad, reprocesar

### `/remitos/{id}` — Detalle de remito

```
┌──────────────────────────────────────────────────────────┐
│  📦 Remito #123456                                       │
├────────────────────────────┬─────────────────────────────┤
│  Cliente: Juan Pérez       │  ┌─────────────────────────┐│
│  Dirección: Av. San Martín │  │    🗺️ Mapa Leaflet      ││
│  1234, Godoy Cruz, Mendoza │  │    📍 Pin en la         ││
│                            │  │       ubicación          ││
│  Estado: ✅ Enviar          │  │                         ││
│  Lifecycle: 🔵 ARMADO      │  │                         ││
│  Carrier: Envío Propio     │  └─────────────────────────┘│
│  Ventana: AM (09:00-13:00) │                             │
│                            │  Timeline:                   │
│  ☐ Urgente  ☑ Prioridad    │  ● Ingresado  28/02 09:15  │
│                            │  ● Armado     28/02 10:30   │
│  [🔧 Corregir dirección]   │  ○ Entregado  —            │
│  [🔄 Reprocesar]           │  ○ Histórico  —            │
│  [🗑️ Eliminar]             │                             │
└────────────────────────────┴─────────────────────────────┘
```

### `/rutas/generar` — Generación de ruta

```
┌──────────────────────────────────────────────────────────┐
│  🗺️ Generar Ruta                                         │
├────────────────────────────┬─────────────────────────────┤
│  Configuración             │                             │
│  ┌─────────────────────┐   │  Candidatos (32 remitos):   │
│  │ Tiempo espera: [10] │   │  ✅ 25 incluidos            │
│  │ Hora desde:  [09:00]│   │  ❌ 7 excluidos             │
│  │ Hora hasta:  [14:00]│   │                             │
│  │ Saltos max:  [25]   │   │  🔴 Urgentes: 3            │
│  │ Vuelta max:  [25]   │   │  🟡 Prioridad: 5           │
│  │ Proveedor:   [ORS▼] │   │  🟢 Normales: 17           │
│  │ Ventana:     [✓]    │   │                             │
│  └─────────────────────┘   │  Costo API estimado: ~$0.45 │
│                            │                             │
│  [🚀 GENERAR RUTA]         │                             │
└────────────────────────────┴─────────────────────────────┘
```

### `/rutas/{id}` — Detalle de ruta + Mapa

```
┌──────────────────────────────────────────────────────────┐
│  🗺️ Ruta #12 — 28/02/2026                    [Estado: ▼]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │                                                      ││
│  │              🗺️ MAPA LEAFLET                         ││
│  │                                                      ││
│  │    🏠 Depósito                                       ││
│  │         ↓                                            ││
│  │    1️⃣ → 2️⃣ → 3️⃣ → ... → 25 → 🏠                   ││
│  │                                                      ││
│  │    Línea azul conectando puntos en orden              ││
│  │    Marcadores numerados con popup de info            ││
│  │                                                      ││
│  └──────────────────────────────────────────────────────┘│
│                                                          │
│  📊 Resumen: 25 paradas │ ~180 min │ ~45 km │ $0.42     │
│                                                          │
│  🔗 Google Maps: [Tramo 1] [Tramo 2] [Tramo 3]          │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  # │ Cliente      │ Dirección          │ Min │ Acum │ Obs│
│  1 │ 🔴 J. Pérez  │ Av. San Martín 123 │ —   │ 0    │ AM │
│  2 │ M. López     │ Belgrano 456       │ 8   │ 18   │    │
│  3 │ 🟡 C. Ruiz   │ Las Heras 789      │ 12  │ 40   │ PM │
│  ...                                                     │
├──────────────────────────────────────────────────────────┤
│  ❌ Excluidos (7)                                        │
│  │ R-789012 │ Salto: 45 min entre paradas               │
│  │ R-789013 │ Fuera de ventana horaria                   │
│  │ ...                                                   │
└──────────────────────────────────────────────────────────┘
```

### `/reporte` — Vista Operativa (reemplaza REPORTE_Transportes)

```
┌──────────────────────────────────────────────────────────┐
│  📋 Reporte de Transportes          [Procesar Entregados]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ── ENVÍO PROPIO (MOLLY MARKET) ──────────────────────── │
│  │ Remito   │ Cliente      │ ☐ Armado │ ☐ Entreg │ Dir  │
│  │ 123456   │ Juan Pérez   │ ☑        │ ☐        │ ...  │
│  │ 123457   │ María López  │ ☐        │ ☐        │ ...  │
│  │ 123458   │ Carlos Ruiz  │ ☑        │ ☑        │ ...  │
│                                                          │
│  ── RETIRO EN COMERCIAL ──────────────────────────────── │
│  │ 123460   │ Ana García   │ ☑        │ ☐        │ ...  │
│                                                          │
│  ── VIA CARGO ────────────────────────────────────────── │
│  │ 123461   │ Pedro Sánchez│ ☑        │ ☐        │ ...  │
│  ...                                                     │
└──────────────────────────────────────────────────────────┘
```

- Agrupado por carrier (mismo layout visual que REPORTE_Transportes actual)
- Checkboxes interactivos con validación en tiempo real
- ENTREGADO bloqueado si ARMADO no está tildado
- Botón "Procesar Entregados" → mueve a histórico los marcados

### `/historico` — Histórico de entregas

- Tabla con filtros por fecha, mes, carrier, búsqueda
- Botón "Exportar XLSX" por mes
- Botón "Restaurar" por remito individual
- Acción "Cierre mensual" (admin only)

### `/qr` — Escáner QR (Mobile-Optimized)

```
┌──────────────────────────┐
│     📱 Escanear QR       │
│                          │
│  ┌──────────────────────┐│
│  │                      ││
│  │    📷 Visor cámara   ││
│  │                      ││
│  │    (auto-detect QR)  ││
│  │                      ││
│  └──────────────────────┘│
│                          │
│  ─ó─ Ingreso manual ─── │
│  [_______________] [OK]  │
│                          │
│  Último escaneo:         │
│  ✅ 123456 → ARMADO      │
│  ✅ 123457 → ARMADO      │
│  ℹ️ 123458 → Ya ARMADO   │
└──────────────────────────┘
```

- Responsive, diseñado para celular
- Usa `html5-qrcode` o `@zxing/browser` para decodificar QR de la cámara
- Sonido/vibración de feedback al escanear
- Historial de escaneos de la sesión

### `/config` — Configuración

- Formulario CRUD para todos los parámetros de CONFIG_RUTA
- Validación en tiempo real
- Preview del impacto (ej: "Con estos parámetros, se incluirían ~25 de 32 remitos")

### `/billing` — Costos de API

- Tabla de trazas de billing con filtros
- Gráfico de costos por servicio y por día
- Resumen mensual

---

## 4.3 Mapa Leaflet — Implementación

### Dependencias

```json
{
  "leaflet": "^1.9.4",
  "react-leaflet": "^4.2.1",
  "@types/leaflet": "^1.9.8"
}
```

### `MapContainer.tsx` — Dynamic Import (SSR-safe)

```tsx
'use client';
import dynamic from 'next/dynamic';

// Leaflet no funciona con SSR — importar dinámicamente
const Map = dynamic(() => import('./MapInner'), { 
  ssr: false,
  loading: () => <div className="h-[500px] bg-gray-100 animate-pulse" />
});

export default function MapContainer(props: MapProps) {
  return <Map {...props} />;
}
```

### `MapInner.tsx` — Mapa con ruta

```tsx
'use client';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';

interface MapProps {
  depot: { lat: number; lng: number };
  stops: RouteStop[];          // Paradas ordenadas
  routeLine?: [number, number][];  // Polyline de la ruta
  zoom?: number;
}

export default function MapInner({ depot, stops, routeLine, zoom = 13 }: MapProps) {
  const center: [number, number] = [depot.lat, depot.lng];
  
  return (
    <MapContainer center={center} zoom={zoom} className="h-[500px] w-full rounded-lg">
      <TileLayer
        attribution='&copy; OpenStreetMap'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {/* Depósito */}
      <Marker position={[depot.lat, depot.lng]} icon={depotIcon}>
        <Popup>🏠 Depósito<br/>Elpidio González 2753</Popup>
      </Marker>
      
      {/* Paradas numeradas */}
      {stops.map((stop, i) => (
        <Marker 
          key={stop.id} 
          position={[stop.lat, stop.lng]}
          icon={createNumberedIcon(i + 1, stop.es_urgente, stop.es_prioridad)}
        >
          <Popup>
            <strong>#{i + 1} — {stop.cliente}</strong><br/>
            {stop.direccion}<br/>
            {stop.minutos_acumulados && `⏱ ${stop.minutos_acumulados} min acum.`}<br/>
            {stop.observaciones}
          </Popup>
        </Marker>
      ))}
      
      {/* Línea de ruta */}
      {routeLine && (
        <Polyline 
          positions={routeLine} 
          color="#3b82f6" 
          weight={3} 
          opacity={0.8}
        />
      )}
    </MapContainer>
  );
}

// Iconos numerados con color por prioridad
function createNumberedIcon(num: number, urgente: boolean, prioridad: boolean) {
  const color = urgente ? '#ef4444' : prioridad ? '#eab308' : '#3b82f6';
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background: ${color}; color: white; 
      border-radius: 50%; width: 28px; height: 28px;
      display: flex; align-items: center; justify-content: center;
      font-weight: bold; font-size: 12px; border: 2px solid white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    ">${num}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}
```

### GeoJSON desde la API

El endpoint `GET /api/v1/rutas/{id}/geojson` retorna:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-68.81829, -32.91973] },
      "properties": { "tipo": "deposito", "nombre": "Depósito" }
    },
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-68.85, -32.90] },
      "properties": { 
        "tipo": "parada", "orden": 1, "cliente": "Juan Pérez",
        "direccion": "Av. San Martín 1234", "urgente": true,
        "minutos_acumulados": 15
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[-68.81829, -32.91973], [-68.85, -32.90], ...]
      },
      "properties": { "tipo": "ruta", "distancia_km": 45, "duracion_min": 180 }
    }
  ]
}
```

---

## 4.4 Cliente HTTP (`lib/api.ts`)

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface ApiOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
}

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options;
  
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',  // httpOnly cookies
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new ApiError(res.status, error.detail);
  }
  
  return res.json();
}

// Helpers tipados
export const remitosApi = {
  list: (params?: URLSearchParams) => 
    api<PaginatedResponse<Remito>>(`/remitos?${params || ''}`),
  get: (id: number) => api<Remito>(`/remitos/${id}`),
  ingest: (remitos: string[]) => 
    api<IngestResponse>('/remitos/ingest', { method: 'POST', body: { remitos } }),
  update: (id: number, data: Partial<Remito>) => 
    api<Remito>(`/remitos/${id}`, { method: 'PUT', body: data }),
  reprocess: (id: number) => 
    api<Remito>(`/remitos/reprocess/${id}`, { method: 'POST' }),
};

export const rutasApi = {
  list: (params?: URLSearchParams) => 
    api<Ruta[]>(`/rutas?${params || ''}`),
  get: (id: number) => api<Ruta>(`/rutas/${id}`),
  generate: (config?: RouteConfig) => 
    api<Ruta>('/rutas/generar', { method: 'POST', body: config }),
  geojson: (id: number) => api<GeoJSON>(`/rutas/${id}/geojson`),
  gmapsLinks: (id: number) => api<{ links: string[] }>(`/rutas/${id}/gmaps-links`),
};

export const qrApi = {
  scan: (remito: string, token: string) => 
    api<QRResult>(`/qr/scan?remito=${remito}&token=${token}`),
  scanBatch: (remitos: string[], token: string) => 
    api<QRBatchResult>('/qr/scan-batch', { 
      method: 'POST', body: { remitos, token } 
    }),
};
```

---

## 4.5 TypeScript Types (`lib/types.ts`)

```typescript
// Estados
type EstadoClasificacion = 
  'pendiente' | 'enviar' | 'corregir' | 'retiro_sospechado' | 
  'transporte_externo' | 'no_encontrado' | 'excluido';

type EstadoLifecycle = 
  'ingresado' | 'armado' | 'despachado' | 'entregado' | 'historico';

type RutaEstado = 
  'generando' | 'generada' | 'en_curso' | 'completada' | 'cancelada';

type ParadaEstado = 
  'pendiente' | 'en_camino' | 'entregada' | 'fallida' | 'saltada';

// Entidades
interface Remito {
  id: number;
  numero: string;
  cliente?: string;
  domicilio_raw?: string;
  domicilio_normalizado?: string;
  localidad?: string;
  provincia?: string;
  observaciones_pl?: string;
  observaciones_entrega?: string;
  estado_clasificacion: EstadoClasificacion;
  motivo_clasificacion?: string;
  estado_lifecycle: EstadoLifecycle;
  carrier_nombre?: string;
  lat?: number;
  lng?: number;
  geocode_source?: string;
  ventana_tipo?: string;
  ventana_desde_min?: number;
  ventana_hasta_min?: number;
  urgente: boolean;
  prioridad: boolean;
  llamar_antes: boolean;
  fecha_ingreso: string;
  fecha_armado?: string;
  fecha_entregado?: string;
}

interface Ruta {
  id: number;
  fecha: string;
  estado: RutaEstado;
  total_paradas: number;
  total_excluidos: number;
  duracion_estimada_min?: number;
  distancia_total_km?: number;
  gmaps_links: string[];
  paradas: RutaParada[];
  excluidos: RutaExcluido[];
  config: RouteConfig;
  api_cost_estimate?: number;
  created_at: string;
}

interface RutaParada {
  id: number;
  orden: number;
  remito_numero: string;
  cliente: string;
  direccion: string;
  lat: number;
  lng: number;
  minutos_desde_anterior?: number;
  tiempo_espera_min?: number;
  minutos_acumulados?: number;
  observaciones?: string;
  es_urgente: boolean;
  es_prioridad: boolean;
  ventana_tipo?: string;
  estado: ParadaEstado;
}

interface RouteConfig {
  tiempo_espera_min: number;
  deposito_lat: number;
  deposito_lng: number;
  hora_desde: string;
  hora_hasta: string;
  evitar_saltos_min: number;
  vuelta_galpon_min: number;
  proveedor_matrix: string;
  utilizar_ventana: boolean;
}

interface Carrier {
  id: number;
  nombre_canonico: string;
  aliases: string[];
  regex_pattern?: string;
  es_externo: boolean;
  es_pickup: boolean;
  activo: boolean;
  prioridad_regex: number;
}

// Paginación
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  size: number;
}

// QR
interface QRResult {
  ok: boolean;
  remito: string;
  message: string;
  version: string;
}
```

---

## 4.6 Colores y Estados

### Badges de estado (clasificación)

| Estado | Color | Icono |
|--------|-------|-------|
| `pendiente` | Gray | ⏳ |
| `enviar` | Green | ✅ |
| `corregir` | Red | 🔧 |
| `retiro_sospechado` | Yellow | 🏪 |
| `transporte_externo` | Blue | 🚛 |
| `no_encontrado` | Red dark | ❌ |
| `excluido` | Orange | ⛔ |

### Badges de lifecycle

| Estado | Color | Icono |
|--------|-------|-------|
| `ingresado` | Gray | 📥 |
| `armado` | Blue | 📦 |
| `despachado` | Indigo | 🚚 |
| `entregado` | Green | ✅ |
| `historico` | Slate | 📚 |

### Marcadores de mapa

| Tipo | Color | Forma |
|------|-------|-------|
| Depósito | Negro | 🏠 House icon |
| Normal | Azul (#3b82f6) | Círculo numerado |
| Urgente | Rojo (#ef4444) | Círculo numerado |
| Prioridad | Amarillo (#eab308) | Círculo numerado |
| Entregado | Verde (#22c55e) | ✓ |

---

## 4.7 Flujos de Usuario

### Flujo 1: Ingesta de remitos

```
/remitos/ingest
   │
   ├─ Pegar lista de remitos (textarea, uno por línea)
   ├─ Click "Ingestar"
   │     → POST /api/v1/remitos/ingest
   │     → Muestra resultado: X nuevos, Y duplicados, Z errores
   │
   └─ Redirige a /remitos con filtro fecha=hoy
```

### Flujo 2: Corrección de dirección

```
/remitos/{id}  (remito con estado "corregir")
   │
   ├─ Click "Corregir dirección"
   ├─ Input con dirección actual → editar
   ├─ Click "Guardar"
   │     → PUT /api/v1/remitos/{id}/corregir-direccion
   │     → Re-geocodifica automáticamente
   │     → Actualiza mapa con nuevo pin
   │
   └─ Si geocodificación exitosa → estado cambia a "enviar"
```

### Flujo 3: Generación de ruta

```
/rutas/generar
   │
   ├─ Revisar/ajustar configuración
   ├─ Click "Generar Ruta"
   │     → POST /api/v1/rutas/generar
   │     → Loading spinner con progress
   │     → Respuesta: ruta con paradas + excluidos
   │
   └─ Redirige a /rutas/{id}
        ├─ Mapa con ruta dibujada
        ├─ Lista de paradas ordenadas
        ├─ Links a Google Maps (fragmentados)
        └─ Lista de excluidos con motivo
```

### Flujo 4: Escaneo QR (ARMADO)

```
/qr  (móvil)
   │
   ├─ Activar cámara → escanear QR del paquete
   │     → Decodifica número de remito
   │     → GET /api/v1/qr/scan?remito=X&token=Y
   │     → Feedback visual + sonido
   │
   ├─ O: ingresar número manualmente
   │
   └─ Historial de escaneos de la sesión
```

### Flujo 5: Marcar entregados

```
/reporte
   │
   ├─ Tildar checkboxes "Entregado" (validación: requiere Armado)
   ├─ Click "Procesar Entregados"
   │     → POST /api/v1/entregados/procesar
   │     → Modal de confirmación con lista
   │     → Resultado: X procesados, Y rechazados
   │
   └─ Tabla se actualiza (entregados desaparecen → /historico)
```

---

## 4.8 Dependencias del Frontend (`package.json`)

```json
{
  "dependencies": {
    "next": "^15.1",
    "react": "^19.0",
    "react-dom": "^19.0",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1",
    "recharts": "^2.15",
    "html5-qrcode": "^2.3.8",
    "tailwindcss": "^4.0",
    "@tailwindcss/postcss": "^4.0",
    "clsx": "^2.1",
    "date-fns": "^4.1"
  },
  "devDependencies": {
    "typescript": "^5.7",
    "@types/react": "^19",
    "@types/leaflet": "^1.9.8",
    "@types/node": "^22",
    "eslint": "^9",
    "eslint-config-next": "^15.1"
  }
}
```

---

*Documento 04 de 05 — Serie Migración MolyMarket*
