import { useId } from "react";

import { money } from "../format.js";

/**
 * Adopted and modified, by fiscal year: a small hand-written SVG line chart (#270 keeps no chart
 * library). The table right after it carries the same numbers; this is the picture.
 *
 * Accessibility (WCAG 2.2 AA, docs/plans/2026-11-12-270-agency-budgets.md "Chart"):
 *   - svg role="img" with a name that sums it up, from the numbers;
 *   - the two lines differ by dash and marker shape, not only color (adopted: solid, circles;
 *     modified: dashed, open circles), and both colors are at least 3:1 on white
 *     (#2359a8 6.2:1, #414141 10:1);
 *   - a missing figure is a gap in the line, never a drop to $0.
 */
const W = 640;
const H = 240;
const PAD = { left: 64, right: 16, top: 16, bottom: 30 };
const COLORS = { adopted: "#2359a8", modified: "#414141" };

/** "$1.2B", "$350M", "$27K" for axis labels. */
export function shortMoney(v) {
  const a = Math.abs(v);
  const [d, s] = a >= 1e9 ? [1e9, "B"] : a >= 1e6 ? [1e6, "M"] : a >= 1e3 ? [1e3, "K"] : [1, ""];
  const n = v / d;
  return `$${Number.isInteger(n) ? n : n.toFixed(n < 10 ? 1 : 0)}${s}`;
}

/** Round axis top and step: 1, 2 or 5 times a power of ten, at most six steps. */
export function niceScale(max) {
  if (!(max > 0)) return { top: 1, step: 1 };
  const raw = max / 6;
  const p = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * p).find((s) => s >= raw);
  return { top: Math.ceil(max / step) * step, step };
}

/** The chart's text alternative: what a sighted reader takes from the picture. */
export function chartSummary(series, title, newest) {
  const first = series[0]?.year;
  const last = series.at(-1)?.year;
  const a = series.filter((s) => s.adopted != null);
  const parts = [`${title}: adopted and modified budget, FY${first}–FY${last}.`];
  if (a.length) {
    const lo = a.reduce((m, s) => (s.adopted < m.adopted ? s : m));
    const hi = a.reduce((m, s) => (s.adopted > m.adopted ? s : m));
    parts.push(`Adopted went from ${money(a[0].adopted)} in FY${a[0].year} to ${money(a.at(-1).adopted)} in FY${a.at(-1).year}; lowest ${money(lo.adopted)} (FY${lo.year}), highest ${money(hi.adopted)} (FY${hi.year}).`);
  }
  const m = series.filter((s) => s.modified != null);
  if (m.length) parts.push(`Modified was ${money(m.at(-1).modified)} in FY${m.at(-1).year}.`);
  if (newest && series.some((s) => s.year === newest && s.modified == null)) parts.push(`FY${newest} modified is not yet published.`);
  parts.push("The table below has every number.");
  return parts.join(" ");
}

export function YearChart({ series, title, newest }) {
  const id = useId();
  const values = series.flatMap((s) => [s.adopted, s.modified]).filter((v) => v != null);
  const minV = Math.min(0, ...values);
  const { top, step } = niceScale(Math.max(...values, 0));
  const x = (i) => PAD.left + (series.length <= 1 ? 0 : (i * (W - PAD.left - PAD.right)) / (series.length - 1));
  const y = (v) => PAD.top + ((top - v) * (H - PAD.top - PAD.bottom)) / (top - minV || 1);
  const ticks = [];
  for (let v = 0; v <= top + step / 2; v += step) ticks.push(v);
  /** Path segments with gaps where a figure is missing. */
  const path = (key) => {
    let d = "";
    let pen = false;
    series.forEach((s, i) => {
      if (s[key] == null) {
        pen = false;
        return;
      }
      d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(s[key]).toFixed(1)}`;
      pen = true;
    });
    return d;
  };
  const summary = chartSummary(series, title, newest);
  return (
    <figure className="year-chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby={`${id}-t`} preserveAspectRatio="xMidYMid meet">
        <title id={`${id}-t`}>{summary}</title>
        <g aria-hidden="true">
          {ticks.map((t) => (
            <g key={t}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)} stroke="#d0d0d0" strokeWidth="1" />
              <text x={PAD.left - 6} y={y(t) + 4} textAnchor="end" fontSize="14" fill="#414141">
                {shortMoney(t)}
              </text>
            </g>
          ))}
          {series.map((s, i) => (
            <text key={s.year} x={x(i)} y={H - 10} textAnchor="middle" fontSize="14" fill="#414141">
              {`’${String(s.year).slice(2)}`}
            </text>
          ))}
          <path d={path("adopted")} fill="none" stroke={COLORS.adopted} strokeWidth="2.5" />
          <path d={path("modified")} fill="none" stroke={COLORS.modified} strokeWidth="2.5" strokeDasharray="7 5" />
          {series.map((s, i) =>
            s.adopted == null ? null : <circle key={`a${s.year}`} cx={x(i)} cy={y(s.adopted)} r="4.5" fill={COLORS.adopted} />
          )}
          {series.map((s, i) =>
            s.modified == null ? null : <circle key={`m${s.year}`} cx={x(i)} cy={y(s.modified)} r="4.5" fill="#FFFFFF" stroke={COLORS.modified} strokeWidth="2" />
          )}
        </g>
      </svg>
      <figcaption className="chart-key">
        <span className="key key-adopted" aria-hidden="true" /> Adopted (solid blue line, filled dots) <span className="key key-modified" aria-hidden="true" /> Modified
        (dashed gray line, open dots). A gap means no figure for that year.
      </figcaption>
    </figure>
  );
}
