import { createFileRoute, Link } from "@tanstack/react-router";
import { CapsuleVisual } from "@/components/site/CapsuleVisual";
import { ArrowRight, Scan, Bell, Radar, ChevronRight } from "lucide-react";

export const Route = createFileRoute("/")({
  component: HomePage,
});

const stats = [
  { value: "50k+", label: "Banned Drugs Tracked" },
  { value: "3", label: "Major Authorities" },
  { value: "100%", label: "Source Transparency" },
];

const whyCards = [
  {
    icon: Scan,
    tint: "from-primary/25 to-primary/5 border-primary/30 text-primary",
    title: "Multi-Authority Check",
    desc: "Every query is cross-referenced against CDSCO, US FDA and WHO GSMS records in the same pass.",
  },
  {
    icon: Bell,
    tint: "from-danger/25 to-danger/5 border-danger/30 text-danger",
    title: "Instant Safety Alerts",
    desc: "Unsafe matches trigger a full-screen alert with authority, batch and reason — not a passive toast.",
  },
  {
    icon: Radar,
    tint: "from-capsule-blue/25 to-capsule-blue/5 border-capsule-blue/30 text-capsule-blue",
    title: "Real-Time Analysis",
    desc: "Regulatory feeds are ingested continuously so results reflect today's enforcement, not last quarter's.",
  },
];

function HomePage() {
  return (
    <>
      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-dots opacity-60" />
        <div className="pointer-events-none absolute -top-40 left-1/2 h-[520px] w-[820px] -translate-x-1/2 rounded-full bg-primary/10 blur-[120px]" />

        <div className="relative mx-auto grid max-w-7xl items-center gap-16 px-6 pb-24 pt-20 md:grid-cols-2 md:pt-28">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/5 px-3 py-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-pulse-dot absolute inset-0 rounded-full bg-primary" />
              </span>
              <span className="mono-label text-primary">Live Regulatory Updates Active</span>
            </span>

            <h1 className="mt-6 font-display text-5xl font-bold leading-[1.05] tracking-tight md:text-6xl">
              Verify Medicines.
              <br />
              Protect <span className="text-teal-gradient">Lives.</span>
            </h1>

            <p className="mt-6 max-w-lg text-base leading-relaxed text-muted-foreground md:text-lg">
              A regulatory-grade verification layer for prescribers, pharmacists and patients —
              powered by live records from CDSCO, US FDA and WHO GSMS.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                to="/verify"
                className="group inline-flex items-center gap-2 rounded-md bg-primary px-5 py-3 font-medium text-primary-foreground shadow-[0_0_0_1px_rgba(78,230,184,0.4),0_20px_50px_-20px_rgba(18,185,129,0.9)] transition-transform hover:-translate-y-0.5"
              >
                Verify Medicine Now
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
              <Link
                to="/how-it-works"
                className="inline-flex items-center gap-2 rounded-md border border-hairline bg-surface/60 px-5 py-3 font-medium text-foreground/90 transition-colors hover:border-primary/40 hover:text-primary"
              >
                How It Works
              </Link>
            </div>

            <div className="mt-12 grid grid-cols-3 gap-6 border-t border-hairline pt-8">
              {stats.map((s) => (
                <div key={s.label}>
                  <div className="font-mono text-2xl font-semibold text-foreground md:text-3xl">
                    {s.value}
                  </div>
                  <div className="mono-label mt-1 text-muted-foreground">{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="relative flex justify-center md:justify-end">
            <CapsuleVisual />
          </div>
        </div>
      </section>

      {/* WHY */}
      <section className="relative mx-auto max-w-7xl px-6 py-24">
        <div className="mx-auto max-w-2xl text-center">
          <span className="mono-label text-primary">/ Why SafeMeds AI</span>
          <h2 className="mt-3 font-display text-3xl font-bold md:text-4xl">
            Built for the moment you can't afford to be wrong
          </h2>
          <p className="mt-4 text-muted-foreground">
            Three primitives sit under every check — authority coverage, alert velocity, and
            analytical transparency.
          </p>
        </div>

        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {whyCards.map(({ icon: Icon, title, desc, tint }) => (
            <div
              key={title}
              className="card-hover group relative overflow-hidden rounded-xl border border-hairline bg-surface p-7"
            >
              <div
                className={`grid h-12 w-12 place-items-center rounded-lg border bg-gradient-to-br ${tint}`}
              >
                <Icon className="h-5 w-5" strokeWidth={2} />
              </div>
              <h3 className="mt-5 font-display text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{desc}</p>
              <div className="pointer-events-none absolute inset-x-0 -bottom-px h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-6 pb-24">
        <div className="relative overflow-hidden rounded-2xl border border-hairline bg-gradient-to-br from-surface via-surface-2 to-background p-10 md:p-16">
          <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary/20 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-24 left-1/3 h-72 w-72 rounded-full bg-capsule-blue/15 blur-3xl" />
          <div className="relative mx-auto max-w-2xl text-center">
            <span className="mono-label text-primary">/ Start Verifying</span>
            <h2 className="mt-3 font-display text-3xl font-bold md:text-4xl">
              Ready to verify your medicine?
            </h2>
            <p className="mt-4 text-muted-foreground">
              Run a check in under three seconds. No account, no PII, no dark patterns.
            </p>
            <Link
              to="/verify"
              className="mt-8 inline-flex items-center gap-2 rounded-md bg-primary px-6 py-3 font-medium text-primary-foreground shadow-[0_20px_50px_-20px_rgba(18,185,129,0.9)] transition-transform hover:-translate-y-0.5"
            >
              Start Verification
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
