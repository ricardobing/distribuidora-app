"use client";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { remitosApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import toast from "react-hot-toast";
import type { IngestResponse } from "@/lib/types";
import { ESTADO_CLASIFICACION_LABELS, ESTADO_CLASIFICACION_COLORS } from "@/lib/constants";
import Link from "next/link";

export default function IngestPage() {
  const qc = useQueryClient();
  const [raw, setRaw] = useState("");
  const [result, setResult] = useState<IngestResponse | null>(null);

  const ingestMut = useMutation({
    mutationFn: (numeros: string[]) => remitosApi.ingest(numeros, "manual"),
    onSuccess: (data) => {
      setResult(data);
      toast.success(`${data.created} remitos creados`);
      qc.invalidateQueries({ queryKey: ["remitos"] });
    },
    onError: () => toast.error("Error al ingresar remitos"),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const numeros = raw
      .split(/[\n,;]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    if (!numeros.length) {
      toast.error("Ingresa al menos un número de remito");
      return;
    }
    ingestMut.mutate(numeros);
  };

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <Link href="/remitos" className="text-gray-400 hover:text-gray-600">
            ← Remitos
          </Link>
          <h1 className="text-2xl font-bold text-gray-800">Ingresar remitos</h1>
        </div>

        <div className="bg-white rounded-xl shadow p-6 mb-6">
          <p className="text-sm text-gray-500 mb-4">
            Pegá los números de remito separados por línea, coma o punto y coma.
            El sistema ejecuta el pipeline completo (normalización → geocodificación → ventana).
          </p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <textarea
              value={raw}
              onChange={(e) => setRaw(e.target.value)}
              rows={8}
              placeholder={"R-001\nR-002\nR-003"}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 font-mono text-sm focus:ring-2 focus:ring-amber-400 outline-none resize-none"
            />
            <button
              type="submit"
              disabled={ingestMut.isPending}
              className="w-full bg-amber-500 hover:bg-amber-600 text-white font-semibold py-2.5 rounded-lg transition disabled:opacity-60"
            >
              {ingestMut.isPending ? "Procesando..." : "Ingresar remitos"}
            </button>
          </form>
        </div>

        {result && (
          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="font-semibold text-gray-700 mb-4">Resultado</h2>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-green-50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-green-600">{result.created}</p>
                <p className="text-xs text-green-600">Creados</p>
              </div>
              <div className="bg-yellow-50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-yellow-600">{result.duplicados}</p>
                <p className="text-xs text-yellow-600">Duplicados</p>
              </div>
              <div className="bg-red-50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-red-600">{result.errors.length}</p>
                <p className="text-xs text-red-600">Errores</p>
              </div>
            </div>

            {result.errors.length > 0 && (
              <div className="bg-red-50 rounded-lg p-3 mb-4">
                <p className="text-xs font-medium text-red-700 mb-1">Errores:</p>
                {result.errors.map((e, i) => (
                  <p key={i} className="text-xs text-red-600">{e}</p>
                ))}
              </div>
            )}

            <div className="space-y-2 max-h-80 overflow-y-auto">
              {result.remitos?.map((r) => (
                <div key={r.id} className="flex items-center justify-between text-sm border-b pb-2">
                  <Link href={`/remitos/${r.numero}`} className="font-mono text-amber-600 hover:underline">
                    {r.numero}
                  </Link>
                  <span className="text-gray-500 truncate mx-4 flex-1">{r.cliente || r.direccion_raw}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${ESTADO_CLASIFICACION_COLORS[r.estado_clasificacion]}`}>
                    {ESTADO_CLASIFICACION_LABELS[r.estado_clasificacion]}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
