import { AuthenticateWithRedirectCallback } from '@clerk/clerk-react';

/**
 * Handles the OAuth callback from Clerk SSO providers (Google, etc.).
 * Clerk processes the callback and redirects to the specified URL.
 */
export function SsoCallbackPage() {
  return <AuthenticateWithRedirectCallback />;
}
