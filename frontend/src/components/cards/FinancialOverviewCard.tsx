/**
 * FinancialOverviewCard — rendered for get_financial_overview tool results.
 *
 * Shows contract value, costs, variations, profit/loss.
 */

import { Wallet, TrendingUp, TrendingDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface FinancialOverviewCardProps {
  result: Record<string, unknown>;
}

function fmt(value: number | null | undefined): string {
  if (value == null) return '-';
  return `$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function FinancialOverviewCard({ result }: FinancialOverviewCardProps) {
  const projectName = (result.project_name || result.name || '') as string;
  const contractValue = result.contract_value as number | undefined;
  const actualCost = result.actual_cost as number | undefined;
  const estimatedCost = result.estimated_cost as number | undefined;
  const projectedProfit = result.projected_profit as number | undefined;
  const profitMargin = result.profit_margin_pct as number | undefined;
  const variationCount = result.variation_count as number | undefined;
  const pendingVariations = result.pending_variations as number | undefined;
  const approvedVariations = result.approved_variations as number | undefined;
  const invoicedTotal = result.invoiced_total as number | undefined;
  const paidTotal = result.paid_total as number | undefined;
  const outstanding = result.outstanding as number | undefined;

  const profitable = (projectedProfit ?? 0) >= 0;

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Wallet className="h-4 w-4 text-machine-dark" />
          <div>
            <p className="text-[12px] font-semibold leading-tight">Financial Overview</p>
            {projectName && <p className="text-[10px] text-muted-foreground">{projectName}</p>}
          </div>
        </div>
        {profitMargin != null && (
          <Badge
            variant={profitable ? 'default' : 'destructive'}
            className="text-[9px] font-mono shrink-0"
          >
            {profitMargin}% margin
          </Badge>
        )}
      </div>

      {/* Key financials */}
      <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1">
        <div>
          <p className="text-[9px] text-muted-foreground">Contract</p>
          <p className="font-mono text-[11px] font-semibold">{fmt(contractValue)}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground">Actual Cost</p>
          <p className="font-mono text-[11px] font-semibold">{fmt(actualCost)}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground">Estimated</p>
          <p className="font-mono text-[11px]">{fmt(estimatedCost)}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground">Profit</p>
          <div className="flex items-center gap-1">
            {profitable ? (
              <TrendingUp className="h-3 w-3 text-pass" />
            ) : (
              <TrendingDown className="h-3 w-3 text-fail" />
            )}
            <p className={`font-mono text-[11px] font-semibold ${profitable ? 'text-pass' : 'text-fail'}`}>
              {fmt(projectedProfit)}
            </p>
          </div>
        </div>
      </div>

      {/* Variations row */}
      {(variationCount != null || approvedVariations != null) && (
        <div className="mt-2 flex items-center gap-3">
          {approvedVariations != null && (
            <span className="font-mono text-[9px] text-muted-foreground">
              Variations: {fmt(approvedVariations)}
            </span>
          )}
          {variationCount != null && (
            <span className="text-[9px] text-muted-foreground">
              ({variationCount} approved)
            </span>
          )}
          {pendingVariations != null && pendingVariations > 0 && (
            <span className="text-[9px] text-warning">
              {pendingVariations} pending
            </span>
          )}
        </div>
      )}

      {/* Payment row */}
      {(invoicedTotal != null || paidTotal != null) && (
        <div className="mt-1 flex items-center gap-3">
          {invoicedTotal != null && (
            <span className="font-mono text-[9px] text-muted-foreground">
              Invoiced: {fmt(invoicedTotal)}
            </span>
          )}
          {paidTotal != null && (
            <span className="font-mono text-[9px] text-muted-foreground">
              Paid: {fmt(paidTotal)}
            </span>
          )}
          {outstanding != null && outstanding > 0 && (
            <span className="font-mono text-[9px] text-warning">
              Outstanding: {fmt(outstanding)}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
