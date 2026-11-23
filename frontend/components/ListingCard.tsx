import { formatPkr, type Listing } from "@/lib/api";

type Props = {
  listing: Listing;
  onAsk: (listing: Listing) => void; // "Ask agent" button puts a question in the chat box
};

export default function ListingCard({ listing, onAsk }: Props) {
  const isCar = listing.type === "car";
  const isRent = listing.purpose === "rent";

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <span className="text-3xl">{isCar ? "🚗" : listing.bedrooms ? "🏡" : "📐"}</span>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">#{listing.id}</span>
      </div>
      <h3 className="mt-2 font-semibold leading-snug">{listing.title}</h3>
      <p className="text-sm text-slate-500">
        {listing.area}, {listing.city}
      </p>
      <div className="mt-2 flex flex-wrap gap-1 text-xs">
        {listing.size_label && <span className="rounded bg-slate-100 px-2 py-0.5">{listing.size_label}</span>}
        {listing.bedrooms && <span className="rounded bg-slate-100 px-2 py-0.5">{listing.bedrooms} bed</span>}
        <span className={`rounded px-2 py-0.5 ${isRent ? "bg-sky-100 text-sky-800" : "bg-emerald-100 text-emerald-800"}`}>
          {isRent ? "For rent" : "For sale"}
        </span>
      </div>
      <p className="mt-3 text-lg font-bold text-slate-900">
        PKR {formatPkr(listing.price_pkr)}
        {isRent && <span className="text-sm font-normal text-slate-500"> /month</span>}
      </p>
      <button
        onClick={() => onAsk(listing)}
        className="mt-3 rounded-lg border border-emerald-600 px-3 py-1.5 text-sm font-medium text-emerald-700 hover:bg-emerald-50"
      >
        {isCar ? "Ask about a test drive" : "Ask about this"}
      </button>
    </div>
  );
}
