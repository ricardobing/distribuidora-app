// ── Auth ─────────────────────────────────────────────────────────────────────
export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: number;
  email: string;
  rol: string;
}

export interface User {
  id: number;
  email: string;
  nombre?: string;
  rol: string;
  activo: boolean;
  created_at?: string;
}

// ── Remitos ───────────────────────────────────────────────────────────────────
export type EstadoClasificacion =
  | "pendiente"
  | "enviar"
  | "corregir"
  | "retiro_sospechado"
  | "transporte_externo"
  | "no_encontrado"
  | "excluido";

export type EstadoLifecycle =
  | "ingresado"
  | "armado"
  | "despachado"
  | "entregado"
  | "historico";

export interface Remito {
  id: number;
  numero: string;
  cliente?: string;
  direccion_raw?: string;
  direccion_normalizada?: string;
  localidad?: string;
  observaciones?: string;
  lat?: number;
  lng?: number;
  geocode_provider?: string;
  geocode_score?: number;
  estado_clasificacion: EstadoClasificacion;
  estado_lifecycle: EstadoLifecycle;
  carrier_nombre?: string;
  carrier_source?: string;
  ventana_raw?: string;
  ventana_tipo?: string;
  ventana_desde?: string;
  ventana_hasta?: string;
  es_urgente: boolean;
  es_prioridad: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface IngestResponse {
  total: number;
  created: number;
  duplicados: number;
  errors: string[];
  remitos: Remito[];
}

// ── Carriers ──────────────────────────────────────────────────────────────────
export interface Carrier {
  id: number;
  nombre_canonico: string;
  aliases: string[];
  regex_pattern?: string;
  es_externo: boolean;
  es_pickup: boolean;
  prioridad_regex: number;
}

// ── Rutas ─────────────────────────────────────────────────────────────────────
export interface RutaParada {
  id: number;
  orden: number;
  remito_id: number;
  remito_numero?: string;
  cliente?: string;
  direccion?: string;
  lat?: number;
  lng?: number;
  minutos_desde_anterior?: number;
  tiempo_espera_min?: number;
  minutos_acumulados?: number;
  distancia_desde_anterior_km?: number;
  observaciones?: string;
  es_urgente: boolean;
  es_prioridad: boolean;
  ventana_tipo?: string;
  estado: string;
}

export interface RutaExcluido {
  id: number;
  remito_id: number;
  remito_numero?: string;
  cliente?: string;
  direccion?: string;
  motivo: string;
  distancia_km?: number;
  observaciones?: string;
}

export interface Ruta {
  id: number;
  fecha: string;
  estado: string;
  total_paradas: number;
  total_excluidos: number;
  duracion_estimada_min?: number;
  distancia_total_km?: number;
  gmaps_links: string[];
  paradas: RutaParada[];
  excluidos: RutaExcluido[];
  config: Record<string, string | number | boolean>;
  api_cost_estimate?: number;
  created_at?: string;
}

export interface RutaSummary {
  id: number;
  fecha: string;
  estado: string;
  total_paradas: number;
  total_excluidos: number;
  duracion_estimada_min?: number;
  distancia_total_km?: number;
}

// ── Config ────────────────────────────────────────────────────────────────────
export interface ConfigItem {
  key: string;
  value: string;
  tipo: string;
  descripcion?: string;
}

// ── Historico ─────────────────────────────────────────────────────────────────
export interface HistoricoItem {
  id: number;
  numero: string;
  cliente?: string;
  direccion?: string;
  localidad?: string;
  fecha_entregado?: string;
  mes_cierre: string;
  carrier_nombre?: string;
  observaciones?: string;
}

// ── Billing ───────────────────────────────────────────────────────────────────
export interface BillingTrace {
  id: number;
  run_id?: string;
  stage?: string;
  service: string;
  sku?: string;
  units: number;
  estimated_cost: number;
  created_at?: string;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export interface DashboardStats {
  today: string;
  remitos: {
    by_clasificacion: Record<string, number>;
    by_lifecycle: Record<string, number>;
    urgentes_pendientes: number;
  };
  historico_mes_actual: number;
  ultima_ruta?: {
    id: number;
    fecha: string;
    estado: string;
    total_paradas: number;
  };
}

// ── Pagination ────────────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ── QR ────────────────────────────────────────────────────────────────────────
export interface QRResult {
  numero: string;
  remito_id?: number;
  estado_anterior?: string;
  estado_nuevo?: string;
  cliente?: string;
  ok: boolean;
  message: string;
}
