import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";

export function formatDate(dateStr?: string): string {
  if (!dateStr) return "—";
  try {
    return format(parseISO(dateStr), "dd/MM/yyyy HH:mm", { locale: es });
  } catch {
    return dateStr;
  }
}

export function formatDateShort(dateStr?: string): string {
  if (!dateStr) return "—";
  try {
    return format(parseISO(dateStr.includes("T") ? dateStr : `${dateStr}T00:00:00`), "dd/MM/yyyy", { locale: es });
  } catch {
    return dateStr;
  }
}

export function formatMinutes(min?: number): string {
  if (min == null) return "—";
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  if (h > 0) return `${h}h ${m}min`;
  return `${m}min`;
}

export function formatKm(km?: number): string {
  if (km == null) return "—";
  return `${km.toFixed(1)} km`;
}

export function formatCost(usd?: number): string {
  if (usd == null) return "—";
  return `USD $${usd.toFixed(4)}`;
}

export function currentMes(): string {
  return format(new Date(), "yyyy-MM");
}
