/**
 * ExclusionCard -- rendered for exclusion-related tool results.
 *
 * Shows category badge, statement, and partial inclusion when present.
 */

import { Ban, Info } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ExclusionCardProps {
  result: Record<string, unknown>;
}

const CATEGORY_COLORS: Record<string, string> = {
  scope: 'bg-blue-100 text-blue-800',
  trade_boundary: 'bg-purple-100 text-purple-800',
  conditions: 'bg-amber-100 text-amber-800',
  risk: 'bg-red-100 text-red-800',
  regulatory: 'bg-rose-100 text-rose-800',
};

export function ExclusionCard({ result }: ExclusionCardProps) {
  const statement = (result.statement || 'Exclusion') as string;
  const category = (result.category || '') as string;
  const partialInclusion = (result.partial_inclusion || '') as string;
  const projectName = (result.project_name || '') as string;

  const badgeClass = CATEGORY_COLORS[category] || 'bg-muted text-muted-foreground';

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Ban className="h-4 w-4 text-machine-dark shrink-0" />
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

      {partialInclusion && (
        <div className="mt-2 flex items-center gap-1">
          <Info className="h-3 w-3 text-muted-foreground shrink-0" />
          <span className="text-[10px] text-muted-foreground">
            Partially includes: {partialInclusion}
          </span>
        </div>
      )}
    </div>
  );
}
