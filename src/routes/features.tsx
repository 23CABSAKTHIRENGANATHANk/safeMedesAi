import { createFileRoute } from "@tanstack/react-router";
import { ShieldCheck, Bell, Database, Truck, Lock, Smartphone } from "lucide-react";

export const Route = createFileRoute("/features")({
  head: () => ({
      meta: [
      { title: "Features — MedVerify" },
      {
        name: "description",
        content: "Multi-authority verification, safety alerts, supply chain tracking and more.",
      },
      { property: "og:title", content: "Features — MedVerify" },
      { property: "og:description", content: "The full feature surface of MedVerify." },
    ],
  }),
  component: FeaturesPage,
});

const features = [
  {
    icon: ShieldCheck,
    title: "Multi-Authority Verification",
    desc: "One query hits CDSCO, US FDA and WHO GSMS simultaneously — no manual cross-referencing.",
  },
  {
    icon: Bell,
    title: "Real-Time Safety Alerts",
    desc: "Unsafe hits open a full-screen alert with the offending batch, authority and mitigation steps.",
  },
  {
    icon: Database,
    title: "Comprehensive Drug Database",
    desc: "50,000+ tracked entries — expired approvals, recalled batches and banned molecules included.",
  },
  {
    icon: Truck,
    title: "Global Supply Chain Tracking",
    desc: "Trace a batch's origin, importer and distributor path across borders where data is public.",
  },
  {
    icon: Lock,
    title: "Privacy-First Architecture",
    desc: "No accounts, no PII collection, no persistent logs. Queries are hashed at the edge.",
  },
  {
    icon: Smartphone,
    title: "Mobile-First Design",
    desc: "Optimized for the pharmacy counter — one-handed use, high-contrast readouts, offline recall.",
  },
];

function FeaturesPage() {
  return (
    <section className="relative mx-auto max-w-7xl px-6 py-24">
      <div className="mx-auto max-w-2xl text-center">
        <span className="mono-label text-primary">/ Feature Set</span>
        <h1 className="mt-3 font-display text-4xl font-bold md:text-5xl">
          Every check, fully instrumented
        </h1>
        <p className="mt-4 text-muted-foreground">
          A verification stack designed for regulatory posture, not marketing pages.
        </p>
      </div>

      <div className="mt-16 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {features.map(({ icon: Icon, title, desc }) => (
          <div
            key={title}
            className="card-hover group relative overflow-hidden rounded-xl border border-hairline bg-surface p-7"
          >
            <div className="grid h-12 w-12 place-items-center rounded-lg border border-primary/30 bg-gradient-to-br from-primary/20 to-primary/5 text-primary">
              <Icon className="h-5 w-5" />
            </div>
            <h3 className="mt-5 font-display text-lg font-semibold">{title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{desc}</p>
            <div className="pointer-events-none absolute inset-x-0 -bottom-px h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
          </div>
        ))}
      </div>
    </section>
  );
}
