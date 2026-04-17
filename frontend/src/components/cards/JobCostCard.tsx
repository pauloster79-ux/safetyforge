/**
 * JobCostCard — rendered for get_job_cost_summary tool results.
 *
 * Shows estimated vs actual cost, margin, burn rate.
 */

import { DollarSign, TrendingUp, TrendingDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface JobCostCardProps {
  result: Record<string, unknown>;
}

function formatCurrency(value: number | null | undefined): string {
  if (value == null) return '-';
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function JobCostCard({ result }: JobCostCardProps) {
  const projectName = (result.project_name || result.name || '') as string;
  const estimated = result.estimated_cost as Record<string, number> | undefined;
  const actual = result.actual_cost as Record<string, number> | undefined;
  const variance = result.variance as number | undefined;
  const margin = result.margin as number | null | undefined;
  const burnRate = result.burn_rate as number | undefined;
  const workItemCount = result.work_item_count as number | undefined;
  const contractValue = result.contract_value as number | undefined;

  const estTotal = estimated?.total ?? 0;
  const actTotal = actual?.total ?? 0;
  const overBudget = (variance ?? 0) > 0;

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <DollarSign className="h-4 w-4 text-machine-dark" />
          <div>
            <p className="text-[12px] font-semibold leading-tight">Job Cost Summary</p>
            {projectName && <p className="text-[10px] text-muted-foreground">{projectName}</p>}
          </div>
        </div>
        {burnRate != null && (
          <Badge
            variant={burnRate > 100 ? 'destructive' : 'secondary'}
            className="text-[9px] font-mono shrink-0"
          >
            {burnRate}% burn
          </Badge>
        )}
      </div>

      <div className="mt-2 grid grid-cols-2 gap-2">
        <div>
          <p className="text-[9px] text-muted-foreground">Estimated</p>
          <p className="font-mono text-[12px] font-semibold">{formatCurrency(estTotal)}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground">Actual</p>
          <p className="font-mono text-[12px] font-semibold">{formatCurrency(actTotal)}</p>
        </div>
      </div>

      <div className="mt-2 flex items-center justify-between">
        <div className="flex items-center gap-1">
          {overBudget ? (
            <TrendingUp className="h-3 w-3 text-fail" />
          ) : (
            <TrendingDown className="h-3 w-3 text-pass" />
          )}
          <span className={`font-mono text-[10px] ${overBudget ? 'text-fail' : 'text-pass'}`}>
            {overBudget ? '+' : ''}{formatCurrency(variance ?? 0)} variance
          </span>
        </div>
        {margin != null && (
          <span className="font-mono text-[10px] text-muted-foreground">
            Margin: {formatCurrency(margin)}
          </span>
        )}
      </div>

      {(contractValue != null || workItemCount != null) && (
        <div className="mt-1 flex items-center gap-3">
          {contractValue != null && (
            <span className="font-mono text-[9px] text-muted-foreground">
              Contract: {formatCurrency(contractValue)}
            </span>
          )}
          {workItemCount != null && (
            <span className="font-mono text-[9px] text-muted-foreground">
              {workItemCount} work items
            </span>
          )}
        </div>
      )}
    </div>
  );
}
