import { createContext, useContext, useState, useCallback, useRef } from 'react';
import { setTokenGetter } from '@/lib/api';
import { setPdfTokenGetter } from '@/lib/pdf';

// Demo user object that mimics a Clerk-like user for demo mode
export const DEMO_USER = {
  id: 'demo_user_001',
  primaryEmailAddress: { emailAddress: 'demo@kerf.build' },
  fullName: 'Demo Contractor',
  firstName: 'Demo',
  lastName: 'Contractor',
  imageUrl: null,
  emailAddresses: [{ emailAddress: 'demo@kerf.build', verification: { status: 'verified' } }],
};

export type ClerkLikeUser = typeof DEMO_USER;

export interface CompanyData {
  id: string;
  name: string;
  trade_type: string;
  subscription_status: string;
  [key: string]: unknown;
}

export interface VerifyTokenResponse {
  user: {
    uid: string;
    email: string;
    email_verified: boolean;
  };
  company: CompanyData;
  is_new_user: boolean;
}

export interface AuthContextType {
  user: ClerkLikeUser | null;
  loading: boolean;
  clerkConfigured: boolean;
  isDemoMode: boolean;
  isNewUser: boolean;
  company: CompanyData | null;
  signInWithGoogle: () => Promise<void>;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  signInDemo: () => void;
  signOut: () => Promise<void>;
  getToken: () => Promise<string | null>;
  verifyToken: () => Promise<VerifyTokenResponse | null>;
  clearNewUserFlag: () => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

/**
 * Demo-only auth provider — used when Clerk is not configured.
 * Only supports demo mode sign-in.
 */
export function useDemoAuthProvider(): AuthContextType {
  const demoActiveOnInit = sessionStorage.getItem('kerf_demo') === 'true';
  const [user, setUser] = useState<ClerkLikeUser | null>(demoActiveOnInit ? DEMO_USER : null);
  const [isDemoMode, setIsDemoMode] = useState(demoActiveOnInit);
  const [isNewUser, setIsNewUser] = useState(false);
  const [company, setCompany] = useState<CompanyData | null>(null);

  // Register demo token getter
  const tokenGetterSet = useRef(false);
  if (!tokenGetterSet.current) {
    const getter = async () => (sessionStorage.getItem('kerf_demo') === 'true' ? 'demo-token' : null);
    setTokenGetter(getter);
    setPdfTokenGetter(getter);
    tokenGetterSet.current = true;
  }

  const signInDemo = useCallback(() => {
    sessionStorage.setItem('kerf_demo', 'true');
    setUser(DEMO_USER);
    setIsDemoMode(true);
  }, []);

  const notConfigured = useCallback(async () => {
    throw new Error('Clerk is not configured. Please set VITE_CLERK_PUBLISHABLE_KEY.');
  }, []);

  const handleSignOut = useCallback(async () => {
    sessionStorage.removeItem('kerf_demo');
    setIsDemoMode(false);
    setUser(null);
    setCompany(null);
    setIsNewUser(false);
  }, []);

  return {
    user,
    loading: false,
    clerkConfigured: false,
    isDemoMode,
    isNewUser,
    company,
    signInWithGoogle: notConfigured,
    signInWithEmail: notConfigured,
    signUpWithEmail: notConfigured,
    signInDemo,
    signOut: handleSignOut,
    getToken: async () => (isDemoMode ? 'demo-token' : null),
    verifyToken: async () => null,
    clearNewUserFlag: useCallback(() => setIsNewUser(false), []),
  };
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
