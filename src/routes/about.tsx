import { createFileRoute } from "@tanstack/react-router";
import { ShieldCheck, Quote } from "lucide-react";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About — MedVerify" },
      {
        name: "description",
        content: "Our data integrity policy: no prediction, only definitive regulatory records.",
      },
      { property: "og:title", content: "About — MedVerify" },
      { property: "og:description", content: "The No Prediction policy behind MedVerify." },
    ],
  }),
  component: AboutPage,
});

function AboutPage() {
  return (
    <section className="relative mx-auto max-w-4xl px-6 py-24">
      <div>
        <span className="mono-label text-primary">/ Our Data Integrity</span>
        <h1 className="mt-3 font-display text-4xl font-bold md:text-5xl">
          The No-Prediction Policy
        </h1>
      </div>

      <div className="glass-panel mt-10 rounded-2xl p-8 md:p-10">
        <div className="flex items-start gap-4">
          <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-primary/30 bg-primary/10 text-primary">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-display text-xl font-semibold">
              Only definitive records classify a medicine as unsafe
            </h2>
            <p className="mt-3 leading-relaxed text-muted-foreground">
              MedVerify will never flag a medicine on similarity, statistical inference or
              crowd-sourced sentiment. A medicine is only classified{" "}
              <span className="text-danger">Unsafe</span> when a definitive record exists in at
              least one of three authorities — <span className="text-primary">CDSCO</span> (India),{" "}
              <span className="text-primary">US FDA</span> Enforcement Reports, or the{" "}
              <span className="text-primary">WHO Global Surveillance & Monitoring System</span>. In
              every other case we return <span className="text-foreground">Safe</span> (no matching
              record) or <span className="text-foreground">Unknown</span> (insufficient data) —
              never a guess.
            </p>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {["CDSCO", "US FDA", "WHO GSMS"].map((a) => (
                <div key={a} className="rounded-lg border border-hairline bg-surface-2 px-4 py-3">
                  <div className="mono-label text-primary">{a}</div>
                  <div className="mt-1 text-xs text-muted-foreground">Live enforcement feed</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <figure className="relative mt-12 overflow-hidden rounded-2xl border border-hairline bg-gradient-to-br from-surface to-background p-10">
        <Quote className="absolute right-6 top-6 h-14 w-14 text-primary/15" />
        <blockquote className="font-display text-2xl leading-snug text-foreground md:text-3xl">
          "We refused to build a black-box classifier. If we can't cite the regulator, we don't call
          it unsafe. That constraint is the product."
        </blockquote>
        <figcaption className="mt-8 flex items-center gap-4">
          <div className="grid h-12 w-12 place-items-center rounded-full border border-primary/40 bg-gradient-to-br from-primary/30 to-primary/5 font-display text-lg font-bold text-primary">
            AK
          </div>
          <div>
            <div className="font-medium text-foreground">Aditi Krishnan</div>
            <div className="mono-label text-muted-foreground">
              Head of Data Integrity · MedVerify
            </div>
          </div>
        </figcaption>
      </figure>
    </section>
  );
}
