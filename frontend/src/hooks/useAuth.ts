import { createContext, useContext, useState, useCallback, useRef } from 'react';
import { setTokenGetter } from '@/lib/api';
import { setPdfTokenGetter } from '@/lib/pdf';

// -----------------------------------------------------------------------------
// Demo user registry
//
// Mirrors backend/app/dependencies.py::DEMO_USERS. Each entry corresponds to
// the owner of one of the 10 seeded golden companies. Switching between them
// lets us test multi-tenant recording without wiring up Clerk.
//
// The alias forms the token suffix sent to the API (demo-token-<alias>).
// -----------------------------------------------------------------------------
export type ClerkLikeUser = {
  id: string;
  primaryEmailAddress: { emailAddress: string };
  fullName: string;
  firstName: string;
  lastName: string;
  imageUrl: string | null;
  emailAddresses: { emailAddress: string; verification: { status: string } }[];
};

export interface DemoUser {
  alias: string;
  uid: string;
  email: string;
  name: string;
  companyId: string;
}

export const DEMO_USERS: DemoUser[] = [
  { alias: 'gp01', uid: 'user_gp01_mike',    email: 'mike@mikeshandyman.com',             name: "Mike Torres (Handyman, FL)",      companyId: 'comp_gp01' },
  { alias: 'gp02', uid: 'user_gp02_sarah',   email: 'sarah@lakeshorebuilders.ca',         name: 'Sarah Chen (Deck, ON)',           companyId: 'comp_gp02' },
  { alias: 'gp03', uid: 'user_gp03_james',   email: 'james@brightstone.co.uk',            name: 'James Okafor (Shop fitout, UK)',  companyId: 'comp_gp03' },
  { alias: 'gp04', uid: 'demo_user_001',     email: 'demo@kerf.build',                    name: 'David Nguyen (Custom home, CA)',  companyId: 'comp_gp04' },
  { alias: 'gp05', uid: 'user_gp05_emma',    email: 'emma@southerncrossindustrial.com.au',name: 'Emma Walsh (Warehouse, AU)',      companyId: 'comp_gp05' },
  { alias: 'gp06', uid: 'user_gp06_ryan',    email: 'ryan@fraservalleycontracting.ca',    name: 'Ryan Patel (School reno, BC)',    companyId: 'comp_gp06' },
  { alias: 'gp07', uid: 'user_gp07_anthony', email: 'arusso@manhattanskyline.com',        name: 'Anthony Russo (High-rise, NY)',   companyId: 'comp_gp07' },
  { alias: 'gp08', uid: 'user_gp08_maria',   email: 'mgonzalez@lonestarinfra.com',        name: 'Maria Gonzalez (Bridge, TX)',     companyId: 'comp_gp08' },
  { alias: 'gp09', uid: 'user_gp09_fiona',   email: 'fiona@highlanddevelopments.co.uk',   name: 'Fiona MacLeod (Incident, UK)',    companyId: 'comp_gp09' },
  { alias: 'gp10', uid: 'user_gp10_ben',     email: 'ben@yarrafitout.com.au',             name: 'Ben Kowalski (Closeout, AU)',     companyId: 'comp_gp10' },
];

export const DEFAULT_DEMO_ALIAS = 'gp04';

function lookupDemoUser(alias: string | null | undefined): DemoUser {
  const fallback = DEMO_USERS.find(u => u.alias === DEFAULT_DEMO_ALIAS)!;
  if (!alias) return fallback;
  return DEMO_USERS.find(u => u.alias === alias) ?? fallback;
}

function toClerkLikeUser(demo: DemoUser): ClerkLikeUser {
  return {
    id: demo.uid,
    primaryEmailAddress: { emailAddress: demo.email },
    fullName: demo.name,
    firstName: demo.name.split(' ')[0] ?? 'Demo',
    lastName: (demo.name.split(' ').slice(1).join(' ') || 'User').replace(/\s*\(.*\)\s*$/, ''),
    imageUrl: null,
    emailAddresses: [{ emailAddress: demo.email, verification: { status: 'verified' } }],
  };
}

// Back-compat: existing call sites import `DEMO_USER`. Keep it resolving to
// whatever user is currently active in sessionStorage so the default-selected
// user is correct on first render.
function readActiveDemoAlias(): string {
  try {
    return sessionStorage.getItem('kerf_demo_user') || DEFAULT_DEMO_ALIAS;
  } catch {
    return DEFAULT_DEMO_ALIAS;
  }
}

export const DEMO_USER: ClerkLikeUser = toClerkLikeUser(
  lookupDemoUser(readActiveDemoAlias()),
);

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
 *
 * Supports multi-user demo mode: the active user is stored in
 * ``sessionStorage.kerf_demo_user`` as an alias (e.g. ``gp03``), which the
 * token getter converts into ``demo-token-gp03``. Use ``switchDemoUser`` to
 * change the active user at runtime — session state is cleared and the
 * page reloads so React Query caches and the Shell context re-initialise
 * against the new tenant.
 */
export function useDemoAuthProvider(): AuthContextType {
  const demoActiveOnInit = sessionStorage.getItem('kerf_demo') === 'true';
  const initialAlias = readActiveDemoAlias();
  const initialDemoUser = lookupDemoUser(initialAlias);
  const [user, setUser] = useState<ClerkLikeUser | null>(
    demoActiveOnInit ? toClerkLikeUser(initialDemoUser) : null,
  );
  const [isDemoMode, setIsDemoMode] = useState(demoActiveOnInit);
  const [isNewUser, setIsNewUser] = useState(false);
  const [company, setCompany] = useState<CompanyData | null>(null);

  // Register demo token getter. Reads the alias on every call so a user
  // switch made after mount is picked up by the next API request.
  const tokenGetterSet = useRef(false);
  if (!tokenGetterSet.current) {
    const getter = async () => {
      if (sessionStorage.getItem('kerf_demo') !== 'true') return null;
      const alias = sessionStorage.getItem('kerf_demo_user') || DEFAULT_DEMO_ALIAS;
      return `demo-token-${alias}`;
    };
    setTokenGetter(getter);
    setPdfTokenGetter(getter);
    tokenGetterSet.current = true;
  }

  const signInDemo = useCallback(() => {
    const alias = sessionStorage.getItem('kerf_demo_user') || DEFAULT_DEMO_ALIAS;
    const demo = lookupDemoUser(alias);
    sessionStorage.setItem('kerf_demo', 'true');
    sessionStorage.setItem('kerf_demo_user', alias);
    sessionStorage.setItem('kerf_company_id', demo.companyId);
    setUser(toClerkLikeUser(demo));
    setIsDemoMode(true);
  }, []);

  const notConfigured = useCallback(async () => {
    throw new Error('Clerk is not configured. Please set VITE_CLERK_PUBLISHABLE_KEY.');
  }, []);

  const handleSignOut = useCallback(async () => {
    sessionStorage.removeItem('kerf_demo');
    sessionStorage.removeItem('kerf_demo_user');
    sessionStorage.removeItem('kerf_company_id');
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
    getToken: async () => {
      if (!isDemoMode) return null;
      const alias = sessionStorage.getItem('kerf_demo_user') || DEFAULT_DEMO_ALIAS;
      return `demo-token-${alias}`;
    },
    verifyToken: async () => null,
    clearNewUserFlag: useCallback(() => setIsNewUser(false), []),
  };
}

/**
 * Switch the active demo user at runtime (dev only).
 *
 * Writes the alias to sessionStorage then forces a full page reload so
 * React Query caches, the Shell context, and the chat session state all
 * reset against the new tenant. Any in-flight draft chat input is lost —
 * acceptable because this is a dev-only tool.
 */
export function switchDemoUser(alias: string): void {
  const demo = lookupDemoUser(alias);
  sessionStorage.setItem('kerf_demo', 'true');
  sessionStorage.setItem('kerf_demo_user', demo.alias);
  sessionStorage.setItem('kerf_company_id', demo.companyId);
  // Clear per-user caches that would otherwise leak into the next session
  sessionStorage.removeItem('kerf_chat_session');
  window.location.reload();
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
