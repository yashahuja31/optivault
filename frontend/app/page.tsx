import Link from "next/link";
import Navbar from "@/components/Navbar";

export default function Home() {
  return (
    <main>
      <Navbar />

      <section className="px-6 md:px-12 pt-24 pb-20 max-w-4xl">
        <p className="ledger-figure text-waste text-sm mb-4">
          ~30% of stored data in most S3 buckets is never read again
        </p>
        <h1 className="font-display font-bold text-5xl md:text-6xl leading-[1.05] mb-6">
          You're paying full price
          <br />
          for data nobody reads.
        </h1>
        <p className="text-muted text-lg max-w-xl mb-10">
          OptiVault scans your S3 buckets, finds the duplicates, the
          forgotten backups, and the files still sitting on expensive
          storage they outgrew months ago — and shows you exactly what
          it's costing you, in dollars, before you change anything.
        </p>
        <div className="flex gap-4">
          <Link
            href="/signup"
            className="bg-savings text-ink px-6 py-3 rounded-md font-medium hover:opacity-90 transition-opacity"
          >
            Scan your first bucket
          </Link>
          <Link
            href="/pricing"
            className="border border-border px-6 py-3 rounded-md font-medium hover:bg-panel transition-colors"
          >
            See pricing
          </Link>
        </div>
      </section>

      <section className="px-6 md:px-12 pb-24 max-w-4xl grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="border-t border-border pt-4">
          <p className="ledger-figure text-savings text-2xl mb-1">Read-only</p>
          <p className="text-muted text-sm">
            We only ever read metadata — file size, age, storage class.
            Never the contents. Nothing to leak.
          </p>
        </div>
        <div className="border-t border-border pt-4">
          <p className="ledger-figure text-savings text-2xl mb-1">Dry-run first</p>
          <p className="text-muted text-sm">
            Every recommendation is a preview until you approve it.
            Nothing moves or deletes on its own.
          </p>
        </div>
        <div className="border-t border-border pt-4">
          <p className="ledger-figure text-savings text-2xl mb-1">Priced in real time</p>
          <p className="text-muted text-sm">
            Savings estimates use current AWS storage-class pricing,
            not rough guesses.
          </p>
        </div>
      </section>
    </main>
  );
}
