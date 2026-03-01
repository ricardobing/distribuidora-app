import axios, { AxiosInstance, AxiosError } from "axios";
import type {
  TokenResponse,
  LoginRequest,
  Remito,
  IngestResponse,
  Carrier,
  Ruta,
  RutaSummary,
  ConfigItem,
  HistoricoItem,
  BillingTrace,
  DashboardStats,
  PaginatedResponse,
  QRResult,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function createClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_URL,
    headers: { "Content-Type": "application/json" },
  });

  client.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  });

  client.interceptors.response.use(
    (res) => res,
    (error: AxiosError) => {
      if (error.response?.status === 401 && typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }
  );

  return client;
}

export const api = createClient();

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (data: LoginRequest) =>
    api.post<TokenResponse>("/auth/login", data).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),
  changePassword: (old_password: string, new_password: string) =>
    api.put("/auth/me/password", { old_password, new_password }).then((r) => r.data),
};

// ── Remitos ───────────────────────────────────────────────────────────────────
export const remitosApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<Remito>>("/remitos", { params }).then((r) => r.data),
  get: (numero: string) =>
    api.get<Remito>(`/remitos/${numero}`).then((r) => r.data),
  ingest: (numeros: string[], source?: string) =>
    api.post<IngestResponse>("/remitos/ingest", { numeros, source }).then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post<Remito>("/remitos", data).then((r) => r.data),
  update: (numero: string, data: Record<string, unknown>) =>
    api.put<Remito>(`/remitos/${numero}`, data).then((r) => r.data),
  correctDireccion: (numero: string, direccion: string) =>
    api.put<Remito>(`/remitos/${numero}/direccion`, { direccion }).then((r) => r.data),
  updateClasificacion: (numero: string, clasificacion: string) =>
    api.put<Remito>(`/remitos/${numero}/clasificacion`, { clasificacion }).then((r) => r.data),
  reprocess: (numero: string) =>
    api.post<Remito>(`/remitos/${numero}/reprocess`).then((r) => r.data),
  reprocessAll: () =>
    api.post("/remitos/reprocess-all").then((r) => r.data),
  delete: (numero: string) =>
    api.delete(`/remitos/${numero}`).then((r) => r.data),
  pendientes: () =>
    api.get<Remito[]>("/remitos/pendientes").then((r) => r.data),
};

// ── Carriers ──────────────────────────────────────────────────────────────────
export const carriersApi = {
  list: () => api.get<Carrier[]>("/carriers").then((r) => r.data),
  create: (data: Partial<Carrier>) =>
    api.post<Carrier>("/carriers", data).then((r) => r.data),
  update: (id: number, data: Partial<Carrier>) =>
    api.put<Carrier>(`/carriers/${id}`, data).then((r) => r.data),
  delete: (id: number) =>
    api.delete(`/carriers/${id}`).then((r) => r.data),
  detect: (texto: string) =>
    api.post("/carriers/detect", { texto }).then((r) => r.data),
};

// ── Rutas ─────────────────────────────────────────────────────────────────────
export const rutasApi = {
  list: () => api.get<RutaSummary[]>("/rutas").then((r) => r.data),
  get: (id: number) => api.get<Ruta>(`/rutas/${id}`).then((r) => r.data),
  generate: (config?: Record<string, unknown>) =>
    api.post<Ruta>("/rutas/generar", config).then((r) => r.data),
  geojson: (id: number) => api.get(`/rutas/${id}/geojson`).then((r) => r.data),
  gmapsLinks: (id: number) =>
    api.get<{ links: string[]; count: number }>(`/rutas/${id}/gmaps-links`).then((r) => r.data),
  updateEstado: (id: number, estado: string) =>
    api.put(`/rutas/${id}/estado`, { estado }).then((r) => r.data),
  delete: (id: number) => api.delete(`/rutas/${id}`).then((r) => r.data),
};

// ── QR ────────────────────────────────────────────────────────────────────────
export const qrApi = {
  scan: (numero: string) =>
    api.get<QRResult>(`/qr/scan`, { params: { numero } }).then((r) => r.data),
  scanBatch: (numeros: string[]) =>
    api.post("/qr/scan-batch", { numeros }).then((r) => r.data),
};

// ── Entregados ────────────────────────────────────────────────────────────────
export const entregadosApi = {
  marcar: (remito_ids: number[]) =>
    api.post("/entregados/marcar", { remito_ids }).then((r) => r.data),
  procesar: (remito_ids: number[]) =>
    api.post("/entregados/procesar", { remito_ids }).then((r) => r.data),
};

// ── Histórico ─────────────────────────────────────────────────────────────────
export const historicoApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<HistoricoItem>>("/historico", { params }).then((r) => r.data),
  exportUrl: (mes: string) => `${API_URL}/historico/export/${mes}`,
  restaurar: (id: number) =>
    api.post(`/historico/restaurar/${id}`).then((r) => r.data),
  cierreMensual: () =>
    api.post("/historico/cierre-mensual").then((r) => r.data),
};

// ── Config ────────────────────────────────────────────────────────────────────
export const configApi = {
  list: () => api.get<ConfigItem[]>("/config").then((r) => r.data),
  update: (key: string, value: string) =>
    api.put<ConfigItem>(`/config/${key}`, { value }).then((r) => r.data),
  reset: () => api.post("/config/reset").then((r) => r.data),
};

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const dashboardApi = {
  stats: () => api.get<DashboardStats>("/dashboard/stats").then((r) => r.data),
  costos: (days?: number) =>
    api.get("/dashboard/stats/costos", { params: { days } }).then((r) => r.data),
  entregas: (months?: number) =>
    api.get("/dashboard/stats/entregas", { params: { months } }).then((r) => r.data),
};

// ── Billing ───────────────────────────────────────────────────────────────────
export const billingApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<BillingTrace>>("/billing", { params }).then((r) => r.data),
  summary: () => api.get("/billing/summary").then((r) => r.data),
};

// ── Geocode ───────────────────────────────────────────────────────────────────
export const geocodeApi = {
  geocode: (address: string, provider?: string) =>
    api.post("/geocode", { address, provider }).then((r) => r.data),
  stats: () => api.get("/geocode/cache/stats").then((r) => r.data),
  clearCache: (expired_only = true) =>
    api.delete("/geocode/cache", { params: { expired_only } }).then((r) => r.data),
};

// ── Pedidos Listos ────────────────────────────────────────────────────────────
export const pedidosListosApi = {
  list: (params?: Record<string, unknown>) =>
    api.get("/pedidos-listos", { params }).then((r) => r.data),
  uploadCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/pedidos-listos/upload-csv", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
};
