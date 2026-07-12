"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { login, ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <Navbar />
      <div className="max-w-sm mx-auto px-6 pt-20">
        <h1 className="font-display font-bold text-3xl mb-8">Log in</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="text-sm text-muted block mb-1.5" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-panel border border-border rounded-md px-3 py-2.5 focus-visible:border-savings"
            />
          </div>
          <div>
            <label className="text-sm text-muted block mb-1.5" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-panel border border-border rounded-md px-3 py-2.5 focus-visible:border-savings"
            />
          </div>
          {error && <p className="text-danger text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="bg-savings text-ink px-4 py-2.5 rounded-md font-medium hover:opacity-90 transition-opacity disabled:opacity-50 mt-2"
          >
            {loading ? "Logging in…" : "Log in"}
          </button>
        </form>
        <p className="text-muted text-sm mt-6">
          No account yet?{" "}
          <a href="/signup" className="text-savings">
            Sign up
          </a>
        </p>
      </div>
    </main>
  );
}
