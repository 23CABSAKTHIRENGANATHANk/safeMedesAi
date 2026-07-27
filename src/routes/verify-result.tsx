import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { 
  ShieldCheck, 
  ShieldAlert, 
  ShieldQuestion, 
  ChevronLeft, 
  Info, 
  AlertTriangle, 
  DollarSign, 
  Activity, 
  FileText, 
  ExternalLink,
  Sparkles,
  Loader2
} from "lucide-react";
import { verifyMedicine, VerifyPayload } from "../services/api";

// Define search parameters type for route validation
interface VerifyResultSearchParams {
  name: string;
  manufacturer?: string;
  batch?: string;
}

export const Route = createFileRoute("/verify-result")({
  validateSearch: (search: Record<string, unknown>): VerifyResultSearchParams => {
    return {
      name: (search.name as string) || "",
      manufacturer: (search.manufacturer as string) || undefined,
      batch: (search.batch as string) || undefined,
    };
  },
  component: VerifyResultPage,
});

interface FullMedicineDetails {
  medicine: {
    id: number | string;
    name: string;
    batch?: string;
    manufacturer?: string;
    status: string;
    authority?: string;
    reason?: string;
  };
  alerts: any[];
  recalls: any[];
  reports: any[];
  fda: any;
  ai_summary?: {
    purpose?: string;
    approval_status?: string;
    safety_alerts?: string[];
    recall_history?: string[];
    manufacturer?: string;
    risk_level?: string;
    reasoning?: string;
  };
}

// Fetch full medicine context (recalls, side effects, AI summary)
const fetchFullDetails = async (name: string): Promise<FullMedicineDetails> => {
  const res = await fetch(`/api/medicine/${encodeURIComponent(name)}`);
  if (!res.ok) {
    throw new Error("Failed to fetch clinical profiles");
  }
  return res.json();
};

function VerifyResultPage() {
  const search = Route.useSearch();
  const navigate = useNavigate();

  // Query 1: Safety verification (combines local SQLite + Supabase checks)
  const { 
    data: verifyResult, 
    isLoading: isVerifying, 
    error: verifyError 
  } = useQuery({
    queryKey: ["verify-medicine", search.name, search.batch, search.manufacturer],
    queryFn: () => verifyMedicine({
      name: search.name,
      batch: search.batch,
      manufacturer: search.manufacturer
    }),
    enabled: !!search.name,
  });

  // Query 2: Full details & clinical context (recalls, FDA labels, side effects, Gemini AI profiles)
  const {
    data: clinicalDetails,
    isLoading: isLoadingDetails,
  } = useQuery({
    queryKey: ["medicine-details", search.name],
    queryFn: () => fetchFullDetails(search.name),
    enabled: !!search.name,
  });

  const loading = isVerifying || isLoadingDetails;

  if (!search.name) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center p-6 text-center">
        <ShieldQuestion className="h-16 w-16 text-muted-foreground animate-pulse" />
        <h2 className="mt-4 font-display text-2xl font-bold">No Medicine Specified</h2>
        <p className="mt-2 text-muted-foreground">Please start a new verification scan.</p>
        <Link to="/verify" className="mt-6 inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 font-medium text-primary-foreground shadow-sm">
          <ChevronLeft className="h-4 w-4" /> Go to Verification Terminal
        </Link>
      </div>
    );
  }

  // Parse safety status (Safe, Warning, Unsafe, Unknown)
  const status = verifyResult?.status || "unknown";
  const authority = verifyResult?.authority || "Regulatory Record Cache";
  
  // Parse details formatted in 'reason' (price, composition, side effects)
  const reasonText = verifyResult?.reason || "";
  const parts = reasonText.split(" | ");
  
  let composition = "";
  let price = "";
  let sideEffectsText = "";
  let description = "";

  parts.forEach(part => {
    if (part.startsWith("Composition: ")) composition = part.substring(13);
    else if (part.startsWith("Price: ")) price = part.substring(7);
    else if (part.startsWith("Side Effects: ")) sideEffectsText = part.substring(14);
    else if (part.startsWith("Description: ")) description = part.substring(13);
  });

  // If reasonText doesn't match standard parsed format, treat the whole thing as description/reason
  if (!composition && !price && !sideEffectsText && !description) {
    description = reasonText;
  }

  // UI styling based on safety status
  const theme = {
    safe: {
      color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/5",
      glow: "shadow-[0_0_50px_-10px_rgba(16,185,129,0.2)]",
      badgeBg: "bg-emerald-500/20 text-emerald-400",
      title: "Verified · No Recall Found",
      desc: "This medicine matches valid regulatory reference data. No active recall notifications have been issued by the CDSCO, US FDA, or WHO GSMS.",
      icon: <ShieldCheck className="h-12 w-12 text-emerald-400" />
    },
    warning: {
      color: "text-amber-400 border-amber-500/30 bg-amber-500/5",
      glow: "shadow-[0_0_50px_-10px_rgba(245,158,11,0.25)]",
      badgeBg: "bg-amber-500/20 text-amber-400",
      title: "Caution · Counterfeit Alert",
      desc: "A falsified or counterfeit version of this medicine brand/batch has been detected in circulation. Purchase only from licensed pharmacies.",
      icon: <AlertTriangle className="h-12 w-12 text-amber-400" />
    },
    unsafe: {
      color: "text-red-400 border-red-500/30 bg-red-500/5",
      glow: "shadow-[0_0_50px_-10px_rgba(239,68,68,0.35)]",
      badgeBg: "bg-red-500/20 text-red-400",
      title: "Unsafe Match · Do Not Consume",
      desc: "This medicine has been flagged under active recalls, safety bans, or failed test parameters in official regulatory updates.",
      icon: <ShieldAlert className="h-12 w-12 text-red-400 animate-pulse" />
    },
    unknown: {
      color: "text-sky-400 border-sky-500/30 bg-sky-500/5",
      glow: "shadow-[0_0_50px_-10px_rgba(56,189,248,0.2)]",
      badgeBg: "bg-sky-500/20 text-sky-400",
      title: "Unlisted · Manual Review Required",
      desc: "No exact match was found in our loaded regulatory databases. Verify details directly with your pharmacist or doctor.",
      icon: <ShieldQuestion className="h-12 w-12 text-sky-400" />
    }
  }[status];

  return (
    <section className="relative min-h-[calc(100vh-4rem)] bg-background py-16 px-6">
      <div className="absolute inset-0 bg-starfield opacity-40 pointer-events-none" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-gradient-to-b from-primary/5 via-transparent to-transparent" />

      <div className="relative mx-auto max-w-4xl">
        {/* Back Button */}
        <Link 
          to="/verify" 
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition mb-8"
        >
          <ChevronLeft className="h-4 w-4" /> Back to Verification Terminal
        </Link>

        {loading ? (
          <div className="flex h-96 flex-col items-center justify-center text-center">
            <Loader2 className="h-12 w-12 text-primary animate-spin" />
            <p className="mt-4 text-muted-foreground animate-pulse font-mono">Analyzing regulatory records and clinical context...</p>
          </div>
        ) : verifyError ? (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-6 text-center">
            <AlertTriangle className="h-10 w-10 text-red-400 mx-auto" />
            <h3 className="mt-4 text-lg font-semibold">Verification Connection Failed</h3>
            <p className="mt-2 text-sm text-muted-foreground">{verifyError.message}</p>
          </div>
        ) : (
          <div className="space-y-8">
            
            {/* 1. Main Safety Banner */}
            <div className={`glass-panel border rounded-2xl p-8 flex flex-col md:flex-row gap-6 items-start md:items-center justify-between ${theme.color} ${theme.glow}`}>
              <div className="flex items-center gap-5">
                <div className="p-3 bg-background/40 rounded-xl border border-white/5">
                  {theme.icon}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className={`rounded-full px-3 py-0.5 text-xs font-semibold uppercase tracking-[0.1em] ${theme.badgeBg}`}>
                      {status}
                    </span>
                    <span className="text-xs text-muted-foreground">Source: {authority}</span>
                  </div>
                  <h1 className="mt-2 font-display text-2xl font-bold md:text-3xl text-foreground">
                    {search.name}
                  </h1>
                  <p className="mt-2 text-sm text-muted-foreground max-w-xl">
                    {theme.desc}
                  </p>
                </div>
              </div>
            </div>

            {/* 2. Medicine Properties & Composition */}
            <div className="grid gap-6 md:grid-cols-3">
              {/* Composition */}
              <div className="glass-panel border border-hairline rounded-xl p-5 bg-surface-2">
                <div className="flex items-center gap-2.5 text-primary mb-3">
                  <Activity className="h-4.5 w-4.5" />
                  <span className="mono-label">Active salt</span>
                </div>
                <div className="text-sm font-medium text-foreground">
                  {composition || "Generic / Unspecified Molecule"}
                </div>
              </div>

              {/* Price */}
              <div className="glass-panel border border-hairline rounded-xl p-5 bg-surface-2">
                <div className="flex items-center gap-2.5 text-primary mb-3">
                  <DollarSign className="h-4.5 w-4.5" />
                  <span className="mono-label">Indicative Price</span>
                </div>
                <div className="text-sm font-medium text-foreground">
                  {price ? `${price}` : "N/A"}
                </div>
              </div>

              {/* Batch & Manufacturer */}
              <div className="glass-panel border border-hairline rounded-xl p-5 bg-surface-2">
                <div className="flex items-center gap-2.5 text-primary mb-3">
                  <Info className="h-4.5 w-4.5" />
                  <span className="mono-label">Entity Details</span>
                </div>
                <div className="text-sm text-foreground space-y-1">
                  <div><span className="text-xs text-muted-foreground">Manufacturer:</span> {search.manufacturer || clinicalDetails?.medicine?.manufacturer || "Unknown"}</div>
                  {search.batch && <div><span className="text-xs text-muted-foreground">Batch:</span> <code className="text-xs font-mono">{search.batch}</code></div>}
                </div>
              </div>
            </div>

            {/* 3. Clinical Description / Heuristic Reasons */}
            {description && (
              <div className="glass-panel border border-hairline rounded-xl p-6 bg-surface">
                <h3 className="font-display text-lg font-semibold mb-3 flex items-center gap-2">
                  <FileText className="h-4.5 w-4.5 text-primary" /> Regulatory Overview
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                  {description}
                </p>
              </div>
            )}

            {/* 4. Side Effects & Cautions (Extracted from Dataset) */}
            {sideEffectsText && (
              <div className="glass-panel border border-amber-500/20 bg-amber-500/5 rounded-xl p-6">
                <h3 className="font-display text-lg font-semibold text-amber-400 mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-4.5 w-4.5" /> Side Effects & Safety Cautions
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {sideEffectsText}
                </p>
              </div>
            )}

            {/* 5. AI Profile & Deep-Dive clinical Summary (Gemini Powered) */}
            {clinicalDetails?.ai_summary && (
              <div className="glass-panel border border-primary/20 bg-primary/5 rounded-xl p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                  <Sparkles className="h-24 w-24 text-primary animate-pulse" />
                </div>
                <h3 className="font-display text-lg font-semibold text-primary mb-4 flex items-center gap-2">
                  <Sparkles className="h-4.5 w-4.5" /> AI Synthesized Clinical Profile
                </h3>
                
                <div className="space-y-4 text-sm relative z-10">
                  {clinicalDetails.ai_summary.purpose && (
                    <div>
                      <span className="text-xs text-muted-foreground uppercase tracking-wider block font-mono">Therapeutic Purpose</span>
                      <p className="mt-1 text-foreground leading-relaxed">{clinicalDetails.ai_summary.purpose}</p>
                    </div>
                  )}

                  {clinicalDetails.ai_summary.safety_alerts && clinicalDetails.ai_summary.safety_alerts.length > 0 && (
                    <div>
                      <span className="text-xs text-muted-foreground uppercase tracking-wider block font-mono">Safety Warnings</span>
                      <ul className="mt-1 list-disc pl-5 space-y-1 text-foreground">
                        {clinicalDetails.ai_summary.safety_alerts.map((alert, idx) => (
                          <li key={idx}>{alert}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {clinicalDetails.ai_summary.reasoning && (
                    <div>
                      <span className="text-xs text-muted-foreground uppercase tracking-wider block font-mono">Clinical Assessment</span>
                      <p className="mt-1 text-foreground leading-relaxed">{clinicalDetails.ai_summary.reasoning}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 6. Matching Regulatory Alerts or Recalls */}
            {clinicalDetails && ((clinicalDetails.alerts || []).length > 0 || (clinicalDetails.recalls || []).length > 0) && (
              <div className="space-y-4">
                <h3 className="font-display text-xl font-bold mt-8 text-foreground">Active Regulatory Notices</h3>
                
                {(clinicalDetails.recalls || []).map((recall, index) => (
                  <div key={index} className="glass-panel border border-red-500/20 bg-red-500/5 rounded-xl p-5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold bg-red-500/20 text-red-400 px-2 py-0.5 rounded">RECALL</span>
                      <span className="text-xs text-muted-foreground">{recall.authority}</span>
                    </div>
                    <h4 className="font-semibold mt-2 text-foreground">{recall.recall_number || "Recall Alert"}</h4>
                    <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{recall.reason}</p>
                  </div>
                ))}

                {(clinicalDetails.alerts || []).map((alert, index) => (
                  <div key={index} className="glass-panel border border-amber-500/20 bg-amber-500/5 rounded-xl p-5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded">ALERT</span>
                      <span className="text-xs text-muted-foreground">{alert.authority}</span>
                    </div>
                    <h4 className="font-semibold mt-2 text-foreground">{alert.title}</h4>
                    <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{alert.summary || alert.details}</p>
                  </div>
                ))}
              </div>
            )}
            
          </div>
        )}
      </div>
    </section>
  );
}
