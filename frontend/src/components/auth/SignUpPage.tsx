import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { HardHat, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import { ROUTES } from '@/lib/constants';

export function SignUpPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { signUpWithEmail, signInWithGoogle, signInDemo, clerkConfigured, verifyToken } = useAuth();
  const navigate = useNavigate();

  const navigateAfterAuth = async () => {
    const result = await verifyToken();
    if (result?.is_new_user) {
      navigate(ROUTES.ONBOARDING, { replace: true });
    } else {
      navigate(ROUTES.DASHBOARD, { replace: true });
    }
  };

  const handleEmailSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setLoading(true);
    try {
      await signUpWithEmail(email, password);
      await navigateAfterAuth();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create account';
      if (message.includes('already') || message.includes('taken') || message.includes('exists')) {
        setError('An account with this email already exists. Please sign in instead.');
      } else if (message.includes('weak') || message.includes('password')) {
        setError('Password is too weak. Please use at least 8 characters with a mix of letters and numbers.');
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignUp = async () => {
    setError('');
    setLoading(true);
    try {
      await signInWithGoogle();
      await navigateAfterAuth();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to sign up with Google';
      if (!message.includes('popup-closed-by-user')) {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
            <HardHat className="h-7 w-7 text-white" />
          </div>
          <h1 className="mt-4 text-2xl font-bold text-foreground">
            Kerf
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Create your account to get started
          </p>
        </div>

        <Card>
          <CardHeader className="text-center">
            <CardTitle>Create an account</CardTitle>
            <CardDescription>
              Safety, daily logs, and time tracking for contractors
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {!clerkConfigured && (
              <div className="mb-4">
                <Button
                  className="w-full bg-primary hover:bg-[var(--machine-dark)] text-primary-foreground text-base py-5"
                  onClick={() => {
                    signInDemo();
                    navigate(ROUTES.DASHBOARD, { replace: true });
                  }}
                >
                  <HardHat className="mr-2 h-5 w-5" />
                  Try Demo — No Account Needed
                </Button>
                <p className="mt-2 text-center text-xs text-muted-foreground">
                  Explore the full app with sample data
                </p>
                <div className="my-4 flex items-center gap-3">
                  <Separator className="flex-1" />
                  <span className="text-xs text-muted-foreground">OR CREATE ACCOUNT</span>
                  <Separator className="flex-1" />
                </div>
              </div>
            )}

            <Button
              variant="outline"
              className="w-full"
              onClick={handleGoogleSignUp}
              disabled={loading}
            >
              <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Continue with Google
            </Button>

            <div className="my-4 flex items-center gap-3">
              <Separator className="flex-1" />
              <span className="text-xs text-muted-foreground">OR</span>
              <Separator className="flex-1" />
            </div>

            <form onSubmit={handleEmailSignUp} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Work Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="At least 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  disabled={loading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                  disabled={loading}
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-[var(--concrete-800)] hover:bg-[var(--concrete-700)]"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Create Account'
                )}
              </Button>
            </form>

            <p className="mt-4 text-center text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link to={ROUTES.LOGIN} className="font-medium text-[var(--machine-dark)] hover:text-primary">
                Sign in
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
