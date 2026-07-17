import { Link } from "@tanstack/react-router";
import { AlertOctagon } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-32 border-t border-hairline bg-surface-2/50">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-16 md:grid-cols-4">
        <div>
          <div className="flex items-center gap-2.5">
            <img src="/logo.png" alt="SafeMeds AI logo" className="h-9 w-9 rounded-md border border-hairline bg-surface object-contain" />
            <span className="font-display text-lg font-bold">
              <span className="text-primary">SafeMeds</span> AI
            </span>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            A regulatory-grade medicine verification platform. Only definitive records. Zero
            prediction.
          </p>
        </div>

        <div>
          <h4 className="mono-label text-muted-foreground">Platform</h4>
          <ul className="mt-4 space-y-2.5 text-sm">
            {["Verify Medicine", "Features", "How It Works", "About"].map((s) => (
              <li key={s}>
                <Link
                  to={
                    s === "Verify Medicine"
                      ? "/verify"
                      : s === "Features"
                        ? "/features"
                        : s === "How It Works"
                          ? "/how-it-works"
                          : "/about"
                  }
                  className="text-foreground/80 transition-colors hover:text-primary"
                >
                  {s}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="mono-label text-muted-foreground">Data Sources</h4>
          <ul className="mt-4 space-y-2.5 text-sm text-foreground/80">
            <li>CDSCO — Central Drugs Standard Control Organisation</li>
            <li>US FDA — Enforcement Reports</li>
            <li>WHO GSMS — Global Surveillance</li>
          </ul>
        </div>

        <div>
          <h4 className="mono-label text-muted-foreground">Legal Disclaimer</h4>
          <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
            SafeMeds AI surfaces publicly available regulatory records. It is not a substitute for
            professional medical advice.
          </p>
          <div className="mt-4 flex items-start gap-2 rounded-md border border-danger/50 bg-danger/5 p-3">
            <AlertOctagon className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
            <p className="text-xs text-danger/90">
              Medical emergency? Call your local emergency number immediately. Do not rely on this
              tool for urgent care.
            </p>
          </div>
        </div>
      </div>

      <div className="border-t border-hairline">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-6 py-6 text-xs text-muted-foreground md:flex-row">
          <p>© {new Date().getFullYear()} SafeMeds AI. All rights reserved.</p>
          <div className="flex gap-6">
            <a href="#" className="hover:text-primary">
              Privacy
            </a>
            <a href="#" className="hover:text-primary">
              Terms
            </a>
            <a href="#" className="hover:text-primary">
              Compliance
            </a>
          </div>
        </div>
      </div>
 
    </footer>
  );
}
