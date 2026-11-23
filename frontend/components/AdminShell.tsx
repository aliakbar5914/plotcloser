"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearAdminPassword } from "@/lib/adminAuth";

const LINKS = [
  { href: "/admin/dashboard", label: "📊 Dashboard" },
  { href: "/admin/visits", label: "📅 Visits" },
  { href: "/admin/listings", label: "🏘️ Listings" },
  { href: "/admin/chats", label: "💬 Chats & cost" },
];

// The frame around every admin page: top bar, menu, logout.
export default function AdminShell({ title, children }: { title: string; children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    clearAdminPassword();
    router.replace("/admin");
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="bg-slate-900 text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-3">
          <Link href="/admin/dashboard" className="font-bold">
            🏠 PlotCloser <span className="font-normal text-slate-400">· Agency dashboard</span>
          </Link>
          <nav className="flex flex-wrap gap-1 text-sm">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-lg px-3 py-1.5 ${pathname === link.href ? "bg-white/15" : "text-slate-300 hover:bg-white/10"}`}
              >
                {link.label}
              </Link>
            ))}
            <Link href="/" className="rounded-lg px-3 py-1.5 text-slate-300 hover:bg-white/10">
              ↗ Website
            </Link>
            <button onClick={logout} className="rounded-lg px-3 py-1.5 text-slate-300 hover:bg-white/10">
              Logout
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <h1 className="mb-4 text-2xl font-bold">{title}</h1>
        {children}
      </main>
    </div>
  );
}
