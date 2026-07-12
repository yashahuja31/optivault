"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getToken, clearToken } from "@/lib/api";

export default function Navbar() {
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(!!getToken());
  }, []);

  return (
    <nav className="flex items-center justify-between px-6 py-5 md:px-12 border-b border-border">
      <Link href="/" className="font-display font-bold text-lg tracking-tight">
        OptiVault
      </Link>
      <div className="flex items-center gap-6 text-sm text-muted">
        <Link href="/pricing" className="hover:text-text transition-colors">
          Pricing
        </Link>
        {loggedIn ? (
          <>
            <Link href="/dashboard" className="hover:text-text transition-colors">
              Dashboard
            </Link>
            <button
              onClick={() => {
                clearToken();
                window.location.href = "/";
              }}
              className="hover:text-text transition-colors"
            >
              Log out
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className="hover:text-text transition-colors">
              Log in
            </Link>
            <Link
              href="/signup"
              className="bg-savings text-ink px-4 py-2 rounded-md font-medium hover:opacity-90 transition-opacity"
            >
              Sign up
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
