"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { carriersApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import toast from "react-hot-toast";
import { useState } from "react";
import type { Carrier } from "@/lib/types";

export default function CarriersPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nombre_canonico: "", regex_pattern: "", es_externo: true, es_pickup: false, prioridad_regex: 50 });

  const { data: carriers, isLoading } = useQuery({
    queryKey: ["carriers"],
    queryFn: carriersApi.list,
  });

  const createMut = useMutation({
    mutationFn: (data: typeof form) => carriersApi.create(data),
    onSuccess: () => {
      toast.success("Carrier creado");
      qc.invalidateQueries({ queryKey: ["carriers"] });
      setShowForm(false);
    },
    onError: () => toast.error("Error al crear carrier"),
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => carriersApi.delete(id),
    onSuccess: () => {
      toast.success("Carrier eliminado");
      qc.invalidateQueries({ queryKey: ["carriers"] });
    },
  });

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Transportistas</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
        >
          + Agregar
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow p-5 mb-5">
          <h2 className="font-semibold text-gray-700 mb-4">Nuevo carrier</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre canónico</label>
              <input value={form.nombre_canonico} onChange={(e) => setForm((f) => ({ ...f, nombre_canonico: e.target.value }))} className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Regex pattern</label>
              <input value={form.regex_pattern} onChange={(e) => setForm((f) => ({ ...f, regex_pattern: e.target.value }))} className="w-full border rounded-lg px-3 py-2 font-mono text-sm focus:ring-2 focus:ring-amber-400 outline-none" placeholder="(?i)pattern" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Prioridad regex</label>
              <input type="number" value={form.prioridad_regex} onChange={(e) => setForm((f) => ({ ...f, prioridad_regex: Number(e.target.value) }))} className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 outline-none" />
            </div>
            <div className="flex items-center gap-6 pt-6">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.es_externo} onChange={(e) => setForm((f) => ({ ...f, es_externo: e.target.checked }))} />
                Externo
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.es_pickup} onChange={(e) => setForm((f) => ({ ...f, es_pickup: e.target.checked }))} />
                Pickup
              </label>
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button onClick={() => createMut.mutate(form)} disabled={createMut.isPending} className="bg-amber-500 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-60">
              {createMut.isPending ? "Creando..." : "Crear"}
            </button>
            <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600 text-sm">Cancelar</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b text-gray-600">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Nombre</th>
              <th className="px-4 py-3 text-left font-medium">Regex</th>
              <th className="px-4 py-3 text-left font-medium">Tipo</th>
              <th className="px-4 py-3 text-left font-medium">Prioridad</th>
              <th className="px-4 py-3 text-left font-medium">Acción</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr><td colSpan={5} className="px-4 py-12 text-center text-gray-400">Cargando...</td></tr>
            ) : carriers?.map((c: Carrier) => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-medium text-gray-800">{c.nombre_canonico}</td>
                <td className="px-4 py-2 font-mono text-gray-500 text-xs max-w-xs truncate">{c.regex_pattern || "—"}</td>
                <td className="px-4 py-2">
                  {c.es_pickup ? (
                    <span className="bg-purple-100 text-purple-700 text-xs px-2 py-0.5 rounded">Pickup</span>
                  ) : c.es_externo ? (
                    <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded">Externo</span>
                  ) : (
                    <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded">Propio</span>
                  )}
                </td>
                <td className="px-4 py-2 text-gray-600">{c.prioridad_regex}</td>
                <td className="px-4 py-2">
                  <button onClick={() => deleteMut.mutate(c.id)} className="text-red-500 hover:text-red-700 text-xs">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppLayout>
  );
}
