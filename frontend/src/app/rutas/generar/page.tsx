"use client";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { rutasApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";
import Link from "next/link";

const DEFAULT_CONFIG = {
  tiempo_espera_min: 10,
  deposito_lat: -32.91973,
  deposito_lng: -68.81829,
  hora_desde: "09:00",
  hora_hasta: "14:00",
  evitar_saltos_min: 25,
  vuelta_galpon_min: 25,
  proveedor_matrix: "ors",
  utilizar_ventana: true,
  distancia_max_km: 45.0,
};

export default function GenerarRutaPage() {
  const qc = useQueryClient();
  const router = useRouter();
  const [config, setConfig] = useState(DEFAULT_CONFIG);

  const generateMut = useMutation({
    mutationFn: () => rutasApi.generate(config),
    onSuccess: (ruta) => {
      toast.success(`Ruta generada: ${ruta.total_paradas} paradas`);
      qc.invalidateQueries({ queryKey: ["rutas"] });
      router.push(`/rutas/${ruta.id}`);
    },
    onError: () => toast.error("Error al generar ruta"),
  });

  const update = (key: string, value: unknown) =>
    setConfig((prev) => ({ ...prev, [key]: value }));

  return (
    <AppLayout>
      <div className="max-w-xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <Link href="/rutas" className="text-gray-400 hover:text-gray-600">← Rutas</Link>
          <h1 className="text-2xl font-bold text-gray-800">Generar ruta con configuración</h1>
        </div>

        <div className="bg-white rounded-xl shadow p-6 space-y-5">
          <ConfigField
            label="Tiempo espera por parada (min)"
            type="number"
            value={String(config.tiempo_espera_min)}
            onChange={(v) => update("tiempo_espera_min", Number(v))}
          />
          <ConfigField
            label="Hora desde"
            type="time"
            value={config.hora_desde}
            onChange={(v) => update("hora_desde", v)}
          />
          <ConfigField
            label="Hora hasta"
            type="time"
            value={config.hora_hasta}
            onChange={(v) => update("hora_hasta", v)}
          />
          <ConfigField
            label="Distancia máxima (km)"
            type="number"
            value={String(config.distancia_max_km)}
            onChange={(v) => update("distancia_max_km", Number(v))}
          />
          <ConfigField
            label="Umbral saltos (min)"
            type="number"
            value={String(config.evitar_saltos_min)}
            onChange={(v) => update("evitar_saltos_min", Number(v))}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Proveedor Distance Matrix</label>
            <select
              value={config.proveedor_matrix}
              onChange={(e) => update("proveedor_matrix", e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 outline-none"
            >
              <option value="ors">ORS (OpenRouteService)</option>
              <option value="mapbox">Mapbox</option>
              <option value="google">Google Maps</option>
            </select>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="utilizar_ventana"
              checked={config.utilizar_ventana}
              onChange={(e) => update("utilizar_ventana", e.target.checked)}
              className="h-4 w-4 text-amber-500 rounded"
            />
            <label htmlFor="utilizar_ventana" className="text-sm font-medium text-gray-700">
              Filtrar por ventana horaria
            </label>
          </div>

          <button
            onClick={() => generateMut.mutate()}
            disabled={generateMut.isPending}
            className="w-full bg-amber-500 hover:bg-amber-600 text-white font-semibold py-2.5 rounded-lg transition disabled:opacity-60"
          >
            {generateMut.isPending ? "Generando ruta..." : "⚡ Generar ruta"}
          </button>
        </div>
      </div>
    </AppLayout>
  );
}

function ConfigField({
  label, type, value, onChange,
}: {
  label: string; type: string; value: string; onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 outline-none"
      />
    </div>
  );
}
