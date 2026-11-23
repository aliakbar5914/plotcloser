// All calls to the PlotCloser API live here, so pages stay simple.

// Set in Vercel (and .env.local for local dev). Baked into the site at build time.
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

// ---------- Types (shapes of the data the API returns) ----------
export type Listing = {
  id: number;
  type: "property" | "car";
  title: string;
  city: string;
  area: string;
  size_label: string | null;
  price_pkr: number;
  purpose: "sale" | "rent";
  bedrooms: number | null;
  description: string | null;
  image_url: string | null;
};

export type ToolCall = { name: string; args: Record<string, unknown> };

export type ChatResult = {
  reply: string;
  tool_calls: ToolCall[];
  tokens: { in: number; out: number };
};

export type Lead = {
  id: number;
  user_id: string;
  name: string | null;
  interest_type: string | null;
  budget_pkr: number | null;
  preferred_area: string | null;
  timeline_months: number | null;
  payment_type: string | null;
  score: number | null;
  temperature: "hot" | "warm" | "cold" | null;
  stage: Stage;
  updated_at: string;
};

export type Stage = "new" | "qualified" | "visit_booked" | "closed";

export type Visit = {
  id: number;
  user_id: string;
  requested_time: string;
  status: string;
  created_at: string;
  listing_id: number;
  title: string;
  area: string;
  type: string;
  lead_name: string | null;
  score: number | null;
  temperature: string | null;
};

export type FollowUp = { id: number; user_id: string; due: string; note: string; status: string; created_at: string };

export type ChatLog = {
  id: number;
  user_id: string;
  thread_id: string;
  user_message: string;
  reply: string;
  tool_calls: ToolCall[];
  tokens_in: number;
  tokens_out: number;
  latency_ms: number;
  blocked: boolean;
  created_at: string;
};

export type Stats = {
  messages: number;
  users: number;
  tokens_in: number;
  tokens_out: number;
  avg_latency_ms: number;
  blocked: number;
  visits_booked: number;
  leads_by_stage: Partial<Record<Stage, number>>;
  leads_by_temperature: Partial<Record<"hot" | "warm" | "cold", number>>;
  estimated_cost_usd: number;
};

export type NewListing = Omit<Listing, "id" | "size_label" | "bedrooms" | "description" | "image_url"> & {
  size_label?: string;
  size_marla?: number;
  bedrooms?: number;
  description?: string;
};

// ---------- Error type so pages can react to "wrong password" ----------
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit = {}, adminPassword?: string): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (adminPassword) headers["X-Admin-Password"] = adminPassword;

  const response = await fetch(`${API_URL}${path}`, { ...options, headers: { ...headers, ...options.headers } });
  if (!response.ok) {
    throw new ApiError(response.status, `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

// ---------- Public (customer) ----------
export function getListings(type?: string, purpose?: string) {
  const query = new URLSearchParams();
  if (type) query.set("type", type);
  if (purpose) query.set("purpose", purpose);
  const suffix = query.toString() ? `?${query}` : "";
  return request<Listing[]>(`/listings${suffix}`);
}

export async function sendChat(userId: string, threadId: string, message: string): Promise<ChatResult> {
  // /chat returns the same JSON shape even for errors (422/429), so read it either way.
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, thread_id: threadId, message }),
  });
  return response.json() as Promise<ChatResult>;
}

// ---------- Admin (needs the password) ----------
export const admin = {
  login: (password: string) => request<{ ok: boolean }>("/admin/login", { method: "POST" }, password),
  stats: (password: string) => request<Stats>("/admin/stats", {}, password),
  leads: (password: string) => request<Lead[]>("/admin/leads", {}, password),
  updateLeadStage: (password: string, leadId: number, stage: Stage) =>
    request<Lead>(`/admin/leads/${leadId}`, { method: "PATCH", body: JSON.stringify({ stage }) }, password),
  visits: (password: string) => request<Visit[]>("/admin/visits", {}, password),
  followUps: (password: string) => request<FollowUp[]>("/admin/follow-ups", {}, password),
  chats: (password: string) => request<ChatLog[]>("/admin/chats?limit=200", {}, password),
  addListing: (password: string, listing: NewListing) =>
    request<Listing>("/admin/listings", { method: "POST", body: JSON.stringify(listing) }, password),
};

// ---------- Small formatting helpers ----------
export function formatPkr(amount: number | null | undefined): string {
  if (amount == null) return "-";
  if (amount >= 10_000_000) return `${+(amount / 10_000_000).toFixed(2)} crore`;
  if (amount >= 100_000) return `${+(amount / 100_000).toFixed(2)} lakh`;
  return amount.toLocaleString("en-PK");
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-PK", { dateStyle: "medium", timeStyle: "short" });
}
