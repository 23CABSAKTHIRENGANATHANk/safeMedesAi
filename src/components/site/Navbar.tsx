import { Link } from "@tanstack/react-router";

const links = [
  { to: "/", label: "Home" },
  { to: "/verify", label: "Verify Medicine" },
  { to: "/features", label: "Features" },
  { to: "/how-it-works", label: "How It Works" },
  { to: "/about", label: "About" },
] as const;

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-hairline/80 bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to="/" className="group flex items-center gap-2.5">
          <img
            src="/logo.png"
            alt="SafeMeds AI logo"
            className="h-9 w-9 rounded-md border border-hairline bg-surface object-contain"
          />
          <span className="font-display text-lg font-bold tracking-tight">
            <span className="text-primary">SafeMeds</span>
            <span className="text-foreground"> AI</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className="mono-label group relative px-3 py-2 text-muted-foreground transition-colors hover:text-foreground"
              activeProps={{ className: "text-primary" }}
              activeOptions={{ exact: l.to === "/" }}
            >
              {l.label}
              <span className="absolute inset-x-3 -bottom-[1px] h-px scale-x-0 bg-primary transition-transform duration-200 group-[.text-primary]:scale-x-100" />
            </Link>
          ))}
        </nav>

        <Link
          to="/verify"
          className="mono-label hidden rounded-md border border-primary/40 bg-primary/10 px-3.5 py-2 text-primary transition-all hover:bg-primary/20 hover:shadow-[0_0_20px_-4px_rgba(18,185,129,0.6)] md:inline-flex"
        >
          Launch Terminal
        </Link>
      </div>
    </header>
  );
}
