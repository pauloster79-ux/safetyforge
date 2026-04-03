import { useAuth } from '@/hooks/useAuth';
import { Loader2 } from 'lucide-react';

interface PublicRouteProps {
  children: React.ReactNode;
  fallback: React.ReactNode;
}

/**
 * Route wrapper for public pages (landing, login, signup).
 *
 * Renders `children` when no user is authenticated.
 * Renders `fallback` (typically a redirect) when a user is already logged in.
 * Shows a loading spinner while auth state is being resolved.
 */
export function PublicRoute({ children, fallback }: PublicRouteProps) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-muted">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (user) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
