import { useEffect, useState } from "react";

import { count, plural } from "../format.js";
import { PAGE_SIZE } from "../query/sql.js";

/** A year with no data: always this, with its reason. Never a zero. */
export function NoData({ year, what, reason }) {
  return (
    <div className="nodata" role="note">
      <strong>
        No {what} data for FY{year}.
      </strong>{" "}
      {reason}
    </div>
  );
}

export function Notice({ children, tone = "info" }) {
  return (
    <div className={`notice notice-${tone}`} role="note">
      {children}
    </div>
  );
}

export function Pager({ page, matched, onPage }) {
  if (matched <= PAGE_SIZE) return null;
  const last = Math.ceil(matched / PAGE_SIZE) - 1;
  return (
    <nav className="pager" aria-label="Pages">
      <button type="button" disabled={page <= 0} onClick={() => onPage(page - 1)}>
        Previous
      </button>
      <span>
        Rows {count(page * PAGE_SIZE + 1)}–{count(Math.min(matched, (page + 1) * PAGE_SIZE))} of {count(matched)}
      </span>
      <button type="button" disabled={page >= last} onClick={() => onPage(page + 1)}>
        Next
      </button>
    </nav>
  );
}

/**
 * A text or number filter that applies on Enter or blur rather than on every keystroke: each
 * application re-runs the queries and rewrites the URL.
 */
export function TextFilter({ label, value, onApply, type = "text", placeholder, width }) {
  const [draft, setDraft] = useState(value ?? "");
  useEffect(() => setDraft(value ?? ""), [value]);
  const apply = () => {
    const v = String(draft).trim();
    if (v !== String(value ?? "")) onApply(v);
  };
  return (
    <label className="field" style={width ? { width } : undefined}>
      <span>{label}</span>
      <input
        type={type}
        inputMode={type === "number" ? "decimal" : undefined}
        value={draft}
        placeholder={placeholder}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={apply}
        onKeyDown={(e) => e.key === "Enter" && apply()}
      />
    </label>
  );
}

export function SelectFilter({ label, value, onApply, options }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value ?? ""} onChange={(e) => onApply(e.target.value)}>
        {options.map(([v, text]) => (
          <option key={String(v)} value={v}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}

export function Status({ loading, updating, error, children }) {
  if (error) return <Notice tone="error">Query failed: {String(error.message ?? error)}</Notice>;
  if (loading) return <p className="muted">Loading…</p>;
  return (
    <div className={updating ? "updating" : undefined} aria-busy={updating ? "true" : undefined}>
      {updating ? <p className="muted small">Updating…</p> : null}
      {children}
    </div>
  );
}

export function Matched({ matched, what }) {
  return <p className="matched">{matched === 0 ? `No ${what} match these filters.` : `${plural(matched, what.replace(/s$/, ""), what)} match.`}</p>;
}

/**
 * A link inside the app: sets the hash state, and stays a real link for open-in-new-tab.
 * `current` marks the view tab the visitor is on (aria-current="page"; DESIGN-NOTES.md §1).
 */
export function HashLink({ href, onGo, children, className, current = false }) {
  return (
    <a
      href={href}
      className={className}
      aria-current={current ? "page" : undefined}
      onClick={(e) => {
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault();
        onGo();
      }}
    >
      {children}
    </a>
  );
}
