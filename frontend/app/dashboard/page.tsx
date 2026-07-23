"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import Navbar from "@/components/Navbar";
import WasteBreakdownBar from "@/components/WasteBreakdownBar";
import {
  listAccounts,
  createAccount,
  startScan,
  getScanStatus,
  analyzeAccount,
  getReport,
  CloudAccount,
  ScanJob,
  AnalysisResult,
  OptimizationReportOut,
} from "@/lib/api";

export default function DashboardPage() {
  const { isAuthenticated, isLoading: authLoading, loginWithRedirect, getAccessTokenSilently } =
    useAuth0();
  const [accounts, setAccounts] = useState<CloudAccount[]>([]);
  const [newBucket, setNewBucket] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      loginWithRedirect();
      return;
    }
    getAccessTokenSilently()
      .then((token) => listAccounts(token))
      .then(setAccounts)
      .finally(() => setLoading(false));
  }, [authLoading, isAuthenticated, loginWithRedirect, getAccessTokenSilently]);

  async function handleAddAccount(e: React.FormEvent) {
    e.preventDefault();
    if (!newBucket.trim()) return;
    const token = await getAccessTokenSilently();
    const account = await createAccount(token, newBucket.trim());
    setAccounts((prev) => [...prev, account]);
    setNewBucket("");
  }

  if (authLoading || loading) {
    return (
      <main>
        <Navbar />
        <p className="px-6 md:px-12 pt-20 text-muted">Loading…</p>
      </main>
    );
  }

  return (
    <main>
      <Navbar />
      <div className="px-6 md:px-12 pt-16 pb-24 max-w-3xl">
        <h1 className="font-display font-bold text-3xl mb-8">Your buckets</h1>

        <form onSubmit={handleAddAccount} className="flex gap-3 mb-10">
          <input
            value={newBucket}
            onChange={(e) => setNewBucket(e.target.value)}
            placeholder="your-bucket-name"
            className="flex-1 bg-panel border border-border rounded-md px-3 py-2.5 ledger-figure text-sm focus-visible:border-savings"
          />
          <button
            type="submit"
            className="bg-savings text-ink px-4 py-2.5 rounded-md font-medium hover:opacity-90 transition-opacity"
          >
            Connect bucket
          </button>
        </form>

        {accounts.length === 0 ? (
          <p className="text-muted">
            No buckets connected yet. Add one above to run your first scan.
          </p>
        ) : (
          <div className="flex flex-col gap-6">
            {accounts.map((account) => (
              <AccountCard key={account.id} account={account} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

function AccountCard({ account }: { account: CloudAccount }) {
  const { getAccessTokenSilently } = useAuth0();
  const [scanJob, setScanJob] = useState<ScanJob | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [report, setReport] = useState<OptimizationReportOut | null>(null);
  const [busy, setBusy] = useState<"scan" | "analyze" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pollScan = useCallback(async () => {
    for (let i = 0; i < 30; i++) {
      const token = await getAccessTokenSilently();
      const job = await getScanStatus(token, account.id);
      setScanJob(job);
      if (job.status === "completed" || job.status === "failed") break;
      await new Promise((r) => setTimeout(r, 1500));
    }
  }, [account.id, getAccessTokenSilently]);

  async function handleScan() {
    setError(null);
    setBusy("scan");
    try {
      const token = await getAccessTokenSilently();
      const job = await startScan(token, account.id);
      setScanJob(job);
      await pollScan();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed to start.");
    } finally {
      setBusy(null);
    }
  }

  async function handleAnalyze() {
    setError(null);
    setBusy("analyze");
    try {
      const token = await getAccessTokenSilently();
      const analysisResult = await analyzeAccount(token, account.id);
      setResult(analysisResult);
      setReport(await getReport(token, account.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed. Run a scan first.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="border border-border rounded-lg p-6 bg-panel">
      <div className="flex items-center justify-between mb-4">
        <p className="ledger-figure font-medium">{account.bucket_name}</p>
        <div className="flex gap-2">
          <button
            onClick={handleScan}
            disabled={busy !== null}
            className="text-sm border border-border px-3 py-1.5 rounded-md hover:bg-panel-hover transition-colors disabled:opacity-50"
          >
            {busy === "scan" ? "Scanning…" : "Scan"}
          </button>
          <button
            onClick={handleAnalyze}
            disabled={busy !== null}
            className="text-sm bg-savings text-ink px-3 py-1.5 rounded-md hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {busy === "analyze" ? "Analyzing…" : "Analyze"}
          </button>
        </div>
      </div>

      {scanJob && (
        <p className="text-xs text-muted mb-4">
          Last scan: {scanJob.status} — {scanJob.objects_scanned} objects indexed
        </p>
      )}

      {error && <p className="text-danger text-sm mb-4">{error}</p>}

      {result && (
        <div className="border-t border-border pt-4 mt-2">
          <div className="flex items-baseline gap-3 mb-1">
            <span className="ledger-figure text-3xl text-savings">
              ${result.estimated_monthly_savings_usd.toFixed(4)}
            </span>
            <span className="text-muted text-sm">/month potential savings</span>
          </div>
          <p className="text-muted text-sm mb-5">
            of ${result.current_monthly_cost_usd.toFixed(4)}/mo currently spent across{" "}
            {result.total_files} files
          </p>
          <WasteBreakdownBar result={result} />
        </div>
      )}

      {report && !result && (
        <p className="text-muted text-sm border-t border-border pt-4 mt-2">
          {report.summary_text}
        </p>
      )}
    </div>
  );
}
