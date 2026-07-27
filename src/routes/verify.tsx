import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ShieldCheck } from "lucide-react";

export const Route = createFileRoute("/verify")({
  head: () => ({
    meta: [
      { title: "Verify Medicine — MedVerify" },
      {
        name: "description",
        content: "Run a secure verification against CDSCO, US FDA and WHO GSMS.",
      },
      { property: "og:title", content: "Verify Medicine — MedVerify" },
      { property: "og:description", content: "Secure Medicine Verification Terminal." },
    ],
  }),
  component: VerifyPage,
});

function VerifyPage() {
  const [name, setName] = useState("");
  const [manufacturer, setManufacturer] = useState("");
  const [batch, setBatch] = useState("");
  const navigate = useNavigate();

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    navigate({
      to: "/verify-result",
      search: {
        name: name.trim(),
        manufacturer: manufacturer.trim() || undefined,
        batch: batch.trim() || undefined,
      },
    });
  }

  return (
    <section className="relative min-h-[calc(100vh-4rem)]">
      <div className="absolute inset-0 bg-starfield opacity-70" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-gradient-to-b from-primary/10 via-transparent to-transparent" />

      <div className="relative mx-auto max-w-3xl px-6 py-20">
        <div className="text-center">
          <span className="mono-label text-primary">/ Terminal · Session Active</span>
          <h1 className="mt-3 font-display text-3xl font-bold md:text-5xl">
            Secure Medicine Verification Terminal
          </h1>
          <p className="mt-4 text-muted-foreground">
            All queries are hashed locally. Nothing personal leaves your device.
          </p>
        </div>

        <form
          onSubmit={onSubmit}
          className="glass-panel relative mt-12 overflow-hidden rounded-2xl p-8 md:p-10"
        >
          <div className="mb-6 flex items-center justify-between">
            <div className="mono-label text-muted-foreground">Query · v1</div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-danger/80" />
              <span className="h-2 w-2 rounded-full bg-amber-400/80" />
              <span className="h-2 w-2 rounded-full bg-primary" />
            </div>
          </div>

          <div className="space-y-5">
            <Field label="Medicine Name / Molecule" required>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Amoxicillin"
                className="w-full rounded-md border border-hairline bg-background/60 px-4 py-3 text-foreground placeholder:text-muted-foreground/60 outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/20"
              />
            </Field>
            <div className="grid gap-5 md:grid-cols-2">
              <Field label="Manufacturer">
                <input
                  value={manufacturer}
                  onChange={(e) => setManufacturer(e.target.value)}
                  placeholder="Optional"
                  className="w-full rounded-md border border-hairline bg-background/60 px-4 py-3 outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20"
                />
              </Field>
              <Field label="Batch Number">
                <input
                  value={batch}
                  onChange={(e) => setBatch(e.target.value)}
                  placeholder="Optional"
                  className="w-full rounded-md border border-hairline bg-background/60 px-4 py-3 font-mono outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20"
                />
              </Field>
            </div>
          </div>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={!name.trim()}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-3 font-medium text-primary-foreground shadow-[0_0_0_1px_rgba(78,230,184,0.4),0_20px_50px_-20px_rgba(18,185,129,0.9)] transition disabled:opacity-60"
            >
              <ShieldCheck className="h-4 w-4" />
              Verify Medicine
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mono-label text-muted-foreground">
        {label} {required && <span className="text-primary">*</span>}
      </span>
      <div className="mt-2">{children}</div>
    </label>
  );
}


