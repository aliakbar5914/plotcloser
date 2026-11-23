"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/listings", label: "Listings & Chat" },
  { href: "/admin", label: "Agency login" },
];

export default function Navbar() {
  const pathname = usePathname(); // which page are we on? (to highlight it)

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold text-slate-900">
          <span className="text-2xl">🏠</span> PlotCloser
        </Link>
        <div className="flex gap-1 text-sm">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-lg px-3 py-2 font-medium transition ${
                pathname === link.href ? "bg-emerald-50 text-emerald-700" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
