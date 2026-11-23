"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { admin, ApiError } from "@/lib/api";
import { saveAdminPassword } from "@/lib/adminAuth";

export default function AdminLoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);

  async function login(event: React.FormEvent) {
    event.preventDefault();
    setChecking(true);
    setError("");
    try {
      await admin.login(password); // the API checks the password, not the website
      saveAdminPassword(password);
      router.push("/admin/dashboard");
    } catch (err) {
      setError(err instanceof ApiError && err.status === 401 ? "Wrong password." : "Could not reach the API.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center bg-slate-900 px-4">
      <form onSubmit={login} className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
        <p className="text-3xl">🏠</p>
        <h1 className="mt-2 text-xl font-bold">PlotCloser agency login</h1>
        <p className="text-sm text-slate-500">See your leads, visits and AI conversations.</p>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Admin password"
          className="mt-5 w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-emerald-500"
          autoFocus
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <button
          disabled={checking || !password}
          className="mt-4 w-full rounded-xl bg-emerald-600 py-2 font-semibold text-white disabled:opacity-40"
        >
          {checking ? "Checking…" : "Login"}
        </button>
        <Link href="/" className="mt-4 block text-center text-sm text-slate-500 hover:underline">
          ← Back to website
        </Link>
      </form>
    </main>
  );
}
