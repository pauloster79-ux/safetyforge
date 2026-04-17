/**
 * GenericEntityCard — fallback card for any tool result without a specific card.
 *
 * Renders a title, key-value pairs, and a status badge.
 */

import { Badge } from '@/components/ui/badge';

interface GenericEntityCardProps {
  toolName: string;
  result: Record<string, unknown>;
}

function inferTitle(result: Record<string, unknown>, toolName: string): string {
  for (const key of ['name', 'title', 'summary', 'project_name', 'worker_name']) {
    if (typeof result[key] === 'string') return result[key] as string;
  }
  return toolName.replace(/_/g, ' ');
}

function inferStatus(result: Record<string, unknown>): string | null {
  for (const key of ['status', 'compliance_status', 'state']) {
    if (typeof result[key] === 'string') return result[key] as string;
  }
  return null;
}

function statusVariant(status: string): 'default' | 'destructive' | 'secondary' {
  const lower = status.toLowerCase();
  if (['pass', 'compliant', 'active', 'complete', 'completed', 'ok'].includes(lower)) return 'default';
  if (['fail', 'non_compliant', 'critical', 'overdue', 'expired'].includes(lower)) return 'destructive';
  return 'secondary';
}

/** Keys to skip in the key-value display */
const SKIP_KEYS = new Set(['name', 'title', 'summary', 'status', 'compliance_status', 'state', 'id', 'company_id']);

export function GenericEntityCard({ toolName, result }: GenericEntityCardProps) {
  const title = inferTitle(result, toolName);
  const status = inferStatus(result);

  const entries = Object.entries(result).filter(
    ([key, val]) => !SKIP_KEYS.has(key) && val != null && typeof val !== 'object',
  );

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-[12px] font-semibold leading-tight">{title}</p>
        {status && (
          <Badge variant={statusVariant(status)} className="text-[9px] uppercase shrink-0">
            {status.replace(/_/g, ' ')}
          </Badge>
        )}
      </div>
      {entries.length > 0 && (
        <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1">
          {entries.slice(0, 6).map(([key, val]) => (
            <div key={key}>
              <dt className="font-mono text-[9px] uppercase text-muted-foreground">{key.replace(/_/g, ' ')}</dt>
              <dd className="text-[11px] font-medium truncate">{String(val)}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
