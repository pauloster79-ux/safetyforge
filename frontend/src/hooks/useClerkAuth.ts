/**
 * Clerk-powered auth provider.
 * Only imported when Clerk is configured (ClerkProvider in tree).
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { useAuth as useClerkAuth, useUser as useClerkUser, useSignIn, useSignUp } from '@clerk/clerk-react';
import { isConfigured } from '@/lib/clerk';
import { setTokenGetter } from '@/lib/api';
import { setPdfTokenGetter } from '@/lib/pdf';
import type { AuthContextType, ClerkLikeUser, VerifyTokenResponse, CompanyData } from './useAuth';
import { DEMO_USER } from './useAuth';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export function useClerkAuthProvider(): AuthContextType {
  const clerkAuth = useClerkAuth();
  const clerkUser = useClerkUser();
  const { signIn } = useSignIn();
  const { signUp } = useSignUp();

  const demoActiveOnInit = sessionStorage.getItem('kerf_demo') === 'true';
  const [demoUser, setDemoUser] = useState<ClerkLikeUser | null>(
    demoActiveOnInit ? DEMO_USER : null
  );
  const [isDemoMode, setIsDemoMode] = useState(demoActiveOnInit);
  const [isNewUser, setIsNewUser] = useState(false);
  const [company, setCompany] = useState<CompanyData | null>(null);
  const verifyInFlight = useRef(false);

  // Derive the active user — demo user or Clerk user
  const user: ClerkLikeUser | null = isDemoMode
    ? demoUser
    : clerkUser.isLoaded && clerkUser.user
      ? {
          id: clerkUser.user.id,
          primaryEmailAddress: clerkUser.user.primaryEmailAddress
            ? { emailAddress: clerkUser.user.primaryEmailAddress.emailAddress }
            : { emailAddress: '' },
          fullName: clerkUser.user.fullName || '',
          firstName: clerkUser.user.firstName || '',
          lastName: clerkUser.user.lastName || '',
          imageUrl: clerkUser.user.imageUrl || null,
          emailAddresses: clerkUser.user.emailAddresses.map((e) => ({
            emailAddress: e.emailAddress,
            verification: { status: e.verification?.status || 'unverified' },
          })),
        }
      : null;

  const loading = isDemoMode ? false : !clerkAuth.isLoaded;

  const verifyToken = useCallback(async (): Promise<VerifyTokenResponse | null> => {
    if (isDemoMode) return null;
    if (!clerkAuth.isSignedIn) return null;
    if (verifyInFlight.current) return null;

    verifyInFlight.current = true;
    try {
      const token = await clerkAuth.getToken();
      if (!token) return null;

      const response = await fetch(`${BASE_URL}/auth/verify-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) return null;

      const data: VerifyTokenResponse = await response.json();
      setCompany(data.company);
      setIsNewUser(data.is_new_user);
      return data;
    } catch {
      return null;
    } finally {
      verifyInFlight.current = false;
    }
  }, [isDemoMode, clerkAuth]);

  // Register the token getter so api.ts and pdf.ts can get tokens
  useEffect(() => {
    const getter = async () => {
      if (isDemoMode) return 'demo-token';
      if (!clerkAuth.isSignedIn) return null;
      return clerkAuth.getToken();
    };
    setTokenGetter(getter);
    setPdfTokenGetter(getter);
  }, [isDemoMode, clerkAuth]);

  // Verify token on initial sign-in
  useEffect(() => {
    if (isDemoMode || !clerkAuth.isLoaded || !clerkAuth.isSignedIn) return;
    if (company) return;

    verifyToken();
  }, [clerkAuth.isLoaded, clerkAuth.isSignedIn, isDemoMode, company, verifyToken]);

  const clearNewUserFlag = useCallback(() => {
    setIsNewUser(false);
  }, []);

  const signInDemo = useCallback(() => {
    sessionStorage.setItem('kerf_demo', 'true');
    setDemoUser(DEMO_USER);
    setIsDemoMode(true);
  }, []);

  const signInWithGoogle = useCallback(async () => {
    if (!signIn) {
      throw new Error('Clerk is not configured. Please set up environment variables.');
    }
    await signIn.authenticateWithRedirect({
      strategy: 'oauth_google',
      redirectUrl: '/sso-callback',
      redirectUrlComplete: '/dashboard',
    });
  }, [signIn]);

  const signInWithEmail = useCallback(
    async (email: string, password: string) => {
      if (!signIn) {
        throw new Error('Clerk is not configured.');
      }
      const result = await signIn.create({
        identifier: email,
        password,
      });
      if (result.status === 'complete') {
        await clerkAuth.setActive?.({ session: result.createdSessionId });
      }
    },
    [signIn, clerkAuth]
  );

  const signUpWithEmail = useCallback(
    async (email: string, password: string) => {
      if (!signUp) {
        throw new Error('Clerk is not configured.');
      }
      const result = await signUp.create({
        emailAddress: email,
        password,
      });
      if (result.status === 'complete') {
        await clerkAuth.setActive?.({ session: result.createdSessionId });
      }
    },
    [signUp, clerkAuth]
  );

  const handleSignOut = useCallback(async () => {
    sessionStorage.removeItem('kerf_demo');
    setIsDemoMode(false);
    setDemoUser(null);
    setCompany(null);
    setIsNewUser(false);
    if (clerkAuth.isSignedIn) {
      await clerkAuth.signOut();
    }
  }, [clerkAuth]);

  const getToken = useCallback(async (): Promise<string | null> => {
    if (isDemoMode) return 'demo-token';
    if (!clerkAuth.isSignedIn) return null;
    return clerkAuth.getToken();
  }, [isDemoMode, clerkAuth]);

  return {
    user,
    loading,
    clerkConfigured: isConfigured,
    isDemoMode,
    isNewUser,
    company,
    signInWithGoogle,
    signInWithEmail,
    signUpWithEmail,
    signInDemo,
    signOut: handleSignOut,
    getToken,
    verifyToken,
    clearNewUserFlag,
  };
}
