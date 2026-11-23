"use client";

import AdminShell from "@/components/AdminShell";
import { admin, formatPkr, type Lead, type Stage, type Stats } from "@/lib/api";
import { useAdminData } from "@/lib/useAdmin";

const STAGES: { key: Stage; label: string; color: string }[] = [
  { key: "new", label: "New", color: "border-t-slate-400" },
  { key: "qualified", label: "Qualified", color: "border-t-amber-400" },
  { key: "visit_booked", label: "Visit booked", color: "border-t-emerald-500" },
  { key: "closed", label: "Closed", color: "border-t-sky-500" },
];

const TEMPERATURE_ICON = { hot: "🔥", warm: "🌤️", cold: "❄️" } as const;

async function loadDashboard(password: string) {
  const [stats, leads] = await Promise.all([admin.stats(password), admin.leads(password)]); // both at once
  return { stats, leads };
}

export default function DashboardPage() {
  // Auto-refresh every 10 s so new leads appear live during the demo.
  const { password, data, error, reload } = useAdminData(loadDashboard, 10_000);

  async function moveLead(lead: Lead, stage: Stage) {
    if (!password) return;
    await admin.updateLeadStage(password, lead.id, stage);
    reload();
  }

  return (
    <AdminShell title="Dashboard">
      {error && <p className="mb-4 text-red-600">{error}</p>}
      {!data ? (
        <p className="text-slate-500">Loading…</p>
      ) : (
        <>
          <StatCards stats={data.stats} totalLeads={data.leads.length} />
          <h2 className="mb-3 mt-8 text-lg font-semibold">Lead pipeline</h2>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {STAGES.map((stage) => {
              const leads = data.leads.filter((lead) => lead.stage === stage.key);
              return (
                <div key={stage.key} className={`rounded-2xl border border-t-4 border-slate-200 bg-white p-3 ${stage.color}`}>
                  <p className="mb-2 font-semibold">
                    {stage.label} <span className="text-slate-400">({leads.length})</span>
                  </p>
                  <div className="space-y-2">
                    {leads.map((lead) => (
                      <LeadCard key={lead.id} lead={lead} onMove={moveLead} />
                    ))}
                    {leads.length === 0 && <p className="text-sm text-slate-400">No leads</p>}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </AdminShell>
  );
}

function StatCards({ stats, totalLeads }: { stats: Stats; totalLeads: number }) {
  const cards = [
    { label: "Leads", value: totalLeads },
    { label: "🔥 Hot leads", value: stats.leads_by_temperature.hot ?? 0 },
    { label: "Visits booked", value: stats.visits_booked },
    { label: "Messages", value: stats.messages },
    { label: "🛡️ Blocked attacks", value: stats.blocked },
    { label: "Avg reply time", value: `${(stats.avg_latency_ms / 1000).toFixed(1)} s` },
    { label: "AI cost so far", value: `$${stats.estimated_cost_usd.toFixed(4)}` },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-7">
      {cards.map((card) => (
        <div key={card.label} className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-xs text-slate-500">{card.label}</p>
          <p className="mt-1 text-2xl font-bold">{card.value}</p>
        </div>
      ))}
    </div>
  );
}

function LeadCard({ lead, onMove }: { lead: Lead; onMove: (lead: Lead, stage: Stage) => void }) {
  return (
    <div className="rounded-xl border border-slate-200 p-3 text-sm">
      <div className="flex items-center justify-between">
        <p className="font-semibold">{lead.name ?? `Visitor ${lead.user_id.slice(-6)}`}</p>
        {lead.score != null && (
          <span className="text-xs font-semibold">
            {lead.temperature ? TEMPERATURE_ICON[lead.temperature] : ""} {lead.score}/10
          </span>
        )}
      </div>
      <p className="text-slate-600">
        {lead.budget_pkr ? `PKR ${formatPkr(lead.budget_pkr)}` : "Budget unknown"}
        {lead.preferred_area && ` · ${lead.preferred_area}`}
      </p>
      <p className="text-xs text-slate-500">
        {lead.timeline_months != null && `Buying in ${lead.timeline_months} mo · `}
        {lead.payment_type ?? "payment unknown"}
      </p>
      <select
        value={lead.stage}
        onChange={(event) => onMove(lead, event.target.value as Stage)}
        className="mt-2 w-full rounded-lg border border-slate-200 px-2 py-1 text-xs"
      >
        {STAGES.map((stage) => (
          <option key={stage.key} value={stage.key}>
            Move to: {stage.label}
          </option>
        ))}
      </select>
    </div>
  );
}
