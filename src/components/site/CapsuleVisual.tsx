import capsuleImg from "@/assets/capsule-3d.png";

export function CapsuleVisual({ className = "" }: { className?: string }) {
  return (
    <div className={`relative aspect-square w-full max-w-[560px] ${className}`}>
      {/* Ambient glows */}
      <div className="absolute inset-0 glow-teal blur-2xl" />
      <div className="absolute left-1/2 top-1/2 h-[70%] w-[70%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/25 blur-3xl animate-pulse-glow" />
      <div className="absolute left-1/2 top-1/2 h-[40%] w-[40%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-capsule-blue/25 blur-3xl" />

      {/* Concentric grid rings */}
      <div className="absolute inset-0 grid place-items-center">
        <div className="absolute h-[92%] w-[92%] rounded-full border border-primary/10" />
        <div className="absolute h-[70%] w-[70%] rounded-full border border-primary/15" />
        <div className="absolute h-[48%] w-[48%] rounded-full border border-primary/20" />

        {/* Crosshair ticks */}
        <svg viewBox="0 0 400 400" className="absolute h-full w-full text-primary/40">
          {Array.from({ length: 24 }).map((_, i) => {
            const a = (i / 24) * Math.PI * 2;
            const r1 = 175,
              r2 = i % 3 === 0 ? 165 : 170;
            const x1 = 200 + Math.cos(a) * r1;
            const y1 = 200 + Math.sin(a) * r1;
            const x2 = 200 + Math.cos(a) * r2;
            const y2 = 200 + Math.sin(a) * r2;
            return (
              <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="currentColor" strokeWidth="1" />
            );
          })}
        </svg>
      </div>

      {/* 3D stage */}
      <div className="absolute inset-0 grid place-items-center [perspective:1200px]">
        {/* Saturn-style rings */}
        <div
          className="absolute h-[82%] w-[82%] rounded-full border-2 border-primary-glow/50"
          style={{
            animation: "orbit-spin 22s linear infinite",
            boxShadow: "0 0 60px rgba(78,230,184,0.25), inset 0 0 60px rgba(78,230,184,0.15)",
          }}
        >
          {/* Ring accent nodes */}
          <div className="absolute -top-1.5 left-1/2 h-3 w-3 -translate-x-1/2 rounded-full bg-primary-glow shadow-[0_0_18px_4px_rgba(78,230,184,0.9)]" />
          <div className="absolute top-1/2 -right-1.5 h-2 w-2 -translate-y-1/2 rounded-full bg-primary shadow-[0_0_12px_2px_rgba(18,185,129,0.8)]" />
        </div>
        <div
          className="absolute h-[96%] w-[96%] rounded-full border border-primary/25"
          style={{ animation: "orbit-spin-rev 34s linear infinite" }}
        >
          <div className="absolute top-1/2 -left-1 h-2 w-2 -translate-y-1/2 rounded-full bg-capsule-blue shadow-[0_0_14px_3px_rgba(59,130,246,0.8)]" />
        </div>
        <div
          className="absolute h-[68%] w-[68%] rounded-full border border-dashed border-primary/30"
          style={{ animation: "orbit-spin 16s linear infinite" }}
        />

        {/* Logo wrapper — bobs and tilts */}
        <div className="animate-bob relative h-[65%] w-[65%]">
          {/* Bottom drop shadow */}
          <div className="absolute -bottom-8 left-1/2 h-6 w-[100%] -translate-x-1/2 rounded-full bg-black/70 blur-xl" />

          {/* Outer teal aura */}
          <div className="pointer-events-none absolute -inset-6 rounded-full bg-primary/25 blur-3xl -z-10" />
          <div className="pointer-events-none absolute -inset-2 rounded-full bg-capsule-blue/25 blur-2xl -z-10" />

          {/* Photorealistic logo */}
          <img
            src={capsuleImg}
            alt="SafeMeds AI Logo"
            width={1024}
            height={1024}
            className="relative h-full w-full object-contain rounded-2xl drop-shadow-[0_30px_60px_rgba(59,130,246,0.55)] [filter:drop-shadow(0_0_30px_rgba(78,230,184,0.35))]"
          />

          {/* Scan sweep across logo */}
          <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-2xl">
            <div className="animate-scan-vertical absolute inset-x-0 h-16 bg-gradient-to-b from-transparent via-primary-glow/60 to-transparent blur-md mix-blend-screen" />
          </div>

          {/* Glossy specular sheen overlay */}
          <div className="pointer-events-none absolute inset-0 rounded-2xl bg-[radial-gradient(ellipse_at_30%_20%,rgba(255,255,255,0.18),transparent_55%)] mix-blend-screen" />
        </div>

        {/* Hex particles - more of them, layered depths */}

        <Hex className="animate-float-a absolute left-[12%] top-[18%]" size={26} />
        <Hex className="animate-float-b absolute right-[14%] top-[32%]" size={18} />
        <Hex className="animate-float-c absolute left-[22%] bottom-[18%]" size={22} />
        <Hex className="animate-float-d absolute right-[18%] bottom-[24%]" size={16} />
        <Hex className="animate-float-b absolute left-[46%] top-[10%]" size={12} filled />
        <Hex className="animate-float-c absolute right-[8%] top-[58%]" size={14} filled />
        <Hex className="animate-float-a absolute left-[8%] top-[62%]" size={12} />

        {/* Orbiting molecule dots */}
        <div className="absolute inset-0" style={{ animation: "orbit-spin 12s linear infinite" }}>
          <div className="absolute left-1/2 top-[8%] h-2 w-2 -translate-x-1/2 rounded-full bg-primary-glow shadow-[0_0_16px_3px_rgba(78,230,184,0.9)]" />
        </div>
        <div
          className="absolute inset-0"
          style={{ animation: "orbit-spin-rev 18s linear infinite" }}
        >
          <div className="absolute right-[10%] top-1/2 h-1.5 w-1.5 rounded-full bg-capsule-blue shadow-[0_0_12px_3px_rgba(59,130,246,0.9)]" />
        </div>
      </div>

      {/* Corner HUD markers */}
      <Corner className="left-2 top-2" />
      <Corner className="right-2 top-2 rotate-90" />
      <Corner className="right-2 bottom-2 rotate-180" />
      <Corner className="left-2 bottom-2 -rotate-90" />
    </div>
  );
}

function Corner({ className = "" }: { className?: string }) {
  return (
    <div className={`pointer-events-none absolute h-5 w-5 ${className}`}>
      <div className="absolute left-0 top-0 h-full w-[2px] bg-primary/60" />
      <div className="absolute left-0 top-0 h-[2px] w-full bg-primary/60" />
    </div>
  );
}

function Hex({
  className = "",
  size = 18,
  filled = false,
}: {
  className?: string;
  size?: number;
  filled?: boolean;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      style={{ filter: "drop-shadow(0 0 10px rgba(78,230,184,0.8))" }}
    >
      <polygon
        points="12,2 21,7 21,17 12,22 3,17 3,7"
        fill={filled ? "rgba(78,230,184,0.85)" : "rgba(18,185,129,0.18)"}
        stroke="#4EE6B8"
        strokeWidth="1.2"
      />
      {!filled && (
        <polygon
          points="12,6 17,9 17,15 12,18 7,15 7,9"
          fill="none"
          stroke="rgba(78,230,184,0.5)"
          strokeWidth="0.8"
        />
      )}
    </svg>
  );
}
