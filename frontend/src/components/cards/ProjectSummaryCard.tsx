/**
 * ProjectSummaryCard — rendered for get_project_summary tool results.
 *
 * Shows project name, status, worker count, equipment count, 7-day activity.
 */

import { FolderKanban, Users, Wrench, Activity } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useShell } from '@/hooks/useShell';

interface ProjectSummaryCardProps {
  result: Record<string, unknown>;
}

export function ProjectSummaryCard({ result }: ProjectSummaryCardProps) {
  const shell = useShell();
  const name = (result.name || result.project_name || 'Project') as string;
  const status = (result.status || 'active') as string;
  const rawWorkers = result.worker_count ?? (Array.isArray(result.workers) ? result.workers.length : result.workers);
  const workerCount = rawWorkers != null ? rawWorkers : '—';
  const equipmentCount = result.equipment_count != null ? result.equipment_count : '—';
  const inspections7d = result.recent_inspections_7d ?? result.recent_inspections ?? null;
  const incidents7d = result.recent_incidents_7d ?? result.recent_incidents ?? null;
  const recentActivity = inspections7d != null
    ? `${inspections7d} insp / ${incidents7d ?? 0} inc`
    : (result.recent_activity ?? result.activity_7d ?? null) as string | null;
  const projectId = result.project_id ?? result.id;

  const statusColor = status === 'active' ? 'default' : status === 'completed' ? 'secondary' : 'destructive';

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <FolderKanban className="h-4 w-4 text-machine-dark" />
          <p className="text-[12px] font-semibold leading-tight">{name}</p>
        </div>
        <Badge variant={statusColor} className="text-[9px] uppercase shrink-0">
          {status}
        </Badge>
      </div>

      <div className="mt-2.5 grid grid-cols-3 gap-3">
        <div className="flex items-center gap-1.5">
          <Users className="h-3 w-3 text-muted-foreground" />
          <div>
            <p className="font-mono text-[9px] text-muted-foreground">Workers</p>
            <p className="text-[12px] font-semibold tabular-nums">{String(workerCount)}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <Wrench className="h-3 w-3 text-muted-foreground" />
          <div>
            <p className="font-mono text-[9px] text-muted-foreground">Equipment</p>
            <p className="text-[12px] font-semibold tabular-nums">{String(equipmentCount)}</p>
          </div>
        </div>
        {recentActivity && (
          <div className="flex items-center gap-1.5">
            <Activity className="h-3 w-3 text-muted-foreground" />
            <div>
              <p className="font-mono text-[9px] text-muted-foreground">7-day</p>
              <p className="text-[12px] font-semibold">{recentActivity}</p>
            </div>
          </div>
        )}
      </div>

      {!!projectId && (
        <Button
          variant="ghost"
          size="sm"
          className="mt-2 h-7 w-full text-[10px] text-muted-foreground hover:text-foreground"
          onClick={() =>
            shell.openCanvasFromCard('ProjectDetailPage', { projectId: String(projectId) }, name)
          }
        >
          Open in canvas
        </Button>
      )}
    </div>
  );
}
