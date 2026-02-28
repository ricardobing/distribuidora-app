"use client";
import { useState, useEffect, useRef } from "react";
import { qrApi } from "@/lib/api";
import AppLayout from "@/components/layout/AppLayout";
import type { QRResult } from "@/lib/types";
import toast from "react-hot-toast";

export default function QRPage() {
  const [mode, setMode] = useState<"camera" | "manual">("manual");
  const [numero, setNumero] = useState("");
  const [result, setResult] = useState<QRResult | null>(null);
  const [scanning, setScanning] = useState(false);
  const scannerRef = useRef<unknown>(null);

  const scan = async (num: string) => {
    if (!num.trim()) return;
    try {
      const r = await qrApi.scan(num.trim());
      setResult(r);
      if (r.ok) {
        toast.success(r.message);
      } else {
        toast.error(r.message);
      }
    } catch {
      toast.error("Error al escanear");
    }
  };

  useEffect(() => {
    if (mode !== "camera") return;
    let scanner: { stop: () => Promise<void> } | null = null;

    import("html5-qrcode").then(({ Html5QrcodeScanner }) => {
      scanner = new Html5QrcodeScanner(
        "qr-reader",
        { fps: 10, qrbox: { width: 250, height: 250 } },
        false
      );
      scanner.render(
        (decoded: string) => {
          scan(decoded);
        },
        (err: unknown) => {
          console.debug("QR error:", err);
        }
      );
      scannerRef.current = scanner;
    });

    return () => {
      scanner?.stop().catch(() => {});
    };
  }, [mode]);

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Escáner QR</h1>

      <div className="max-w-lg mx-auto">
        <div className="flex gap-2 mb-5">
          <button
            onClick={() => setMode("manual")}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${
              mode === "manual" ? "bg-amber-500 text-white" : "border border-gray-300 text-gray-600 hover:bg-gray-50"
            }`}
          >
            Manual
          </button>
          <button
            onClick={() => setMode("camera")}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${
              mode === "camera" ? "bg-amber-500 text-white" : "border border-gray-300 text-gray-600 hover:bg-gray-50"
            }`}
          >
            Cámara
          </button>
        </div>

        {mode === "manual" && (
          <div className="bg-white rounded-xl shadow p-6">
            <p className="text-sm text-gray-500 mb-4">Ingresa el número de remito del QR</p>
            <div className="flex gap-2">
              <input
                value={numero}
                onChange={(e) => setNumero(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && scan(numero)}
                placeholder="Número de remito"
                autoFocus
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 font-mono text-sm focus:ring-2 focus:ring-amber-400 outline-none"
              />
              <button
                onClick={() => scan(numero)}
                className="bg-amber-500 hover:bg-amber-600 text-white px-5 py-2.5 rounded-lg font-medium transition"
              >
                Escanear
              </button>
            </div>
          </div>
        )}

        {mode === "camera" && (
          <div className="bg-white rounded-xl shadow p-4">
            <div id="qr-reader" className="w-full" />
          </div>
        )}

        {result && (
          <div className={`mt-5 rounded-xl p-5 ${result.ok ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}>
            <p className={`font-semibold text-lg ${result.ok ? "text-green-700" : "text-red-700"}`}>
              {result.ok ? "✓ Escaneado" : "✗ Error"}
            </p>
            <p className="text-sm mt-1 text-gray-700">{result.message}</p>
            {result.cliente && <p className="text-sm text-gray-600 mt-1">Cliente: {result.cliente}</p>}
            {result.estado_anterior && (
              <p className="text-xs text-gray-500 mt-2">
                {result.estado_anterior} → {result.estado_nuevo}
              </p>
            )}
            <button
              onClick={() => { setResult(null); setNumero(""); }}
              className="mt-3 text-sm text-gray-500 hover:text-gray-700"
            >
              Nuevo escaneo
            </button>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
