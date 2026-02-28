"use client";
import { use } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { rutasApi, entregadosApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import { formatMinutes, formatKm } from "@/lib/formatters";
import dynamic from "next/dynamic";
import toast from "react-hot-toast";
import Link from "next/link";
import { useState } from "react";

const RutaMap = dynamic(() => import("@/components/map/RutaMap"), { ssr: false });

export default function RutaDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const rutaId = Number(id);
  const qc = useQueryClient();
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [tab, setTab] = useState<"paradas" | "excluidos" | "mapa">("paradas");

  const { data: ruta, isLoading } = useQuery({
    queryKey: ["ruta", rutaId],
    queryFn: () => rutasApi.get(rutaId),
  });

  const marcarMut = useMutation({
    mutationFn: (ids: number[]) => entregadosApi.marcar(ids),
    onSuccess: () => {
      toast.success("Remitos marcados como entregados");
      qc.invalidateQueries({ queryKey: ["ruta", rutaId] });
      setSelectedIds([]);
    },
  });

  if (isLoading) {
    return (
      <AppLayout>
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-amber-500" />
        </div>
      </AppLayout>
    );
  }

  if (!ruta) {
    return (
      <AppLayout>
        <div className="text-center py-20 text-gray-400">Ruta no encontrada</div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="flex items-center gap-3 mb-4">
        <Link href="/rutas" className="text-gray-400 hover:text-gray-600">← Rutas</Link>
        <h1 className="text-2xl font-bold text-gray-800">Ruta #{ruta.id}</h1>
        <span className="text-gray-500 text-sm">{ruta.fecha}</span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <Stat label="Paradas" value={ruta.total_paradas} />
        <Stat label="Excluidos" value={ruta.total_excluidos} />
        <Stat label="Duración" value={formatMinutes(ruta.duracion_estimada_min)} />
        <Stat label="Distancia" value={formatKm(ruta.distancia_total_km)} />
      </div>

      {/* Google Maps links */}
      {ruta.gmaps_links?.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-5">
          <p className="text-sm font-medium text-amber-700 mb-2">Links Google Maps ({ruta.gmaps_links.length} segmentos)</p>
          <div className="flex flex-wrap gap-2">
            {ruta.gmaps_links.map((link, i) => (
              <a
                key={i}
                href={link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs bg-white border border-amber-300 text-amber-700 px-3 py-1.5 rounded-lg hover:bg-amber-100 transition"
              >
                Segmento {i + 1}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b">
        {(["paradas", "excluidos", "mapa"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium transition border-b-2 -mb-px capitalize ${
              tab === t ? "border-amber-500 text-amber-600" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t === "paradas" ? `Paradas (${ruta.total_paradas})` :
             t === "excluidos" ? `Excluidos (${ruta.total_excluidos})` : "Mapa"}
          </button>
        ))}
      </div>

      {tab === "mapa" && (
        <div className="bg-white rounded-xl shadow overflow-hidden" style={{ height: 500 }}>
          <RutaMap paradas={ruta.paradas} excluidos={ruta.excluidos} />
        </div>
      )}

      {tab === "paradas" && (
        <>
          {selectedIds.length > 0 && (
            <div className="flex items-center gap-3 mb-3 bg-amber-50 border border-amber-200 rounded-lg p-3">
              <span className="text-sm text-amber-700">{selectedIds.length} seleccionados</span>
              <button
                onClick={() => marcarMut.mutate(selectedIds)}
                disabled={marcarMut.isPending}
                className="bg-green-500 text-white text-sm px-4 py-1.5 rounded-lg hover:bg-green-600 disabled:opacity-60"
              >
                ✓ Marcar entregados
              </button>
              <button onClick={() => setSelectedIds([])} className="text-gray-400 text-sm">Cancelar</button>
            </div>
          )}
          <div className="bg-white rounded-xl shadow overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b text-gray-600">
                <tr>
                  <th className="px-3 py-3 text-left w-8">
                    <input
                      type="checkbox"
                      onChange={(e) => {
                        setSelectedIds(e.target.checked ? ruta.paradas.map((p) => p.remito_id) : []);
                      }}
                    />
                  </th>
                  <th className="px-3 py-3 text-left font-medium">#</th>
                  <th className="px-3 py-3 text-left font-medium">Remito</th>
                  <th className="px-3 py-3 text-left font-medium">Cliente</th>
                  <th className="px-3 py-3 text-left font-medium">Dirección</th>
                  <th className="px-3 py-3 text-left font-medium">⏱ Acum.</th>
                  <th className="px-3 py-3 text-left font-medium">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {ruta.paradas.map((p) => (
                  <tr key={p.id} className={`hover:bg-amber-50 transition ${p.es_urgente ? "bg-red-50" : ""}`}>
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(p.remito_id)}
                        onChange={(e) =>
                          setSelectedIds((prev) =>
                            e.target.checked ? [...prev, p.remito_id] : prev.filter((x) => x !== p.remito_id)
                          )
                        }
                      />
                    </td>
                    <td className="px-3 py-2 font-bold text-amber-600">{p.orden}</td>
                    <td className="px-3 py-2 font-mono text-gray-700">
                      <Link href={`/remitos/${p.remito_numero}`} className="hover:underline">{p.remito_numero}</Link>
                    </td>
                    <td className="px-3 py-2 text-gray-700 max-w-xs truncate">{p.cliente || "—"}</td>
                    <td className="px-3 py-2 text-gray-500 max-w-xs truncate">{p.direccion || "—"}</td>
                    <td className="px-3 py-2 text-gray-600">{formatMinutes(p.minutos_acumulados)}</td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        p.estado === "entregado" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                      }`}>{p.estado}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === "excluidos" && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Remito</th>
                <th className="px-4 py-3 text-left font-medium">Cliente</th>
                <th className="px-4 py-3 text-left font-medium">Motivo</th>
                <th className="px-4 py-3 text-left font-medium">Distancia</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {ruta.excluidos.map((e) => (
                <tr key={e.id}>
                  <td className="px-4 py-2 font-mono text-gray-700">{e.remito_numero}</td>
                  <td className="px-4 py-2 text-gray-700">{e.cliente || "—"}</td>
                  <td className="px-4 py-2">
                    <span className="bg-red-50 text-red-700 px-2 py-0.5 rounded text-xs">{e.motivo}</span>
                  </td>
                  <td className="px-4 py-2 text-gray-500">{formatKm(e.distancia_km)}</td>
                </tr>
              ))}
              {!ruta.excluidos.length && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-400">Sin remitos excluidos</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-xl shadow p-4">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-xl font-bold text-gray-800 mt-1">{value}</p>
    </div>
  );
}
