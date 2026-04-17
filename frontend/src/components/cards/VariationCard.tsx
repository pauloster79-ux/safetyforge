/**
 * VariationCard — rendered for create_variation / detect_variation tool results.
 *
 * Shows description, status, amount, evidence chain.
 */

import { GitBranch, AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface VariationCardProps {
  result: Record<string, unknown>;
}

export function VariationCard({ result }: VariationCardProps) {
  // Detection results have flags; creation results have variation_id
  const isDetection = Array.isArray(result.flags);

  if (isDetection) {
    return <VariationDetectionCard result={result} />;
  }

  return <VariationCreationCard result={result} />;
}

function VariationCreationCard({ result }: { result: Record<string, unknown> }) {
  const description = (result.description || '') as string;
  const status = (result.status || 'draft') as string;
  const amount = result.amount as number | null | undefined;
  const number = result.number as number | undefined;
  const linkedWI = result.linked_work_items as number | undefined;
  const linkedEv = result.linked_evidence as number | undefined;
  const projectName = (result.project_name || '') as string;

  const statusVariant = (): 'default' | 'destructive' | 'secondary' => {
    if (['approved'].includes(status)) return 'default';
    if (['rejected'].includes(status)) return 'destructive';
    return 'secondary';
  };

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-machine-dark" />
          <div>
            <p className="text-[12px] font-semibold leading-tight">
              Variation {number != null ? `#${number}` : ''}
            </p>
            {projectName && <p className="text-[10px] text-muted-foreground">{projectName}</p>}
          </div>
        </div>
        <Badge variant={statusVariant()} className="text-[9px] uppercase shrink-0">
          {status.replace(/_/g, ' ')}
        </Badge>
      </div>

      {description && (
        <p className="mt-2 text-[10px] text-muted-foreground line-clamp-2">{description}</p>
      )}

      <div className="mt-2 flex items-center gap-3">
        {amount != null && (
          <span className="font-mono text-[12px] font-semibold">
            ${Number(amount).toLocaleString()}
          </span>
        )}
        {linkedWI != null && linkedWI > 0 && (
          <span className="text-[9px] text-muted-foreground">
            {linkedWI} work item{linkedWI > 1 ? 's' : ''}
          </span>
        )}
        {linkedEv != null && linkedEv > 0 && (
          <span className="text-[9px] text-muted-foreground">
            {linkedEv} evidence
          </span>
        )}
      </div>
    </div>
  );
}

function VariationDetectionCard({ result }: { result: Record<string, unknown> }) {
  const flags = (result.flags || []) as Array<Record<string, unknown>>;
  const flagCount = (result.flag_count || flags.length) as number;
  const logsAnalysed = result.logs_analysed as number | undefined;
  const projectName = (result.project_name || '') as string;

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className={`h-4 w-4 ${flagCount > 0 ? 'text-warning' : 'text-pass'}`} />
          <div>
            <p className="text-[12px] font-semibold leading-tight">Variation Detection</p>
            {projectName && <p className="text-[10px] text-muted-foreground">{projectName}</p>}
          </div>
        </div>
        <Badge
          variant={flagCount > 0 ? 'destructive' : 'default'}
          className="text-[9px] font-mono shrink-0"
        >
          {flagCount} flag{flagCount !== 1 ? 's' : ''}
        </Badge>
      </div>

      {flags.length > 0 && (
        <div className="mt-2 space-y-1">
          {flags.slice(0, 3).map((flag, i) => (
            <div key={i} className="rounded-sm bg-muted/50 px-2 py-1">
              <p className="font-mono text-[9px] text-muted-foreground">
                {String(flag.log_date || '')}
              </p>
              <p className="text-[10px] text-foreground line-clamp-1">
                {String(flag.work_performed || flag.reason || '')}
              </p>
            </div>
          ))}
        </div>
      )}

      {logsAnalysed != null && (
        <p className="mt-1 text-[9px] text-muted-foreground">
          {logsAnalysed} logs analysed
        </p>
      )}
    </div>
  );
}
