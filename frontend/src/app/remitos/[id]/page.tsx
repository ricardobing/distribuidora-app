"use client";
import { use } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { remitosApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import { formatDate } from "@/lib/formatters";
import {
  ESTADO_CLASIFICACION_LABELS,
  ESTADO_CLASIFICACION_COLORS,
  ESTADO_LIFECYCLE_LABELS,
} from "@/lib/constants";
import toast from "react-hot-toast";
import Link from "next/link";
import { useState } from "react";

export default function RemitoDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: numero } = use(params);
  const qc = useQueryClient();
  const [editDir, setEditDir] = useState(false);
  const [newDir, setNewDir] = useState("");

  const { data: remito, isLoading, error } = useQuery({
    queryKey: ["remito", numero],
    queryFn: () => remitosApi.get(numero),
  });

  const reprocessMut = useMutation({
    mutationFn: () => remitosApi.reprocess(numero),
    onSuccess: () => {
      toast.success("Remito reprocesado");
      qc.invalidateQueries({ queryKey: ["remito", numero] });
    },
  });

  const correctDirMut = useMutation({
    mutationFn: (dir: string) => remitosApi.correctDireccion(numero, dir),
    onSuccess: () => {
      toast.success("Dirección corregida y geocodificada");
      qc.invalidateQueries({ queryKey: ["remito", numero] });
      setEditDir(false);
    },
    onError: () => toast.error("Error al corregir dirección"),
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

  if (error || !remito) {
    return (
      <AppLayout>
        <div className="text-center py-20 text-gray-400">Remito no encontrado</div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <Link href="/remitos" className="text-gray-400 hover:text-gray-600">← Remitos</Link>
          <h1 className="text-2xl font-bold text-gray-800 font-mono">{remito.numero}</h1>
          {remito.es_urgente && (
            <span className="bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded font-medium">URGENTE</span>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <InfoCard title="Estado clasificación">
            <span className={`px-2.5 py-1 rounded text-sm font-medium ${ESTADO_CLASIFICACION_COLORS[remito.estado_clasificacion]}`}>
              {ESTADO_CLASIFICACION_LABELS[remito.estado_clasificacion]}
            </span>
          </InfoCard>
          <InfoCard title="Estado lifecycle">
            <span className="text-gray-700">{ESTADO_LIFECYCLE_LABELS[remito.estado_lifecycle] || remito.estado_lifecycle}</span>
          </InfoCard>
        </div>

        <div className="bg-white rounded-xl shadow p-6 space-y-4">
          <Field label="Cliente" value={remito.cliente} />
          <Field label="Dirección raw" value={remito.direccion_raw} />
          <Field label="Dirección normalizada" value={remito.direccion_normalizada} />
          <Field label="Localidad" value={remito.localidad} />
          <Field label="Observaciones" value={remito.observaciones} />
          <Field label="Carrier" value={remito.carrier_nombre} />
          <Field label="Carrier source" value={remito.carrier_source} />
          <Field label="Ventana horaria" value={remito.ventana_raw} />
          <Field label="Ventana tipo" value={remito.ventana_tipo} />
          {remito.lat && remito.lng && (
            <Field label="Coordenadas" value={`${remito.lat.toFixed(6)}, ${remito.lng.toFixed(6)}`} />
          )}
          <Field label="Geocode provider" value={remito.geocode_provider} />
          <Field label="Score" value={remito.geocode_score?.toFixed(2)} />
          <Field label="Creado" value={formatDate(remito.created_at)} />
          <Field label="Actualizado" value={formatDate(remito.updated_at)} />
        </div>

        {/* Corrección de dirección */}
        <div className="bg-white rounded-xl shadow p-6 mt-4">
          <h2 className="font-semibold text-gray-700 mb-3">Corregir dirección</h2>
          {editDir ? (
            <div className="flex gap-2">
              <input
                value={newDir}
                onChange={(e) => setNewDir(e.target.value)}
                placeholder="Nueva dirección completa"
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 outline-none"
              />
              <button
                onClick={() => correctDirMut.mutate(newDir)}
                disabled={correctDirMut.isPending || !newDir}
                className="bg-amber-500 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-60"
              >
                {correctDirMut.isPending ? "..." : "Guardar"}
              </button>
              <button onClick={() => setEditDir(false)} className="text-gray-400 hover:text-gray-600 text-sm px-2">
                Cancelar
              </button>
            </div>
          ) : (
            <button onClick={() => { setEditDir(true); setNewDir(remito.direccion_raw || ""); }} className="text-amber-600 hover:text-amber-700 text-sm font-medium">
              ✏ Corregir dirección y geocodificar
            </button>
          )}
        </div>

        {/* Acciones */}
        <div className="flex gap-3 mt-4">
          <button
            onClick={() => reprocessMut.mutate()}
            disabled={reprocessMut.isPending}
            className="border border-gray-300 hover:bg-gray-50 px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-60"
          >
            {reprocessMut.isPending ? "Reprocesando..." : "🔄 Reprocesar"}
          </button>
        </div>
      </div>
    </AppLayout>
  );
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex gap-4 text-sm border-b pb-3 last:border-b-0 last:pb-0">
      <span className="text-gray-400 w-44 shrink-0">{label}</span>
      <span className="text-gray-800">{value || "—"}</span>
    </div>
  );
}

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl shadow p-4">
      <p className="text-xs text-gray-400 mb-2">{title}</p>
      {children}
    </div>
  );
}
