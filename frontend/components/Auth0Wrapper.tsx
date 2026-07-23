"use client";

import { Auth0Provider } from "@auth0/auth0-react";

const domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN || "";
const clientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID || "";
const audience = process.env.NEXT_PUBLIC_AUTH0_AUDIENCE || "";

export default function Auth0Wrapper({ children }: { children: React.ReactNode }) {
  // On the server (and before hydration) window is undefined; Auth0Provider is
  // a client component, so this file is only evaluated in the browser tree.
  const redirectUri =
    typeof window !== "undefined" ? window.location.origin : undefined;

  return (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: redirectUri,
        audience,
      }}
    >
      {children}
    </Auth0Provider>
  );
}
