"use client";
import { useQuery } from "@tanstack/react-query";
import { billingApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import { formatDate } from "@/lib/formatters";
import { useState } from "react";
import type { BillingTrace } from "@/lib/types";

export default function BillingPage() {
  const [page, setPage] = useState(1);

  const { data: summary } = useQuery({
    queryKey: ["billing-summary"],
    queryFn: billingApi.summary,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["billing", page],
    queryFn: () => billingApi.list({ page, size: 50 }),
  });

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Costos de APIs</h1>

      {summary && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 mb-6">
          <p className="text-sm text-amber-700 font-medium mb-3">
            Total acumulado: <strong>USD ${summary.grand_total_usd?.toFixed(4)}</strong>
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {summary.by_service_sku?.map((s: { service: string; sku?: string; total_cost_usd: number; calls: number }) => (
              <div key={`${s.service}-${s.sku}`} className="bg-white rounded-lg p-3">
                <p className="text-xs text-gray-400 capitalize">{s.service}{s.sku ? ` / ${s.sku}` : ""}</p>
                <p className="font-bold text-gray-800">${s.total_cost_usd.toFixed(4)}</p>
                <p className="text-xs text-gray-500">{s.calls} llamadas</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500" />
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Servicio</th>
                <th className="px-4 py-3 text-left font-medium">SKU</th>
                <th className="px-4 py-3 text-left font-medium">Stage</th>
                <th className="px-4 py-3 text-left font-medium">Unidades</th>
                <th className="px-4 py-3 text-left font-medium">Costo USD</th>
                <th className="px-4 py-3 text-left font-medium">Fecha</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items?.map((b: BillingTrace) => (
                <tr key={b.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium text-gray-700 capitalize">{b.service}</td>
                  <td className="px-4 py-2 text-gray-500 text-xs">{b.sku || "—"}</td>
                  <td className="px-4 py-2 text-gray-500 text-xs">{b.stage || "—"}</td>
                  <td className="px-4 py-2 text-gray-600">{b.units}</td>
                  <td className="px-4 py-2 font-mono text-gray-800">${b.estimated_cost.toFixed(6)}</td>
                  <td className="px-4 py-2 text-gray-400 text-xs">{formatDate(b.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && data.pages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
          <span>{data.total} registros</span>
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
