/**
 * ConflictAlertCard — rendered for detect_conflicts tool results.
 *
 * Shows scheduling conflicts with type, affected worker, and resolution.
 */

import { AlertTriangle, Shield, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ConflictAlertCardProps {
  result: Record<string, unknown>;
}

export function ConflictAlertCard({ result }: ConflictAlertCardProps) {
  const conflicts = (result.conflicts || []) as Array<Record<string, unknown>>;
  const totalConflicts = (result.total_conflicts ?? conflicts.length) as number;
  const hasConflicts = (result.has_conflicts ?? totalConflicts > 0) as boolean;

  const typeIcon = (type: string) => {
    switch (type) {
      case 'cert_expiry': return <Shield className="h-3 w-3 text-fail" />;
      case 'double_booking': return <Users className="h-3 w-3 text-fail" />;
      default: return <AlertTriangle className="h-3 w-3 text-warn" />;
    }
  };

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className={`h-4 w-4 ${hasConflicts ? 'text-fail' : 'text-pass'}`} />
          <p className="text-[12px] font-semibold leading-tight">Conflict Detection</p>
        </div>
        <Badge
          variant={hasConflicts ? 'destructive' : 'default'}
          className="text-[9px] uppercase shrink-0"
        >
          {hasConflicts ? `${totalConflicts} found` : 'Clear'}
        </Badge>
      </div>

      {conflicts.length > 0 && (
        <div className="mt-2 space-y-1.5">
          {conflicts.slice(0, 5).map((conflict, i) => (
            <div key={i} className="rounded bg-muted/50 px-2 py-1.5">
              <div className="flex items-start gap-1.5">
                {typeIcon(conflict.type as string)}
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] font-medium leading-snug">
                    {conflict.description as string}
                  </p>
                  {!!conflict.resolution && (
                    <p className="mt-0.5 text-[9px] text-muted-foreground">
                      Fix: {String(conflict.resolution)}
                    </p>
                  )}
                </div>
                <Badge variant="outline" className="text-[8px] shrink-0">
                  {(conflict.type as string || 'unknown').replace(/_/g, ' ')}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      )}

      {!hasConflicts && (
        <p className="mt-2 text-[10px] text-muted-foreground">
          No scheduling conflicts detected.
        </p>
      )}
    </div>
  );
}
