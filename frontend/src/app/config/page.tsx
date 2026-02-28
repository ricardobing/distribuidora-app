"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { configApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import { useState } from "react";
import toast from "react-hot-toast";
import type { ConfigItem } from "@/lib/types";

export default function ConfigPage() {
  const qc = useQueryClient();
  const { data: items, isLoading } = useQuery({
    queryKey: ["config"],
    queryFn: configApi.list,
  });

  const updateMut = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) =>
      configApi.update(key, value),
    onSuccess: () => {
      toast.success("Configuración actualizada");
      qc.invalidateQueries({ queryKey: ["config"] });
    },
    onError: () => toast.error("Error al actualizar"),
  });

  const resetMut = useMutation({
    mutationFn: configApi.reset,
    onSuccess: () => {
      toast.success("Configuración restaurada a defaults");
      qc.invalidateQueries({ queryKey: ["config"] });
    },
  });

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Configuración</h1>
        <button
          onClick={() => resetMut.mutate()}
          disabled={resetMut.isPending}
          className="border border-red-300 text-red-600 hover:bg-red-50 px-4 py-2 rounded-lg text-sm font-medium transition"
        >
          Restaurar defaults
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500" />
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Clave</th>
                <th className="px-4 py-3 text-left font-medium">Descripción</th>
                <th className="px-4 py-3 text-left font-medium">Tipo</th>
                <th className="px-4 py-3 text-left font-medium">Valor</th>
                <th className="px-4 py-3 text-left font-medium">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items?.map((item: ConfigItem) => (
                <ConfigRow key={item.key} item={item} onSave={(val) => updateMut.mutate({ key: item.key, value: val })} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  );
}

function ConfigRow({ item, onSave }: { item: ConfigItem; onSave: (v: string) => void }) {
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState(item.value);

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3 font-mono text-gray-700 text-xs">{item.key}</td>
      <td className="px-4 py-3 text-gray-500 text-xs">{item.descripcion || "—"}</td>
      <td className="px-4 py-3">
        <span className="bg-gray-100 text-gray-500 text-xs px-1.5 py-0.5 rounded">{item.tipo}</span>
      </td>
      <td className="px-4 py-3">
        {editing ? (
          <input
            value={val}
            onChange={(e) => setVal(e.target.value)}
            className="border border-amber-400 rounded px-2 py-1 text-sm w-36 focus:ring-2 focus:ring-amber-400 outline-none"
          />
        ) : (
          <span className="font-medium text-gray-800">{item.value}</span>
        )}
      </td>
      <td className="px-4 py-3">
        {editing ? (
          <div className="flex gap-2">
            <button onClick={() => { onSave(val); setEditing(false); }} className="text-green-600 hover:text-green-700 text-xs font-medium">Guardar</button>
            <button onClick={() => { setVal(item.value); setEditing(false); }} className="text-gray-400 text-xs">Cancelar</button>
          </div>
        ) : (
          <button onClick={() => setEditing(true)} className="text-amber-600 hover:text-amber-700 text-xs font-medium">Editar</button>
        )}
      </td>
    </tr>
  );
}
