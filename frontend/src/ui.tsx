import type { ReactNode } from "react";

export const STAGES = ["introduction", "background", "projects", "technical", "wrap_up"] as const;

export const label = (key: string) => key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export const errorMessage = (err: unknown) => (err instanceof Error ? err.message : "Something went wrong");

export const formatDate = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });

export function scoreTone(score: number) {
  if (score >= 75) return "good";
  if (score >= 55) return "ok";
  return "low";
}

export function Spinner({ text = "Loading…" }: { text?: string }) {
  return (
    <div className="spinner" role="status">
      <span className="spinner-dot" aria-hidden />
      {text}
    </div>
  );
}

export function ErrorBanner({ error, onRetry }: { error: string | null; onRetry?: () => void }) {
  if (!error) return null;
  return (
    <div className="alert" role="alert">
      <span>{error}</span>
      {onRetry && (
        <button className="btn btn-ghost btn-sm" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function Card({ title, action, children }: { title?: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="card">
      {(title || action) && (
        <div className="card-head">
          {title && <h2>{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function Chips({ items, tone }: { items: string[]; tone?: "good" | "low" }) {
  if (!items.length) return <span className="muted">None</span>;
  return (
    <div className="chips">
      {items.map((item) => (
        <span key={item} className={`chip ${tone ? `chip-${tone}` : ""}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

export function ScoreRing({ score, size = 132 }: { score: number; size?: number }) {
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const value = Math.max(0, Math.min(100, score));
  return (
    <div className={`ring tone-${scoreTone(value)}`} style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={r} className="ring-track" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          className="ring-value"
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - value / 100)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="ring-label">
        <strong>{Math.round(value)}</strong>
        <span>/ 100</span>
      </div>
    </div>
  );
}

export function Bar({ name, value }: { name: string; value: number }) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div className="bar-row">
      <div className="bar-head">
        <span>{name}</span>
        <strong>{Math.round(v)}</strong>
      </div>
      <div className="bar-track">
        <div className={`bar-fill tone-${scoreTone(v)}`} style={{ width: `${v}%` }} />
      </div>
    </div>
  );
}
