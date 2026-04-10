/**
 * Clerk authentication configuration.
 *
 * Replaces Firebase Auth. Clerk handles sign-up, sign-in,
 * session management, and JWT token generation.
 */

export const CLERK_PUBLISHABLE_KEY =
  import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';

export const isConfigured =
  CLERK_PUBLISHABLE_KEY !== '' && CLERK_PUBLISHABLE_KEY !== 'not-configured';

if (!isConfigured) {
  console.warn(
    'Clerk is not configured. Set VITE_CLERK_PUBLISHABLE_KEY in .env'
  );
}
