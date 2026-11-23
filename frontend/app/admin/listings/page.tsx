"use client";

import { useState } from "react";
import AdminShell from "@/components/AdminShell";
import { admin, formatPkr, getListings, type NewListing } from "@/lib/api";
import { useAdminData } from "@/lib/useAdmin";

const EMPTY_FORM = {
  type: "property", purpose: "sale", title: "", city: "Islamabad", area: "",
  size_label: "", size_marla: "", price_pkr: "", bedrooms: "", description: "",
};

export default function AdminListingsPage() {
  const { password, data: listings, error, reload } = useAdminData(() => getListings());
  const [form, setForm] = useState(EMPTY_FORM);
  const [message, setMessage] = useState("");

  // One function updates any form field by its name.
  function update(field: keyof typeof EMPTY_FORM, value: string) {
    setForm((old) => ({ ...old, [field]: value }));
  }

  async function addListing(event: React.FormEvent) {
    event.preventDefault();
    if (!password) return;
    const listing: NewListing = {
      type: form.type as NewListing["type"],
      purpose: form.purpose as NewListing["purpose"],
      title: form.title,
      city: form.city,
      area: form.area,
      price_pkr: Number(form.price_pkr),
      size_label: form.size_label || undefined,
      size_marla: form.size_marla ? Number(form.size_marla) : undefined,
      bedrooms: form.bedrooms ? Number(form.bedrooms) : undefined,
      description: form.description || undefined,
    };
    try {
      const created = await admin.addListing(password, listing);
      setMessage(`✅ Added #${created.id}. The agent can find it right away.`);
      setForm(EMPTY_FORM);
      reload();
    } catch {
      setMessage("❌ Could not add the listing. Check the fields and try again.");
    }
  }

  const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500";

  return (
    <AdminShell title="Listings">
      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
          {error && <p className="p-4 text-red-600">{error}</p>}
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="p-3">#</th>
                <th className="p-3">Title</th>
                <th className="p-3">Area</th>
                <th className="p-3">Size</th>
                <th className="p-3">Price</th>
                <th className="p-3">Purpose</th>
              </tr>
            </thead>
            <tbody>
              {(listings ?? []).map((listing) => (
                <tr key={listing.id} className="border-t border-slate-100">
                  <td className="p-3 font-semibold">#{listing.id}</td>
                  <td className="p-3">{listing.type === "car" ? "🚗" : "🏡"} {listing.title}</td>
                  <td className="p-3">{listing.area}, {listing.city}</td>
                  <td className="p-3">{listing.size_label ?? "-"}</td>
                  <td className="p-3">PKR {formatPkr(listing.price_pkr)}</td>
                  <td className="p-3">{listing.purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <form onSubmit={addListing} className="h-fit space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
          <h2 className="font-semibold">➕ Add a listing</h2>
          <div className="grid grid-cols-2 gap-2">
            <select value={form.type} onChange={(e) => update("type", e.target.value)} className={input}>
              <option value="property">Property</option>
              <option value="car">Car</option>
            </select>
            <select value={form.purpose} onChange={(e) => update("purpose", e.target.value)} className={input}>
              <option value="sale">For sale</option>
              <option value="rent">For rent</option>
            </select>
          </div>
          <input required minLength={3} placeholder="Title, e.g. 10 Marla House" value={form.title} onChange={(e) => update("title", e.target.value)} className={input} />
          <div className="grid grid-cols-2 gap-2">
            <input required placeholder="City" value={form.city} onChange={(e) => update("city", e.target.value)} className={input} />
            <input required placeholder="Area / sector" value={form.area} onChange={(e) => update("area", e.target.value)} className={input} />
          </div>
          <input required type="number" min={1} placeholder="Price in PKR, e.g. 30000000" value={form.price_pkr} onChange={(e) => update("price_pkr", e.target.value)} className={input} />
          <div className="grid grid-cols-3 gap-2">
            <input placeholder="Size label" value={form.size_label} onChange={(e) => update("size_label", e.target.value)} className={input} />
            <input type="number" step="0.5" placeholder="Marla" value={form.size_marla} onChange={(e) => update("size_marla", e.target.value)} className={input} />
            <input type="number" placeholder="Beds" value={form.bedrooms} onChange={(e) => update("bedrooms", e.target.value)} className={input} />
          </div>
          <textarea placeholder="Short description" value={form.description} onChange={(e) => update("description", e.target.value)} className={input} rows={3} />
          <button className="w-full rounded-xl bg-emerald-600 py-2 font-semibold text-white">Add listing</button>
          {message && <p className="text-sm">{message}</p>}
        </form>
      </div>
    </AdminShell>
  );
}
