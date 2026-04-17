/**
 * Dev-only demo-user switcher.
 *
 * Floats in the bottom-left of the shell when:
 *  - we're in a development build (`import.meta.env.DEV`), AND
 *  - the active auth provider is the demo provider (no Clerk configured OR
 *    Clerk in demo fallback mode).
 *
 * Selecting a different user writes the alias to sessionStorage and reloads
 * the page. Reload is intentional — it forces React Query, the Shell
 * context, and the chat session to re-initialise against the new tenant
 * so no stale data leaks across the user boundary.
 */

import { UserCog } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DEMO_USERS,
  DEFAULT_DEMO_ALIAS,
  switchDemoUser,
  useAuth,
} from '@/hooks/useAuth';

function readActiveAlias(): string {
  try {
    return sessionStorage.getItem('kerf_demo_user') || DEFAULT_DEMO_ALIAS;
  } catch {
    return DEFAULT_DEMO_ALIAS;
  }
}

export function DemoUserSwitcher() {
  const { isDemoMode, clerkConfigured } = useAuth();

  // Only render in dev mode AND when the demo auth provider is active.
  // If Clerk is configured and the user is signed in via Clerk, we never
  // want this switcher to appear — it would be confusing and wouldn't work.
  if (!import.meta.env.DEV) return null;
  if (clerkConfigured && !isDemoMode) return null;
  if (!isDemoMode) return null;

  const activeAlias = readActiveAlias();

  return (
    <div className="flex items-center gap-1.5 rounded-md border border-dashed border-amber-500 bg-background/95 px-1.5 py-1">
      <UserCog className="h-3 w-3 text-amber-600" />
      <span className="text-[9px] uppercase tracking-wide text-muted-foreground">
        Dev
      </span>
      <Select
        value={activeAlias}
        onValueChange={(next) => {
          if (next && next !== activeAlias) switchDemoUser(next);
        }}
      >
        <SelectTrigger
          className="h-7 w-[220px] border-none bg-transparent px-2 text-xs shadow-none focus:ring-0"
          aria-label="Switch demo user"
        >
          <SelectValue placeholder="Select demo user" />
        </SelectTrigger>
        <SelectContent align="start">
          {DEMO_USERS.map((u) => (
            <SelectItem key={u.alias} value={u.alias} className="text-xs">
              <span className="font-mono text-[10px] uppercase text-muted-foreground">
                {u.alias}
              </span>
              <span className="ml-2">{u.name}</span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
