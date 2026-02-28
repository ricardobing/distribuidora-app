"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { rutasApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import { formatDateShort, formatMinutes, formatKm } from "@/lib/formatters";
import { RUTA_ESTADO_LABELS } from "@/lib/constants";
import type { RutaSummary } from "@/lib/types";
import toast from "react-hot-toast";
import Link from "next/link";

export default function RutasPage() {
  const qc = useQueryClient();
  const [generating, setGenerating] = useState(false);

  const { data: rutas, isLoading } = useQuery({
    queryKey: ["rutas"],
    queryFn: rutasApi.list,
  });

  const generateMut = useMutation({
    mutationFn: () => rutasApi.generate(),
    onMutate: () => setGenerating(true),
    onSuccess: (ruta) => {
      toast.success(`Ruta generada: ${ruta.total_paradas} paradas`);
      qc.invalidateQueries({ queryKey: ["rutas"] });
      setGenerating(false);
    },
    onError: () => {
      toast.error("Error al generar ruta");
      setGenerating(false);
    },
  });

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Rutas</h1>
        <div className="flex gap-2">
          <Link
            href="/rutas/generar"
            className="border border-amber-500 text-amber-600 hover:bg-amber-50 px-4 py-2 rounded-lg text-sm font-medium transition"
          >
            Generar con config
          </Link>
          <button
            onClick={() => generateMut.mutate()}
            disabled={generating}
            className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-60"
          >
            {generating ? "Generando..." : "⚡ Generar ruta"}
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500" />
        </div>
      ) : (
        <div className="grid gap-3">
          {rutas?.map((r: RutaSummary) => (
            <Link
              key={r.id}
              href={`/rutas/${r.id}`}
              className="bg-white rounded-xl shadow p-5 hover:shadow-md transition flex items-center justify-between"
            >
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-bold text-gray-800">Ruta #{r.id}</span>
                  <span className="text-sm text-gray-500">{formatDateShort(r.fecha)}</span>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                    r.estado === "completada" ? "bg-green-100 text-green-700" :
                    r.estado === "en_curso" ? "bg-blue-100 text-blue-700" :
                    r.estado === "confirmada" ? "bg-amber-100 text-amber-700" :
                    "bg-gray-100 text-gray-600"
                  }`}>
                    {RUTA_ESTADO_LABELS[r.estado] || r.estado}
                  </span>
                </div>
                <div className="flex gap-6 mt-2 text-sm text-gray-500">
                  <span>📍 {r.total_paradas} paradas</span>
                  <span>⏱ {formatMinutes(r.duracion_estimada_min)}</span>
                  <span>📏 {formatKm(r.distancia_total_km)}</span>
                </div>
              </div>
              <span className="text-gray-300 text-xl">›</span>
            </Link>
          ))}
          {!rutas?.length && (
            <div className="text-center py-16 text-gray-400">
              No hay rutas generadas. Hacé click en &quot;Generar ruta&quot; para comenzar.
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}
