import { useState } from 'react';
import { X, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';

const DISMISS_KEY = 'kerf_email_banner_dismissed';

export function EmailVerificationBanner() {
  const { user, isDemoMode } = useAuth();
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem(DISMISS_KEY) === 'true'
  );

  // Don't show if: demo mode, no user, email is verified, or banner dismissed
  if (isDemoMode || !user) return null;

  const emailVerified = user.emailAddresses?.[0]?.verification?.status === 'verified';
  if (emailVerified || dismissed) return null;

  const handleDismiss = () => {
    sessionStorage.setItem(DISMISS_KEY, 'true');
    setDismissed(true);
  };

  return (
    <div
      className="flex items-center justify-between gap-3 px-4 py-2.5"
      style={{
        background: 'var(--warn-bg)',
        borderBottom: '1px solid var(--warn)',
        fontFamily: 'IBM Plex Sans, sans-serif',
      }}
    >
      <div className="flex items-center gap-2 text-[13px]" style={{ color: 'var(--concrete-800)' }}>
        <Mail className="h-4 w-4 flex-shrink-0" style={{ color: 'var(--warn)' }} />
        <span>
          Please verify your email address. Check your inbox for a verification link.
        </span>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          onClick={handleDismiss}
          className="flex items-center justify-center p-1 transition-colors hover:bg-[var(--warn-bg)]"
          style={{ borderRadius: 3, color: 'var(--concrete-500)' }}
          aria-label="Dismiss email verification banner"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
