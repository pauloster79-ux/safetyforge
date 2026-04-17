/**
 * WorkItemCard — rendered for work-item related tool results.
 *
 * Shows description, state, computed cost, assigned workers.
 */

import { Hammer, DollarSign, User } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface WorkItemCardProps {
  result: Record<string, unknown>;
}

export function WorkItemCard({ result }: WorkItemCardProps) {
  const description = (result.description || result.work_item_description || result.name || result.title || 'Work Item') as string;
  const state = (result.state || result.status || '') as string;

  // Cost from backend — values are in cents, convert to dollars
  const sellPriceCents = Number(result.sell_price_cents ?? result.line_total ?? 0);
  const labourCents = Number(result.labour_total_cents ?? 0);
  const itemsCents = Number(result.items_total_cents ?? 0);
  const costEstimate = sellPriceCents > 0 ? sellPriceCents / 100 : null;
  const labourDollars = labourCents > 0 ? labourCents / 100 : null;
  const itemsDollars = itemsCents > 0 ? itemsCents / 100 : null;
  const quantity = result.quantity as number | undefined;
  const unit = (result.unit || '') as string;

  // Assigned workers — could be a string or an array from assign_workers
  const assigned = result.assigned as Array<Record<string, unknown>> | undefined;
  const assignedTo = (result.assigned_to || result.worker_name || '') as string;
  const assignedDisplay = assignedTo ||
    (Array.isArray(assigned) && assigned.length > 0
      ? assigned.map(a => String(a.worker_name || a.crew_name || a.name || '')).filter(Boolean).join(', ')
      : '');

  const projectName = (result.project_name || '') as string;

  const stateVariant = (): 'default' | 'destructive' | 'secondary' => {
    const s = state.toLowerCase();
    if (['complete', 'completed', 'done'].includes(s)) return 'default';
    if (['blocked', 'overdue'].includes(s)) return 'destructive';
    return 'secondary';
  };

  const fmtCost = (v: unknown) => {
    const n = Number(v);
    if (isNaN(n)) return String(v);
    return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
  };

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Hammer className="h-4 w-4 text-machine-dark shrink-0" />
          <div className="min-w-0">
            <p className="text-[12px] font-semibold leading-tight truncate">{description}</p>
            {projectName && <p className="text-[10px] text-muted-foreground truncate">{projectName}</p>}
          </div>
        </div>
        {state && (
          <Badge variant={stateVariant()} className="text-[9px] uppercase shrink-0">
            {state.replace(/_/g, ' ')}
          </Badge>
        )}
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-3">
        {quantity != null && quantity > 0 && (
          <span className="text-[10px] text-muted-foreground">{quantity} {unit}</span>
        )}
        {labourDollars != null && (
          <span className="font-mono text-[10px] text-muted-foreground">Labour: {fmtCost(labourDollars)}</span>
        )}
        {itemsDollars != null && (
          <span className="font-mono text-[10px] text-muted-foreground">Materials: {fmtCost(itemsDollars)}</span>
        )}
        {costEstimate != null && (
          <div className="flex items-center gap-1">
            <DollarSign className="h-3 w-3 text-muted-foreground" />
            <span className="font-mono text-[10px] font-semibold">{fmtCost(costEstimate)}</span>
          </div>
        )}
        {assignedDisplay && (
          <div className="flex items-center gap-1">
            <User className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground truncate max-w-[120px]">{assignedDisplay}</span>
          </div>
        )}
      </div>
    </div>
  );
}
