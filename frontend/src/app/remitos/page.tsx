"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { remitosApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import { formatDate } from "@/lib/formatters";
import {
  ESTADO_CLASIFICACION_LABELS,
  ESTADO_CLASIFICACION_COLORS,
} from "@/lib/constants";
import type { Remito, EstadoClasificacion } from "@/lib/types";
import toast from "react-hot-toast";
import Link from "next/link";

const CLASIFICACIONES: EstadoClasificacion[] = [
  "pendiente", "enviar", "corregir", "retiro_sospechado",
  "transporte_externo", "no_encontrado", "excluido"
];

export default function RemitosPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [estadoFilter, setEstadoFilter] = useState<string>("");
  const [q, setQ] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["remitos", page, estadoFilter, q],
    queryFn: () =>
      remitosApi.list({
        page,
        size: 50,
        estado_clasificacion: estadoFilter || undefined,
        q: q || undefined,
      }),
  });

  const reprocessMut = useMutation({
    mutationFn: remitosApi.reprocessAll,
    onSuccess: () => {
      toast.success("Reprocesamiento iniciado");
      qc.invalidateQueries({ queryKey: ["remitos"] });
    },
  });

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Remitos</h1>
        <div className="flex gap-2">
          <Link
            href="/remitos/ingest"
            className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
          >
            + Ingresar
          </Link>
          <button
            onClick={() => reprocessMut.mutate()}
            disabled={reprocessMut.isPending}
            className="border border-gray-300 hover:bg-gray-50 px-4 py-2 rounded-lg text-sm font-medium transition"
          >
            Reprocesar pendientes
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="text"
          placeholder="Buscar número o cliente..."
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-64 focus:ring-2 focus:ring-amber-400 outline-none"
        />
        <select
          value={estadoFilter}
          onChange={(e) => { setEstadoFilter(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 outline-none"
        >
          <option value="">Todos los estados</option>
          {CLASIFICACIONES.map((e) => (
            <option key={e} value={e}>{ESTADO_CLASIFICACION_LABELS[e]}</option>
          ))}
        </select>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500" />
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b text-gray-600">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Número</th>
                <th className="text-left px-4 py-3 font-medium">Cliente</th>
                <th className="text-left px-4 py-3 font-medium">Dirección</th>
                <th className="text-left px-4 py-3 font-medium">Estado</th>
                <th className="text-left px-4 py-3 font-medium">Carrier</th>
                <th className="text-left px-4 py-3 font-medium">Fecha</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items?.map((r: Remito) => (
                <tr key={r.id} className="hover:bg-amber-50 transition cursor-pointer">
                  <td className="px-4 py-3">
                    <Link href={`/remitos/${r.numero}`} className="font-mono text-amber-600 hover:underline">
                      {r.numero}
                    </Link>
                    {r.es_urgente && (
                      <span className="ml-2 text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded">
                        URGENTE
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-700 max-w-xs truncate">{r.cliente || "—"}</td>
                  <td className="px-4 py-3 text-gray-500 max-w-xs truncate">{r.direccion_normalizada || r.direccion_raw || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${ESTADO_CLASIFICACION_COLORS[r.estado_clasificacion]}`}>
                      {ESTADO_CLASIFICACION_LABELS[r.estado_clasificacion]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{r.carrier_nombre || "—"}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{formatDate(r.created_at)}</td>
                </tr>
              ))}
              {!data?.items?.length && (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                    Sin remitos para mostrar
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Paginación */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
          <span>{data.total} remitos totales</span>
          <div className="flex gap-2">
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >
              ← Anterior
            </button>
            <span className="px-3 py-1">Página {page} de {data.pages}</span>
            <button
              disabled={page === data.pages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >
              Siguiente →
            </button>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
