"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import ListingCard from "@/components/ListingCard";
import Navbar from "@/components/Navbar";
import { getListings, type Listing } from "@/lib/api";

// The chat uses localStorage (browser only), so never render it on the server.
const ChatPanel = dynamic(() => import("@/components/ChatPanel"), {
  ssr: false,
  loading: () => <div className="h-[480px] animate-pulse rounded-2xl bg-white ring-1 ring-slate-200" />,
});

// Filter tabs: each one decides which listings are shown.
const FILTERS: { label: string; match: (listing: Listing) => boolean }[] = [
  { label: "All", match: () => true },
  { label: "Houses", match: (l) => l.type === "property" && l.purpose === "sale" && !!l.bedrooms },
  { label: "Plots", match: (l) => l.type === "property" && l.purpose === "sale" && !l.bedrooms },
  { label: "For rent", match: (l) => l.purpose === "rent" },
  { label: "Cars", match: (l) => l.type === "car" },
];

export default function ListingsPage() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filterIndex, setFilterIndex] = useState(0);
  const [prefill, setPrefill] = useState<{ text: string; nonce: number }>();

  // Load listings once when the page opens.
  useEffect(() => {
    getListings()
      .then(setListings)
      .catch(() => setError("Could not load listings. Please refresh the page."))
      .finally(() => setLoading(false));
  }, []);

  const visible = listings.filter(FILTERS[filterIndex].match);

  function askAbout(listing: Listing) {
    const text =
      listing.type === "car"
        ? `I'm interested in #${listing.id} ${listing.title}. Can I book a test drive?`
        : `Tell me more about #${listing.id} ${listing.title} in ${listing.area}.`;
    setPrefill({ text, nonce: Date.now() }); // nonce makes the same text work twice
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto grid w-full max-w-6xl flex-1 gap-6 px-4 py-6 lg:grid-cols-[1fr_380px]">
        {/* Left: listings */}
        <section>
          <h1 className="text-2xl font-bold">Available listings</h1>
          <p className="text-sm text-slate-500">Capital Estates · Islamabad & Rawalpindi</p>

          <div className="mt-4 flex flex-wrap gap-2">
            {FILTERS.map((filter, index) => (
              <button
                key={filter.label}
                onClick={() => setFilterIndex(index)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium ${
                  index === filterIndex ? "bg-slate-900 text-white" : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-100"
                }`}
              >
                {filter.label} ({listings.filter(filter.match).length})
              </button>
            ))}
          </div>

          {loading && <p className="mt-6 text-slate-500">Loading listings…</p>}
          {error && <p className="mt-6 text-red-600">{error}</p>}

          <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {visible.map((listing) => (
              <ListingCard key={listing.id} listing={listing} onAsk={askAbout} />
            ))}
          </div>
        </section>

        {/* Right: chat (sticks to the screen while you scroll) */}
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <ChatPanel prefill={prefill} />
        </aside>
      </main>
    </>
  );
}
