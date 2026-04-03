import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider, QueryCache, MutationCache } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Toaster } from '@/components/ui/sonner';
import { AuthContext, useAuthProvider } from '@/hooks/useAuth';
import { LocaleProvider } from '@/lib/i18n';
import { App } from './App';
import './index.css';

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      if (error && typeof error === 'object' && 'status' in error) {
        const status = (error as { status: number }).status;
        // 401 and 403 are already handled by the API layer with redirects
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
      // Mutation errors are already toasted by the API layer,
      // so we only toast if it's not an ApiError (e.g. unexpected errors)
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

function AuthProvider({ children }: { children: React.ReactNode }) {
  const auth = useAuthProvider();
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <LocaleProvider>
          <App />
          <Toaster position="top-right" />
        </LocaleProvider>
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>
);
