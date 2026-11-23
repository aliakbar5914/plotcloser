import Link from "next/link";
import Navbar from "@/components/Navbar";

// Landing page: the business pitch. No data or clicks to handle, so it stays a
// Server Component (rendered to plain HTML = fast, no "use client" needed).

const STEPS = [
  { icon: "💬", title: "Lead messages", text: "A buyer asks about a house or car, day or night, in English or Roman Urdu." },
  { icon: "🔎", title: "Agent matches", text: "PlotCloser searches your real listings and recommends the best options." },
  { icon: "🎯", title: "Lead is scored", text: "Budget, timeline and payment are asked naturally and scored Hot, Warm or Cold." },
  { icon: "📅", title: "Visit booked", text: "Site visits and test drives are booked only after the customer confirms." },
];

const FEATURES = [
  "Replies in seconds, 24/7",
  "Houses, plots, rentals and used cars",
  "Remembers returning customers",
  "Asks before any booking",
  "Refuses off-topic and trick requests",
  "Lead pipeline dashboard for your team",
];

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        {/* Hero */}
        <section className="bg-gradient-to-b from-emerald-50 to-slate-50">
          <div className="mx-auto max-w-6xl px-4 py-20 text-center">
            <p className="mb-4 inline-block rounded-full bg-emerald-100 px-4 py-1 text-sm font-medium text-emerald-800">
              For real estate agents & car dealers in Islamabad / Rawalpindi
            </p>
            <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
              Never lose a lead to a slow reply again.
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-lg text-slate-600">
              PlotCloser is an AI sales agent that answers every property and car enquiry in seconds, qualifies the
              buyer and books the site visit, while your team focuses on closing.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link href="/listings" className="rounded-xl bg-emerald-600 px-6 py-3 font-semibold text-white shadow hover:bg-emerald-700">
                💬 Chat with the agent
              </Link>
              <Link href="/admin" className="rounded-xl border border-slate-300 bg-white px-6 py-3 font-semibold text-slate-800 hover:bg-slate-100">
                See the agency dashboard
              </Link>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="mb-8 text-center text-2xl font-bold">How it works</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((step, index) => (
              <div key={step.title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="text-3xl">{step.icon}</div>
                <p className="mt-3 text-xs font-semibold text-emerald-700">STEP {index + 1}</p>
                <h3 className="font-semibold">{step.title}</h3>
                <p className="mt-1 text-sm text-slate-600">{step.text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Features + pricing */}
        <section className="mx-auto grid max-w-6xl gap-6 px-4 pb-20 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold">Why agencies use PlotCloser</h2>
            <ul className="mt-4 space-y-2">
              {FEATURES.map((feature) => (
                <li key={feature} className="flex gap-2 text-slate-700">
                  <span className="text-emerald-600">✔</span> {feature}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl bg-slate-900 p-6 text-white shadow-sm">
            <h2 className="text-xl font-bold">Simple pricing</h2>
            <p className="mt-4 text-4xl font-bold">
              Rs 5,000<span className="text-base font-normal text-slate-300"> / month per agency</span>
            </p>
            <p className="mt-2 text-slate-300">or Rs 1,000 per booked site visit. 7-day free trial.</p>
            <p className="mt-6 text-sm text-slate-400">
              One closed plot deal pays for years of PlotCloser. Every unanswered lead is ad money wasted.
            </p>
          </div>
        </section>
      </main>
      <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-500">
        PlotCloser · Group G37 · AI-4016 Agentic AI, Design to Production
      </footer>
    </>
  );
}
