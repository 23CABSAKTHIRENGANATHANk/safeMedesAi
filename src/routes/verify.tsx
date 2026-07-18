import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Camera, ShieldCheck, ShieldAlert, ShieldQuestion, X, Loader2 } from "lucide-react";
import { useVerifyMedicine } from "../hooks/useVerify";
import { Result } from "../services/api";

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
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);

  const verifyMutation = useVerifyMedicine();
  const loading = verifyMutation.isPending;

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setError(null);
    setResult(null);
    verifyMutation.mutate(
      {
        name: name.trim(),
        manufacturer: manufacturer.trim() || undefined,
        batch: batch.trim() || undefined,
      },
      {
        onSuccess: (data) => {
          setResult(data);
        },
        onError: (error) => {
          setError(error instanceof Error ? error.message : String(error));
        },
      },
    );
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
          {loading && (
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
              <div className="animate-scan absolute inset-x-0 h-24 bg-gradient-to-b from-transparent via-primary/25 to-transparent" />
            </div>
          )}

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
              disabled={loading || !name.trim()}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-3 font-medium text-primary-foreground shadow-[0_0_0_1px_rgba(78,230,184,0.4),0_20px_50px_-20px_rgba(18,185,129,0.9)] transition disabled:opacity-60"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Scanning authorities…
                </>
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4" />
                  Verify Medicine
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-6 rounded-xl border border-red-400/40 bg-red-500/5 p-5 text-sm text-red-700">
            <strong>Verification failed:</strong> {error}
          </div>
        )}

        {result && result.status === "warning" && (
          <div className="mt-8 rounded-xl border border-amber-500/60 bg-amber-500/10 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] bg-amber-500/20 text-amber-500">
                CAUTION
              </div>
              <div className="text-sm text-muted-foreground">
                Falsified/counterfeit version detected in circulation
              </div>
            </div>
            <div className="flex items-start gap-4">
              <ShieldQuestion className="h-6 w-6 text-amber-400 mt-1 shrink-0" />
              <div>
                <div className="mono-label text-amber-500">Warning · Counterfeit Alert</div>
                <h3 className="mt-1 font-display text-xl font-semibold">{result.name}</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {
                    "A falsified or counterfeit version of this medicine has been detected in the market. "
                  }
                  {
                    "The legitimate medicine is approved, but you should verify the source carefully."
                  }
                </p>
                {result.reason && (
                  <p className="mt-3 rounded-md bg-amber-500/10 border border-amber-500/30 p-3 text-sm text-amber-700 dark:text-amber-200">
                    {result.reason}
                  </p>
                )}
                {result.authority && (
                  <p className="mt-2 text-xs text-muted-foreground">Source: {result.authority}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {result && result.status !== "unsafe" && result.status !== "warning" && (
          <div
            className={`mt-8 rounded-xl border p-6 ${
              result.status === "safe"
                ? "border-primary/40 bg-primary/5"
                : "border-amber-500/40 bg-amber-500/5"
            }`}
          >
            <div className="flex items-center gap-3">
              <div
                className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${
                  result.status === "safe"
                    ? "bg-emerald-500/10 text-emerald-500"
                    : "bg-amber-500/10 text-amber-500"
                }`}
              >
                {result.status}
              </div>
              <div className="text-sm text-muted-foreground">
                {result.status === "safe"
                  ? "No active recalls or alerts found for this medicine."
                  : "No authoritative match found in current regulatory sources."}
              </div>
            </div>
            <div className="flex items-start gap-4">
              {result.status === "safe" ? (
                <ShieldCheck className="h-6 w-6 text-primary" />
              ) : (
                <ShieldQuestion className="h-6 w-6 text-amber-400" />
              )}
              <div>
                <div className="mono-label text-muted-foreground">
                  {result.status === "safe"
                    ? "Verified · No Adverse Records"
                    : "No Definitive Record"}
                </div>
                <h3 className="mt-1 font-display text-xl font-semibold">{result.name}</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {result.status === "safe"
                    ? "This medicine was checked against current CDSCO, US FDA, and WHO GSMS records and returned no active matches."
                    : "This query does not match an authoritative record in current regulatory sources; it may be unlisted or require manual review."}
                </p>
                {result.reason && (
                  <p className="mt-3 rounded-md bg-surface p-3 text-sm text-foreground/90">
                    {result.reason}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {result?.status === "unsafe" && (
        <UnsafeAlert result={result} onClose={() => setResult(null)} />
      )}
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

function UnsafeAlert({ result, onClose }: { result: Result; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-background/95 backdrop-blur-md p-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(240,69,90,0.25),transparent_60%)]" />
      <div className="pointer-events-none absolute inset-0 border-[3px] border-danger/60 animate-pulse" />
      <div className="relative w-full max-w-xl rounded-2xl border-2 border-danger bg-surface p-8 shadow-[0_0_80px_-10px_rgba(240,69,90,0.7)]">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-md p-1.5 text-muted-foreground hover:bg-hairline hover:text-foreground"
        >
          <X className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-3">
          <div className="grid h-12 w-12 place-items-center rounded-full border border-danger/60 bg-danger/15">
            <ShieldAlert className="h-6 w-6 text-danger" />
          </div>
          <div className="mono-label text-danger">Unsafe Match · Do Not Consume</div>
        </div>

        <h2 className="mt-6 font-display text-3xl font-bold text-foreground">{result.name}</h2>
        {result.batch && (
          <p className="mono-label mt-1 text-muted-foreground">Batch · {result.batch}</p>
        )}

        <div className="mt-6 space-y-3 rounded-lg border border-danger/30 bg-danger/5 p-5">
          <Row k="Authority" v={result.authority || "CDSCO"} />
          <Row k="Reason" v={result.reason || "Match found in active enforcement registry."} />
          <Row
            k="Recommended Action"
            v="Stop use immediately. Contact your pharmacist and report the batch."
          />
        </div>

        <div className="mt-6 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-md border border-hairline bg-surface-2 px-4 py-3 text-sm font-medium text-foreground hover:border-primary/40"
          >
            Close
          </button>
          <a
            href="#"
            className="flex-1 rounded-md bg-danger px-4 py-3 text-center text-sm font-medium text-destructive-foreground hover:opacity-95"
          >
            Report This Batch
          </a>
        </div>
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="grid grid-cols-3 gap-3 text-sm">
      <div className="mono-label text-danger/80">{k}</div>
      <div className="col-span-2 text-foreground/90">{v}</div>
    </div>
  );
}
