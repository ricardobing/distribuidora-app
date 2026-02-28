"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { historicoApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import { currentMes, formatDate } from "@/lib/formatters";
import toast from "react-hot-toast";
import type { HistoricoItem } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function HistoricoPage() {
  const [mes, setMes] = useState(currentMes());
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["historico", mes, page],
    queryFn: () => historicoApi.list({ mes, page, size: 50 }),
  });

  const handleExport = () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : "";
    const url = `${API_URL}/api/v1/historico/export/${mes}`;
    const a = document.createElement("a");
    a.href = url;
    a.setAttribute("download", `historico_${mes}.xlsx`);
    // Add auth header via fetch
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.blob())
      .then((blob) => {
        const href = URL.createObjectURL(blob);
        a.href = href;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(href);
      })
      .catch(() => toast.error("Error al exportar"));
  };

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Histórico de entregas</h1>
        <div className="flex items-center gap-3">
          <input
            type="month"
            value={mes}
            onChange={(e) => { setMes(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 outline-none"
          />
          <button
            onClick={handleExport}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
          >
            Exportar XLSX
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500" />
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Número</th>
                <th className="px-4 py-3 text-left font-medium">Cliente</th>
                <th className="px-4 py-3 text-left font-medium">Dirección</th>
                <th className="px-4 py-3 text-left font-medium">Carrier</th>
                <th className="px-4 py-3 text-left font-medium">Fecha entrega</th>
                <th className="px-4 py-3 text-left font-medium">Mes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items?.map((h: HistoricoItem) => (
                <tr key={h.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-mono text-gray-700">{h.numero}</td>
                  <td className="px-4 py-2 text-gray-700 max-w-xs truncate">{h.cliente || "—"}</td>
                  <td className="px-4 py-2 text-gray-500 max-w-xs truncate">{h.direccion || "—"}</td>
                  <td className="px-4 py-2 text-gray-600">{h.carrier_nombre || "—"}</td>
                  <td className="px-4 py-2 text-gray-500 text-xs">{formatDate(h.fecha_entregado)}</td>
                  <td className="px-4 py-2">
                    <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded">{h.mes_cierre}</span>
                  </td>
                </tr>
              ))}
              {!data?.items?.length && (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                    Sin entregas para {mes}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {data && data.pages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
          <span>{data.total} entregas totales</span>
          <div className="flex gap-2">
            <button disabled={page === 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1 border rounded disabled:opacity-40">← Anterior</button>
            <span className="px-3 py-1">Página {page} de {data.pages}</span>
            <button disabled={page === data.pages} onClick={() => setPage((p) => p + 1)} className="px-3 py-1 border rounded disabled:opacity-40">Siguiente →</button>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
