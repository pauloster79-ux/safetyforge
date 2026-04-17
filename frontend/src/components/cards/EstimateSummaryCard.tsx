/**
 * EstimateSummaryCard — rendered for get_estimate_summary tool results.
 *
 * Shows project name, total items, labour total, materials total, margin, grand total.
 */

import { Calculator, Layers, DollarSign } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface EstimateSummaryCardProps {
  result: Record<string, unknown>;
}

export function EstimateSummaryCard({ result }: EstimateSummaryCardProps) {
  const projectName = (result.project_name || 'Project Estimate') as string;
  const projectStatus = (result.project_status || '') as string;
  const itemCount = (result.item_count ?? 0) as number;
  // Backend returns values in cents — convert to dollars
  const totalLabour = ((result.total_labour_cents ?? result.total_labour ?? 0) as number) / 100;
  const totalMaterials = ((result.total_items_cents ?? result.total_materials ?? 0) as number) / 100;
  const grandTotal = ((result.grand_total_cents ?? result.grand_total ?? 0) as number) / 100;
  const currency = (result.currency || 'USD') as string;
  const assumptionCount = (result.assumption_count ?? 0) as number;
  const exclusionCount = (result.exclusion_count ?? 0) as number;

  const fmt = (v: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(v);

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Calculator className="h-4 w-4 text-machine-dark" />
          <p className="text-[12px] font-semibold leading-tight">{projectName}</p>
        </div>
        {projectStatus && (
          <Badge variant="secondary" className="text-[9px] uppercase shrink-0">
            {projectStatus.replace(/_/g, ' ')}
          </Badge>
        )}
      </div>

      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1">
        <div className="flex items-center gap-1">
          <Layers className="h-3 w-3 text-muted-foreground" />
          <span className="text-[10px] text-muted-foreground">{itemCount} items</span>
        </div>
        <div className="flex items-center gap-1">
          <DollarSign className="h-3 w-3 text-muted-foreground" />
          <span className="font-mono text-[10px] text-muted-foreground">Labour: {fmt(totalLabour)}</span>
        </div>
        <div>
          <span className="font-mono text-[10px] text-muted-foreground">Materials: {fmt(totalMaterials)}</span>
        </div>
        <div>
          <span className="font-mono text-[11px] font-semibold">Total: {fmt(grandTotal)}</span>
        </div>
      </div>

      {(assumptionCount > 0 || exclusionCount > 0) && (
        <div className="mt-1 flex items-center gap-3 text-[10px] text-muted-foreground">
          {assumptionCount > 0 && <span>{assumptionCount} assumption{assumptionCount !== 1 ? 's' : ''}</span>}
          {exclusionCount > 0 && <span>{exclusionCount} exclusion{exclusionCount !== 1 ? 's' : ''}</span>}
        </div>
      )}

      {Array.isArray(result.items) && (result.items as Record<string, unknown>[]).length > 0 && (
        <div className="mt-2 border-t border-border pt-2">
          <p className="text-[9px] font-medium uppercase text-muted-foreground mb-1">Line Items</p>
          {(result.items as Record<string, unknown>[]).slice(0, 5).map((item, idx) => (
            <div key={idx} className="flex justify-between text-[10px]">
              <span className="truncate mr-2">{item.description as string}</span>
              <span className="font-mono shrink-0">{fmt(((item.line_total ?? item.sell_price_cents ?? 0) as number) / 100)}</span>
            </div>
          ))}
          {(result.items as Record<string, unknown>[]).length > 5 && (
            <p className="text-[9px] text-muted-foreground mt-1">
              +{(result.items as Record<string, unknown>[]).length - 5} more items
            </p>
          )}
        </div>
      )}
    </div>
  );
}
