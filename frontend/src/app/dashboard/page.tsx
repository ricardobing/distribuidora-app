"use client";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import { formatMinutes, formatKm } from "@/lib/formatters";
import { ESTADO_CLASIFICACION_LABELS, RUTA_ESTADO_LABELS } from "@/lib/constants";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from "recharts";

const COLORS = ["#f59e0b", "#10b981", "#ef4444", "#6366f1", "#8b5cf6", "#ec4899", "#14b8a6"];

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: dashboardApi.stats,
    refetchInterval: 30000,
  });

  const { data: costos } = useQuery({
    queryKey: ["dashboard-costos"],
    queryFn: () => dashboardApi.costos(30),
  });

  if (isLoading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-amber-500" />
        </div>
      </AppLayout>
    );
  }

  const clasificacionData = Object.entries(stats?.remitos?.by_clasificacion || {}).map(
    ([k, v]) => ({ name: ESTADO_CLASIFICACION_LABELS[k] || k, value: v })
  );

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard
          title="Urgentes pendientes"
          value={stats?.remitos?.urgentes_pendientes ?? 0}
          color="red"
        />
        <KpiCard
          title="Para enviar"
          value={stats?.remitos?.by_clasificacion?.enviar ?? 0}
          color="green"
        />
        <KpiCard
          title="Entregados este mes"
          value={stats?.historico_mes_actual ?? 0}
          color="blue"
        />
        <KpiCard
          title="Costo APIs (30d)"
          value={`$${costos?.total_cost_usd?.toFixed(3) ?? "0.000"}`}
          color="amber"
        />
      </div>

      {/* Última ruta */}
      {stats?.ultima_ruta && (
        <div className="bg-white rounded-xl shadow p-5 mb-6">
          <h2 className="font-semibold text-gray-700 mb-3">Última ruta generada</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <InfoItem label="ID" value={`#${stats.ultima_ruta.id}`} />
            <InfoItem label="Fecha" value={stats.ultima_ruta.fecha} />
            <InfoItem label="Estado" value={RUTA_ESTADO_LABELS[stats.ultima_ruta.estado] || stats.ultima_ruta.estado} />
            <InfoItem label="Paradas" value={String(stats.ultima_ruta.total_paradas)} />
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow p-5">
          <h2 className="font-semibold text-gray-700 mb-4">Remitos por clasificación</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={clasificacionData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {clasificacionData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow p-5">
          <h2 className="font-semibold text-gray-700 mb-4">Costos por servicio (30d)</h2>
          {costos?.by_service?.length ? (
            <div className="space-y-2">
              {costos.by_service.map(
                (s: { service: string; total_cost_usd: number; calls: number }) => (
                  <div key={s.service} className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 capitalize">{s.service}</span>
                    <span className="font-mono text-gray-800">
                      ${s.total_cost_usd.toFixed(4)} ({s.calls} calls)
                    </span>
                  </div>
                )
              )}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">Sin datos de costos</p>
          )}
        </div>
      </div>
    </AppLayout>
  );
}

function KpiCard({
  title, value, color,
}: {
  title: string;
  value: string | number;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    red: "bg-red-50 border-red-200 text-red-700",
    green: "bg-green-50 border-green-200 text-green-700",
    blue: "bg-blue-50 border-blue-200 text-blue-700",
    amber: "bg-amber-50 border-amber-200 text-amber-700",
  };
  return (
    <div className={`rounded-xl border p-4 ${colorMap[color] ?? ""}`}>
      <p className="text-xs font-medium opacity-70">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="font-medium text-gray-800">{value}</p>
    </div>
  );
}
