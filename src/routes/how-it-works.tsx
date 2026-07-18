import { createFileRoute } from "@tanstack/react-router";
import { Search, Network, ShieldCheck, FileCheck } from "lucide-react";

export const Route = createFileRoute("/how-it-works")({
  head: () => ({
    meta: [
      { title: "How It Works — MedVerify" },
      {
        name: "description",
        content: "The four-step verification pipeline behind every MedVerify query.",
      },
      { property: "og:title", content: "How It Works — MedVerify" },
      { property: "og:description", content: "Query → Cross-reference → Classify → Return." },
    ],
  }),
  component: HowPage,
});

const steps = [
  {
    icon: Search,
    title: "Query",
    desc: "Enter a molecule, brand or batch — hashed locally before it leaves your device.",
  },
  {
    icon: Network,
    title: "Cross-Reference",
    desc: "The query hits CDSCO, US FDA and WHO GSMS in parallel, with retries for stale feeds.",
  },
  {
    icon: ShieldCheck,
    title: "Classify",
    desc: "Matches are graded: Safe (no records), Unknown (no definitive record), Unsafe (active enforcement).",
  },
  {
    icon: FileCheck,
    title: "Return",
    desc: "You get the authority, the record ID and the citation link — every claim is auditable.",
  },
];

function HowPage() {
  return (
    <section className="relative mx-auto max-w-6xl px-6 py-24">
      <div className="mx-auto max-w-2xl text-center">
        <span className="mono-label text-primary">/ Pipeline</span>
        <h1 className="mt-3 font-display text-4xl font-bold md:text-5xl">
          Four steps, zero prediction
        </h1>
        <p className="mt-4 text-muted-foreground">
          MedVerify never guesses. It reports what regulators have on record — and cites where it
          came from.
        </p>
      </div>

      <ol className="mt-16 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {steps.map(({ icon: Icon, title, desc }, i) => (
          <li key={title} className="relative rounded-xl border border-hairline bg-surface p-7">
            <div className="mono-label text-primary/70">Step 0{i + 1}</div>
            <div className="mt-4 grid h-12 w-12 place-items-center rounded-lg border border-primary/30 bg-primary/10 text-primary">
              <Icon className="h-5 w-5" />
            </div>
            <h3 className="mt-5 font-display text-lg font-semibold">{title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{desc}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
