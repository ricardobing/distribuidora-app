export const ESTADO_CLASIFICACION_LABELS: Record<string, string> = {
  pendiente: "Pendiente",
  enviar: "Para enviar",
  corregir: "Corregir dirección",
  retiro_sospechado: "Retiro sospechado",
  transporte_externo: "Transporte externo",
  no_encontrado: "No encontrado",
  excluido: "Excluido",
};

export const ESTADO_CLASIFICACION_COLORS: Record<string, string> = {
  pendiente: "bg-yellow-100 text-yellow-800",
  enviar: "bg-green-100 text-green-800",
  corregir: "bg-orange-100 text-orange-800",
  retiro_sospechado: "bg-purple-100 text-purple-800",
  transporte_externo: "bg-blue-100 text-blue-800",
  no_encontrado: "bg-red-100 text-red-800",
  excluido: "bg-gray-100 text-gray-800",
};

export const ESTADO_LIFECYCLE_LABELS: Record<string, string> = {
  ingresado: "Ingresado",
  armado: "Armado",
  despachado: "Despachado",
  entregado: "Entregado",
  historico: "Histórico",
};

export const RUTA_ESTADO_LABELS: Record<string, string> = {
  borrador: "Borrador",
  confirmada: "Confirmada",
  en_curso: "En curso",
  completada: "Completada",
  cancelada: "Cancelada",
};

export const DEPOT_LAT = -32.91973;
export const DEPOT_LNG = -68.81829;

export const MENDOZA_CENTER: [number, number] = [-32.9, -68.85];
export const MENDOZA_ZOOM = 11;
