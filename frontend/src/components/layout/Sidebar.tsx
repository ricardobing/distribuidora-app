"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import clsx from "clsx";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/remitos", label: "Remitos", icon: "📦" },
  { href: "/rutas", label: "Rutas", icon: "🗺️" },
  { href: "/qr", label: "Escáner QR", icon: "📷" },
  { href: "/historico", label: "Histórico", icon: "📁" },
  { href: "/carriers", label: "Transportistas", icon: "🚚" },
  { href: "/config", label: "Configuración", icon: "⚙️" },
  { href: "/billing", label: "Costos API", icon: "💰" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="fixed left-0 top-0 w-64 h-screen bg-white border-r border-gray-200 flex flex-col shadow-sm">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-100">
        <Link href="/dashboard" className="block">
          <h1 className="text-xl font-bold text-amber-600">MolyMarket</h1>
          <p className="text-xs text-gray-400 mt-0.5">Logística Mendoza</p>
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                active
                  ? "bg-amber-50 text-amber-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="px-4 py-4 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-700 truncate">{user?.nombre || user?.email}</p>
            <p className="text-xs text-gray-400 capitalize">{user?.rol}</p>
          </div>
          <button
            onClick={logout}
            title="Cerrar sesión"
            className="text-gray-400 hover:text-red-500 transition ml-2 shrink-0"
          >
            ⏻
          </button>
        </div>
      </div>
    </aside>
  );
}
