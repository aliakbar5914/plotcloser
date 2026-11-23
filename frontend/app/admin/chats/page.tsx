"use client";

import { useState } from "react";
import AdminShell from "@/components/AdminShell";
import { admin, formatDate } from "@/lib/api";
import { useAdminData } from "@/lib/useAdmin";

export default function ChatsPage() {
  const { data: chats, error } = useAdminData((password) => admin.chats(password), 15_000);
  const [onlyBlocked, setOnlyBlocked] = useState(false);

  const visible = (chats ?? []).filter((chat) => !onlyBlocked || chat.blocked);
  const totalIn = visible.reduce((sum, chat) => sum + chat.tokens_in, 0);
  const totalOut = visible.reduce((sum, chat) => sum + chat.tokens_out, 0);
  const cost = (totalIn * 0.1 + totalOut * 0.5) / 1_000_000; // Claude Haiku 5.5 price per 1M tokens

  return (
    <AdminShell title="Conversations & cost">
      {error && <p className="mb-4 text-red-600">{error}</p>}
      <div className="mb-4 flex flex-wrap items-center gap-4 text-sm">
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={onlyBlocked} onChange={(e) => setOnlyBlocked(e.target.checked)} />
          Show only blocked (safety) messages
        </label>
        <span className="text-slate-500">
          {visible.length} messages · {totalIn.toLocaleString()} tokens in / {totalOut.toLocaleString()} out · ≈ ${cost.toFixed(4)}
        </span>
      </div>

      <div className="space-y-3">
        {!chats && <p className="text-slate-500">Loading…</p>}
        {visible.map((chat) => (
          <div key={chat.id} className={`rounded-2xl border bg-white p-4 text-sm ${chat.blocked ? "border-red-200" : "border-slate-200"}`}>
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
              <span>
                {formatDate(chat.created_at)} · user …{chat.user_id.slice(-6)} · thread …{chat.thread_id.slice(-6)}
              </span>
              <span>
                {chat.blocked && <span className="mr-2 rounded bg-red-100 px-2 py-0.5 font-semibold text-red-700">🛡️ Blocked</span>}
                {(chat.latency_ms / 1000).toFixed(1)} s · {chat.tokens_in}/{chat.tokens_out} tokens
              </span>
            </div>
            <p className="mt-2"><span className="font-semibold">Customer:</span> {chat.user_message}</p>
            <p className="mt-1 whitespace-pre-wrap text-slate-700"><span className="font-semibold">Agent:</span> {chat.reply.replace(/\*\*/g, "")}</p>
            {chat.tool_calls.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {chat.tool_calls.map((tool, index) => (
                  <span key={index} className="rounded-full bg-slate-100 px-2 py-0.5 font-mono text-[11px] text-slate-600">
                    🔧 {tool.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </AdminShell>
  );
}
