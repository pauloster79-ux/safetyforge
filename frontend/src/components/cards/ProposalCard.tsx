/**
 * ProposalCard — rendered for generate_proposal tool results.
 *
 * Shows project name, total value, status, generated date, client info.
 */

import { FileText, DollarSign, Calendar, User } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ProposalCardProps {
  result: Record<string, unknown>;
}

export function ProposalCard({ result }: ProposalCardProps) {
  const projectName = (result.project_name || 'Proposal') as string;
  const status = (result.status || 'draft') as string;
  const grandTotal = (result.grand_total ?? 0) as number;
  const itemCount = (result.item_count ?? 0) as number;
  const currency = (result.currency || 'USD') as string;
  const terms = (result.terms || '') as string;
  const generatedAt = (result.generated_at || '') as string;
  const client = result.client as Record<string, unknown> | null;

  const fmt = (v: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(v);

  const dateStr = generatedAt
    ? new Date(generatedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : '';

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-machine-dark" />
          <p className="text-[12px] font-semibold leading-tight">Proposal: {projectName}</p>
        </div>
        <Badge variant="secondary" className="text-[9px] uppercase shrink-0">
          {status.replace(/_/g, ' ')}
        </Badge>
      </div>

      <div className="mt-2 flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-1">
          <DollarSign className="h-3 w-3 text-muted-foreground" />
          <span className="font-mono text-[11px] font-semibold">{fmt(grandTotal)}</span>
        </div>
        <span className="text-[10px] text-muted-foreground">{itemCount} items</span>
        {terms && (
          <span className="text-[10px] text-muted-foreground">{terms}</span>
        )}
      </div>

      <div className="mt-2 flex items-center gap-4">
        {client && !!(client as Record<string, unknown>).name && (
          <div className="flex items-center gap-1">
            <User className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground">{String((client as Record<string, unknown>).name)}</span>
          </div>
        )}
        {dateStr && (
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground">{dateStr}</span>
          </div>
        )}
      </div>
    </div>
  );
}
