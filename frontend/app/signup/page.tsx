"use client";

import { useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import Navbar from "@/components/Navbar";

export default function SignupPage() {
  const { loginWithRedirect, isLoading, isAuthenticated } = useAuth0();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      loginWithRedirect({ authorizationParams: { screen_hint: "signup" } });
    }
  }, [isLoading, isAuthenticated, loginWithRedirect]);

  return (
    <main>
      <Navbar />
      <div className="max-w-sm mx-auto px-6 pt-20">
        <p className="text-muted">Redirecting to secure sign up…</p>
      </div>
    </main>
  );
}
