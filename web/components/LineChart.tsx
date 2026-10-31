"use client";
import { useMemo, useRef, useState } from "react";

export interface Series { name: string; color: string; points: { t: string; v: number }[] }

/** Minimal line chart: one y-axis, 2px lines, crosshair + tooltip on hover/touch. */
const FORMATS = {
  pct0: (v: number) => `${(v * 100).toFixed(0).replace("-", "−")} %`,
  pct1: (v: number) => `${(v * 100).toFixed(1).replace(".", ",").replace("-", "−")} %`,
};

export default function LineChart({ series, height = 240, valueFormat = "pct0", ariaLabel }:
  { series: Series[]; height?: number; valueFormat?: keyof typeof FORMATS; ariaLabel: string }) {
  const format = FORMATS[valueFormat];
  const W = 900, H = height, padL = 52, padR = 12, padT = 10, padB = 24;
  const ref = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);
  const times = useMemo(() => [...new Set(series.flatMap((s) => s.points.map((p) => p.t)))].sort(), [series]);
  const vals = series.flatMap((s) => s.points.map((p) => p.v));
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const span = hi - lo || 1;
  const x = (i: number) => padL + (i / Math.max(times.length - 1, 1)) * (W - padL - padR);
  const y = (v: number) => padT + (1 - (v - lo) / span) * (H - padT - padB);
  const ticks = [lo, lo + span / 2, hi];
  const onMove = (e: React.PointerEvent) => {
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const px = ((e.clientX - r.left) / r.width) * W;
    const i = Math.round(((px - padL) / (W - padL - padR)) * (times.length - 1));
    setHover(Math.min(Math.max(i, 0), times.length - 1));
  };
  const ht = hover !== null ? times[hover] : null;
  return (
    <div style={{ position: "relative" }}>
      <div className="legend">
        {series.map((s) => <span key={s.name} style={{ ["--c" as string]: s.color }}>{s.name}</span>)}
      </div>
      <svg ref={ref} className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={ariaLabel}
        onPointerMove={onMove} onPointerLeave={() => setHover(null)}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={padL} x2={W - padR} y1={y(t)} y2={y(t)} stroke="var(--border)" strokeWidth={1} />
            <text x={padL - 6} y={y(t) + 4} textAnchor="end">{format(t)}</text>
          </g>
        ))}
        <text x={padL} y={H - 6}>{times[0]?.slice(0, 7)}</text>
        <text x={W - padR} y={H - 6} textAnchor="end">{times.at(-1)?.slice(0, 7)}</text>
        {series.map((s) => {
          const idx = new Map(times.map((t, i) => [t, i]));
          const d = s.points.map((p, k) => `${k ? "L" : "M"}${x(idx.get(p.t) ?? 0).toFixed(1)},${y(p.v).toFixed(1)}`).join("");
          return <path key={s.name} d={d} fill="none" stroke={s.color} strokeWidth={2} strokeLinejoin="round" />;
        })}
        {ht ? <line x1={x(hover!)} x2={x(hover!)} y1={padT} y2={H - padB} stroke="var(--text-3)" strokeWidth={1} /> : null}
        {ht ? series.map((s) => {
          const p = s.points.find((q) => q.t === ht);
          return p ? <circle key={s.name} cx={x(hover!)} cy={y(p.v)} r={4} fill={s.color} stroke="var(--surface)" strokeWidth={2} /> : null;
        }) : null}
      </svg>
      {ht ? (
        <div className="tooltip" style={{ left: `min(calc(${(x(hover!) / W) * 100}% + 8px), calc(100% - 180px))`, top: 28 }}>
          <div className="muted">{ht}</div>
          {series.map((s) => {
            const p = s.points.find((q) => q.t === ht);
            return p ? <div key={s.name}>{s.name}: <strong>{format(p.v)}</strong></div> : null;
          })}
        </div>
      ) : null}
    </div>
  );
}
