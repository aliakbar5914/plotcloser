"use client";

import AdminShell from "@/components/AdminShell";
import { admin, formatDate } from "@/lib/api";
import { useAdminData } from "@/lib/useAdmin";

async function loadVisits(password: string) {
  const [visits, followUps] = await Promise.all([admin.visits(password), admin.followUps(password)]);
  return { visits, followUps };
}

export default function VisitsPage() {
  const { data, error } = useAdminData(loadVisits, 15_000);

  return (
    <AdminShell title="Visits & follow-ups">
      {error && <p className="mb-4 text-red-600">{error}</p>}
      {!data ? (
        <p className="text-slate-500">Loading…</p>
      ) : (
        <div className="space-y-8">
          <section>
            <h2 className="mb-2 font-semibold">📅 Booked site visits & test drives ({data.visits.length})</h2>
            <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="p-3">Visit</th>
                    <th className="p-3">Customer</th>
                    <th className="p-3">Listing</th>
                    <th className="p-3">When</th>
                    <th className="p-3">Lead</th>
                    <th className="p-3">Booked at</th>
                  </tr>
                </thead>
                <tbody>
                  {data.visits.map((visit) => (
                    <tr key={visit.id} className="border-t border-slate-100">
                      <td className="p-3 font-semibold">#{visit.id}</td>
                      <td className="p-3">{visit.lead_name ?? `Visitor ${visit.user_id.slice(-6)}`}</td>
                      <td className="p-3">
                        {visit.type === "car" ? "🚗" : "🏡"} #{visit.listing_id} {visit.title}
                        <span className="block text-xs text-slate-500">{visit.area}</span>
                      </td>
                      <td className="p-3 font-medium">{visit.requested_time}</td>
                      <td className="p-3">{visit.score != null ? `${visit.score}/10 ${visit.temperature ?? ""}` : "-"}</td>
                      <td className="p-3 text-slate-500">{formatDate(visit.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {data.visits.length === 0 && <p className="p-4 text-sm text-slate-400">No visits yet.</p>}
            </div>
          </section>

          <section>
            <h2 className="mb-2 font-semibold">🔔 Follow-ups ({data.followUps.length})</h2>
            <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="p-3">#</th>
                    <th className="p-3">Customer</th>
                    <th className="p-3">Due</th>
                    <th className="p-3">Note</th>
                    <th className="p-3">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {data.followUps.map((followUp) => (
                    <tr key={followUp.id} className="border-t border-slate-100">
                      <td className="p-3 font-semibold">#{followUp.id}</td>
                      <td className="p-3">Visitor {followUp.user_id.slice(-6)}</td>
                      <td className="p-3 font-medium">{followUp.due}</td>
                      <td className="p-3">{followUp.note}</td>
                      <td className="p-3 text-slate-500">{formatDate(followUp.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {data.followUps.length === 0 && <p className="p-4 text-sm text-slate-400">No follow-ups yet.</p>}
            </div>
          </section>
        </div>
      )}
    </AdminShell>
  );
}
