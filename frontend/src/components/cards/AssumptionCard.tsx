/**
 * AssumptionCard -- rendered for assumption-related tool results.
 *
 * Shows category badge, statement, variation trigger indicator,
 * and relied-on value when present.
 */

import { ShieldAlert, AlertTriangle, Ruler } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface AssumptionCardProps {
  result: Record<string, unknown>;
}

const CATEGORY_COLORS: Record<string, string> = {
  schedule: 'bg-blue-100 text-blue-800',
  quantities: 'bg-emerald-100 text-emerald-800',
  access: 'bg-amber-100 text-amber-800',
  coordination: 'bg-purple-100 text-purple-800',
  site_conditions: 'bg-orange-100 text-orange-800',
  design_completeness: 'bg-cyan-100 text-cyan-800',
  pricing: 'bg-rose-100 text-rose-800',
  regulatory: 'bg-red-100 text-red-800',
};

export function AssumptionCard({ result }: AssumptionCardProps) {
  const statement = (result.statement || 'Assumption') as string;
  const category = (result.category || '') as string;
  const variationTrigger = result.variation_trigger as boolean | undefined;
  const triggerDescription = (result.trigger_description || '') as string;
  const reliedOnValue = (result.relied_on_value || '') as string;
  const reliedOnUnit = (result.relied_on_unit || '') as string;
  const projectName = (result.project_name || '') as string;

  const badgeClass = CATEGORY_COLORS[category] || 'bg-muted text-muted-foreground';

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <ShieldAlert className="h-4 w-4 text-machine-dark shrink-0" />
          <div className="min-w-0">
            <p className="text-[12px] font-semibold leading-tight">{statement}</p>
            {projectName && <p className="text-[10px] text-muted-foreground truncate">{projectName}</p>}
          </div>
        </div>
        {category && (
          <Badge className={`text-[9px] uppercase shrink-0 ${badgeClass} border-0`}>
            {category.replace(/_/g, ' ')}
          </Badge>
        )}
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-3">
        {variationTrigger && (
          <div className="flex items-center gap-1">
            <AlertTriangle className="h-3 w-3 text-amber-500" />
            <span className="text-[10px] font-medium text-amber-700">
              Variation trigger{triggerDescription ? `: ${triggerDescription}` : ''}
            </span>
          </div>
        )}
        {reliedOnValue && (
          <div className="flex items-center gap-1">
            <Ruler className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground">
              Based on: {reliedOnValue}{reliedOnUnit ? ` ${reliedOnUnit}` : ''}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
