"use client";
import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { RutaParada, RutaExcluido } from "@/lib/types";
import { DEPOT_LAT, DEPOT_LNG, MENDOZA_CENTER, MENDOZA_ZOOM } from "@/lib/constants";

// Fix Leaflet default icon issue with Next.js
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

function createNumberedIcon(n: number, urgent = false): L.DivIcon {
  return L.divIcon({
    className: "",
    html: `<div style="
      width:28px;height:28px;border-radius:50%;
      background:${urgent ? "#ef4444" : "#f59e0b"};
      color:#fff;font-weight:bold;font-size:12px;
      display:flex;align-items:center;justify-content:center;
      border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);
    ">${n}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function createDepotIcon(): L.DivIcon {
  return L.divIcon({
    className: "",
    html: `<div style="
      width:32px;height:32px;border-radius:4px;
      background:#1f2937;color:white;font-size:18px;
      display:flex;align-items:center;justify-content:center;
      border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);
    ">🏭</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
}

interface Props {
  paradas: RutaParada[];
  excluidos: RutaExcluido[];
}

export default function RutaMap({ paradas, excluidos }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current).setView(MENDOZA_CENTER, MENDOZA_ZOOM);
    mapInstanceRef.current = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
    }).addTo(map);

    // Depot marker
    L.marker([DEPOT_LAT, DEPOT_LNG], { icon: createDepotIcon() })
      .bindPopup("<strong>Depósito</strong><br>Elpidio González 2753")
      .addTo(map);

    // Route line
    const coords: [number, number][] = [[DEPOT_LAT, DEPOT_LNG]];
    paradas.forEach((p) => {
      if (p.lat && p.lng) coords.push([p.lat, p.lng]);
    });
    coords.push([DEPOT_LAT, DEPOT_LNG]);
    if (coords.length > 2) {
      L.polyline(coords, { color: "#f59e0b", weight: 3, dashArray: "6,4", opacity: 0.8 }).addTo(map);
    }

    // Parada markers
    paradas.forEach((p) => {
      if (!p.lat || !p.lng) return;
      L.marker([p.lat, p.lng], { icon: createNumberedIcon(p.orden, p.es_urgente) })
        .bindPopup(`
          <strong>#${p.orden} - ${p.remito_numero || ""}</strong><br>
          ${p.cliente || ""}<br>
          ${p.direccion || ""}<br>
          <small>⏱ ${p.minutos_acumulados ? Math.round(p.minutos_acumulados) + " min acum." : ""}</small>
        `)
        .addTo(map);
    });

    // Excluidos markers (gray X)
    excluidos.forEach((e) => {
      // Excluidos don't have lat/lng in this schema, skip rendering
    });

    // Fit bounds
    if (coords.length > 2) {
      map.fitBounds(L.latLngBounds(coords), { padding: [40, 40] });
    }

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [paradas, excluidos]);

  return <div ref={mapRef} style={{ width: "100%", height: "100%" }} />;
}
