/**
 * CapacityCard — rendered for check_capacity tool results.
 *
 * Shows active projects count, worker utilisation, and upcoming availability.
 */

import { BarChart3, Users, FolderKanban, TrendingUp } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface CapacityCardProps {
  result: Record<string, unknown>;
}

export function CapacityCard({ result }: CapacityCardProps) {
  const activeProjects = (result.active_projects ?? '—') as number | string;
  const totalWorkers = (result.total_workers ?? '—') as number | string;
  const unassigned = (result.unassigned_workers ?? 0) as number;
  const utilisation = (result.utilisation_pct ?? 0) as number;
  const canTakeWork = result.can_take_new_work as boolean | undefined;
  const leadsInPipeline = (result.leads_in_pipeline ?? 0) as number;
  const quotedProjects = (result.quoted_projects ?? 0) as number;

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-machine-dark" />
          <p className="text-[12px] font-semibold leading-tight">Capacity Overview</p>
        </div>
        {canTakeWork != null && (
          <Badge
            variant={canTakeWork ? 'default' : 'destructive'}
            className="text-[9px] uppercase shrink-0"
          >
            {canTakeWork ? 'Available' : 'At capacity'}
          </Badge>
        )}
      </div>

      <div className="mt-2.5 grid grid-cols-3 gap-3">
        <div className="flex items-center gap-1.5">
          <FolderKanban className="h-3 w-3 text-muted-foreground" />
          <div>
            <p className="font-mono text-[9px] text-muted-foreground">Active</p>
            <p className="text-[12px] font-semibold tabular-nums">{activeProjects}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <Users className="h-3 w-3 text-muted-foreground" />
          <div>
            <p className="font-mono text-[9px] text-muted-foreground">Workers</p>
            <p className="text-[12px] font-semibold tabular-nums">{totalWorkers}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <TrendingUp className="h-3 w-3 text-muted-foreground" />
          <div>
            <p className="font-mono text-[9px] text-muted-foreground">Utilisation</p>
            <p className="text-[12px] font-semibold tabular-nums">{utilisation}%</p>
          </div>
        </div>
      </div>

      <div className="mt-2">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className={`h-full rounded-full ${utilisation > 85 ? 'bg-fail' : utilisation > 60 ? 'bg-warn' : 'bg-pass'}`}
            style={{ width: `${Math.min(utilisation, 100)}%` }}
          />
        </div>
      </div>

      <div className="mt-2 flex gap-3 text-[10px] text-muted-foreground">
        <span>{unassigned} unassigned</span>
        <span>&bull;</span>
        <span>{leadsInPipeline} leads</span>
        <span>&bull;</span>
        <span>{quotedProjects} quoted</span>
      </div>
    </div>
  );
}
