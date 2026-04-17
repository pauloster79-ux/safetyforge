/**
 * InvoiceCard — rendered for generate_invoice / invoice-related tool results.
 *
 * Shows invoice number, amount, status, due date, days until/overdue.
 */

import { Receipt, DollarSign, Calendar, AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface InvoiceCardProps {
  result: Record<string, unknown>;
}

export function InvoiceCard({ result }: InvoiceCardProps) {
  const invoiceId = (result.invoice_id || result.id || '') as string;
  const invoiceNumber = (result.invoice_number || result.number || invoiceId) as string;
  const amount = (result.amount ?? result.invoice_amount ?? 0) as number;
  const status = (result.status || result.invoice_status || 'draft') as string;
  const dueDate = (result.due_date || '') as string;
  const projectName = (result.project_name || '') as string;
  const currency = (result.currency || 'USD') as string;
  const daysOverdue = result.days_overdue as number | undefined;
  const daysUntilDue = result.days_until_due as number | undefined;

  const fmt = (v: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(v);

  const statusVariant = (): 'default' | 'destructive' | 'secondary' => {
    const s = status.toLowerCase();
    if (['paid'].includes(s)) return 'default';
    if (['overdue', 'void'].includes(s)) return 'destructive';
    return 'secondary';
  };

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Receipt className="h-4 w-4 text-machine-dark" />
          <p className="text-[12px] font-semibold leading-tight">
            {invoiceNumber !== invoiceId ? `#${invoiceNumber}` : 'Invoice'}
            {projectName && <span className="font-normal text-muted-foreground"> — {projectName}</span>}
          </p>
        </div>
        <Badge variant={statusVariant()} className="text-[9px] uppercase shrink-0">
          {status.replace(/_/g, ' ')}
        </Badge>
      </div>

      <div className="mt-2 flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-1">
          <DollarSign className="h-3 w-3 text-muted-foreground" />
          <span className="font-mono text-[11px] font-semibold">{fmt(amount)}</span>
        </div>

        {dueDate && (
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground">Due: {dueDate}</span>
          </div>
        )}

        {daysOverdue != null && daysOverdue > 0 && (
          <div className="flex items-center gap-1">
            <AlertTriangle className="h-3 w-3 text-destructive" />
            <span className="text-[10px] text-destructive font-medium">{daysOverdue}d overdue</span>
          </div>
        )}

        {daysUntilDue != null && daysUntilDue >= 0 && (
          <span className="text-[10px] text-muted-foreground">{daysUntilDue}d until due</span>
        )}
      </div>

      {Array.isArray(result.lines) && (result.lines as Record<string, unknown>[]).length > 0 && (
        <div className="mt-2 border-t border-border pt-2">
          <p className="text-[9px] font-medium uppercase text-muted-foreground mb-1">Lines</p>
          {(result.lines as Record<string, unknown>[]).slice(0, 4).map((line, idx) => (
            <div key={idx} className="flex justify-between text-[10px]">
              <span className="truncate mr-2">{line.description as string}</span>
              <span className="font-mono shrink-0">{fmt((line.amount ?? 0) as number)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
