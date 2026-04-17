/**
 * PaymentStatusCard — rendered for track_payment_status tool results.
 *
 * Shows project invoiced total, paid total, outstanding, overdue amount.
 */

import { Banknote, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface PaymentStatusCardProps {
  result: Record<string, unknown>;
}

export function PaymentStatusCard({ result }: PaymentStatusCardProps) {
  const projectName = (result.project_name || 'Payment Status') as string;
  const totalInvoiced = (result.total_invoiced ?? 0) as number;
  const totalPaid = (result.total_paid ?? 0) as number;
  const totalOutstanding = (result.total_outstanding ?? 0) as number;
  const totalOverdue = (result.total_overdue ?? 0) as number;
  const invoiceCount = (result.invoice_count ?? 0) as number;
  const asOf = (result.as_of || '') as string;

  const fmt = (v: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v);

  const paidPct = totalInvoiced > 0 ? Math.round((totalPaid / totalInvoiced) * 100) : 0;

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Banknote className="h-4 w-4 text-machine-dark" />
          <p className="text-[12px] font-semibold leading-tight">{projectName}</p>
        </div>
        <Badge variant="secondary" className="text-[9px] uppercase shrink-0">
          {invoiceCount} invoices
        </Badge>
      </div>

      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1">
        <div>
          <dt className="font-mono text-[9px] uppercase text-muted-foreground">Invoiced</dt>
          <dd className="font-mono text-[11px] font-medium">{fmt(totalInvoiced)}</dd>
        </div>
        <div>
          <dt className="font-mono text-[9px] uppercase text-muted-foreground">Paid</dt>
          <dd className="flex items-center gap-1">
            <CheckCircle className="h-3 w-3 text-green-600" />
            <span className="font-mono text-[11px] font-medium">{fmt(totalPaid)}</span>
            <span className="text-[9px] text-muted-foreground">({paidPct}%)</span>
          </dd>
        </div>
        <div>
          <dt className="font-mono text-[9px] uppercase text-muted-foreground">Outstanding</dt>
          <dd className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3 text-muted-foreground" />
            <span className="font-mono text-[11px] font-medium">{fmt(totalOutstanding)}</span>
          </dd>
        </div>
        {totalOverdue > 0 && (
          <div>
            <dt className="font-mono text-[9px] uppercase text-muted-foreground">Overdue</dt>
            <dd className="flex items-center gap-1">
              <AlertTriangle className="h-3 w-3 text-destructive" />
              <span className="font-mono text-[11px] font-medium text-destructive">{fmt(totalOverdue)}</span>
            </dd>
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div className="mt-2">
        <div className="h-1.5 w-full rounded-full bg-muted">
          <div
            className="h-1.5 rounded-full bg-green-600 transition-all"
            style={{ width: `${paidPct}%` }}
          />
        </div>
      </div>

      {asOf && (
        <p className="mt-1 text-[9px] text-muted-foreground">As of {asOf}</p>
      )}
    </div>
  );
}
