import { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import {
  auth,
  googleProvider,
  isConfigured,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  firebaseSignOut,
  onAuthStateChanged,
  type User,
} from '@/lib/firebase';

// Demo user object that mimics Firebase User for demo mode
const DEMO_USER = {
  uid: 'demo_user_001',
  email: 'demo@safetyforge.com',
  displayName: 'Demo Contractor',
  emailVerified: true,
  photoURL: null,
  getIdToken: async () => 'demo-token-not-real',
} as unknown as User;

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
  user: User | null;
  loading: boolean;
  firebaseConfigured: boolean;
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

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export function useAuthProvider(): AuthContextType {
  // Check demo mode SYNCHRONOUSLY on init to prevent redirect race condition
  const demoActiveOnInit = sessionStorage.getItem('safetyforge_demo') === 'true';
  const [user, setUser] = useState<User | null>(demoActiveOnInit ? DEMO_USER : null);
  const [loading, setLoading] = useState(demoActiveOnInit ? false : isConfigured);
  const [isDemoMode, setIsDemoMode] = useState(demoActiveOnInit);
  const [isNewUser, setIsNewUser] = useState(false);
  const [company, setCompany] = useState<CompanyData | null>(null);
  const verifyInFlight = useRef(false);

  const verifyToken = useCallback(async (): Promise<VerifyTokenResponse | null> => {
    if (isDemoMode || !auth?.currentUser) return null;
    if (verifyInFlight.current) return null;

    verifyInFlight.current = true;
    try {
      const token = await auth.currentUser.getIdToken();
      const response = await fetch(`${BASE_URL}/auth/verify-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
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
  }, [isDemoMode]);

  const clearNewUserFlag = useCallback(() => {
    setIsNewUser(false);
  }, []);

  useEffect(() => {
    // Demo already handled synchronously above — skip
    if (demoActiveOnInit) return;

    if (!isConfigured || !auth) {
      setLoading(false);
      return;
    }
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        // Verify token with backend to get/create company
        try {
          const token = await firebaseUser.getIdToken();
          const response = await fetch(`${BASE_URL}/auth/verify-token`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
          });
          if (response.ok) {
            const data: VerifyTokenResponse = await response.json();
            setCompany(data.company);
            setIsNewUser(data.is_new_user);
          }
        } catch {
          // Backend may be unavailable — continue with Firebase auth only
        }
      } else {
        setCompany(null);
        setIsNewUser(false);
      }
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const signInDemo = useCallback(() => {
    sessionStorage.setItem('safetyforge_demo', 'true');
    setUser(DEMO_USER);
    setIsDemoMode(true);
  }, []);

  const signInWithGoogle = useCallback(async () => {
    if (!auth || !googleProvider) {
      throw new Error('Firebase is not configured. Please set up environment variables.');
    }
    await signInWithPopup(auth, googleProvider);
  }, []);

  const signInWithEmail = useCallback(async (email: string, password: string) => {
    if (!auth) {
      throw new Error('Firebase is not configured. Please set up environment variables.');
    }
    await signInWithEmailAndPassword(auth, email, password);
  }, []);

  const signUpWithEmail = useCallback(async (email: string, password: string) => {
    if (!auth) {
      throw new Error('Firebase is not configured. Please set up environment variables.');
    }
    await createUserWithEmailAndPassword(auth, email, password);
  }, []);

  const signOut = useCallback(async () => {
    sessionStorage.removeItem('safetyforge_demo');
    setIsDemoMode(false);
    setUser(null);
    setCompany(null);
    setIsNewUser(false);
    if (auth) {
      await firebaseSignOut(auth);
    }
  }, []);

  const getToken = useCallback(async (): Promise<string | null> => {
    if (isDemoMode) return 'demo-token';
    if (!user) return null;
    return user.getIdToken();
  }, [user, isDemoMode]);

  return {
    user,
    loading,
    firebaseConfigured: isConfigured,
    isDemoMode,
    isNewUser,
    company,
    signInWithGoogle,
    signInWithEmail,
    signUpWithEmail,
    signInDemo,
    signOut,
    getToken,
    verifyToken,
    clearNewUserFlag,
  };
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
