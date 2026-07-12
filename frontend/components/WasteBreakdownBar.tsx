import { AnalysisResult } from "@/lib/api";

interface Segment {
  label: string;
  amount: number;
  color: string;
}

export default function WasteBreakdownBar({ result }: { result: AnalysisResult }) {
  const segments: Segment[] = [
    { label: "Duplicates", amount: result.duplicate_waste_usd, color: "bg-danger" },
    { label: "Wrong tier / stale", amount: result.archive_savings_usd, color: "bg-waste" },
  ].filter((s) => s.amount > 0);

  const total = segments.reduce((sum, s) => sum + s.amount, 0);

  if (total === 0) {
    return (
      <p className="text-muted text-sm">
        No waste detected in the last scan — this bucket is already lean.
      </p>
    );
  }

  return (
    <div>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-panel-hover">
        {segments.map((s) => (
          <div
            key={s.label}
            className={s.color}
            style={{ width: `${(s.amount / total) * 100}%` }}
            title={`${s.label}: $${s.amount.toFixed(4)}/mo`}
          />
        ))}
      </div>
      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1">
        {segments.map((s) => (
          <div key={s.label} className="flex items-center gap-2 text-sm">
            <span className={`h-2 w-2 rounded-full ${s.color}`} />
            <span className="text-muted">{s.label}</span>
            <span className="ledger-figure text-text">${s.amount.toFixed(4)}/mo</span>
          </div>
        ))}
      </div>
    </div>
  );
}
