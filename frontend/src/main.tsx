import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider, QueryCache, MutationCache } from '@tanstack/react-query';
import { ClerkProvider } from '@clerk/clerk-react';
import { toast } from 'sonner';
import { Toaster } from '@/components/ui/sonner';
import { AuthContext, useDemoAuthProvider } from '@/hooks/useAuth';
import { useClerkAuthProvider } from '@/hooks/useClerkAuth';
import { LocaleProvider } from '@/lib/i18n';
import { CLERK_PUBLISHABLE_KEY, isConfigured as clerkIsConfigured } from '@/lib/clerk';
import { App } from './App';
import './index.css';

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      if (error && typeof error === 'object' && 'status' in error) {
        const status = (error as { status: number }).status;
        if (status === 401 || status === 403) return;
      }
      toast.error(error.message || 'An error occurred while fetching data');
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      if (error && typeof error === 'object' && 'status' in error) {
        const status = (error as { status: number }).status;
        if (status === 401 || status === 403) return;
      }
      if (!(error && typeof error === 'object' && 'status' in error)) {
        toast.error(error.message || 'An error occurred');
      }
    },
  }),
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});

/**
 * Auth provider when Clerk is configured — uses Clerk hooks (safe inside ClerkProvider).
 */
function ClerkAuthProvider({ children }: { children: React.ReactNode }) {
  const auth = useClerkAuthProvider();
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

/**
 * Auth provider when Clerk is NOT configured — demo-only mode.
 */
function DemoAuthProvider({ children }: { children: React.ReactNode }) {
  const auth = useDemoAuthProvider();
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <LocaleProvider>
        {children}
        <Toaster position="top-right" />
      </LocaleProvider>
    </QueryClientProvider>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {clerkIsConfigured ? (
      <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
        <ClerkAuthProvider>
          <AppShell>
            <App />
          </AppShell>
        </ClerkAuthProvider>
      </ClerkProvider>
    ) : (
      <DemoAuthProvider>
        <AppShell>
          <App />
        </AppShell>
      </DemoAuthProvider>
    )}
  </StrictMode>
);
