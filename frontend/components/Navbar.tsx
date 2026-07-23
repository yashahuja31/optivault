"use client";

import Link from "next/link";
import { useAuth0 } from "@auth0/auth0-react";

export default function Navbar() {
  const { isAuthenticated, isLoading, loginWithRedirect, logout } = useAuth0();

  return (
    <nav className="flex items-center justify-between px-6 py-5 md:px-12 border-b border-border">
      <Link href="/" className="font-display font-bold text-lg tracking-tight">
        OptiVault
      </Link>
      <div className="flex items-center gap-6 text-sm text-muted">
        <Link href="/pricing" className="hover:text-text transition-colors">
          Pricing
        </Link>
        {isLoading ? null : isAuthenticated ? (
          <>
            <Link href="/dashboard" className="hover:text-text transition-colors">
              Dashboard
            </Link>
            <button
              onClick={() =>
                logout({ logoutParams: { returnTo: window.location.origin } })
              }
              className="hover:text-text transition-colors"
            >
              Log out
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => loginWithRedirect()}
              className="hover:text-text transition-colors"
            >
              Log in
            </button>
            <button
              onClick={() =>
                loginWithRedirect({
                  authorizationParams: { screen_hint: "signup" },
                })
              }
              className="bg-savings text-ink px-4 py-2 rounded-md font-medium hover:opacity-90 transition-opacity"
            >
              Sign up
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
