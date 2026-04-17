/**
 * ScheduleCard — rendered for get_schedule tool results.
 *
 * Shows a weekly schedule view with work items and assigned workers.
 */

import { Calendar, User, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ScheduleCardProps {
  result: Record<string, unknown>;
}

export function ScheduleCard({ result }: ScheduleCardProps) {
  const projectName = (result.project_name || 'Schedule') as string;
  const totalItems = (result.total_items ?? 0) as number;
  const scheduledItems = (result.scheduled_items ?? 0) as number;
  const weeks = (result.weeks || {}) as Record<string, Array<Record<string, unknown>>>;
  const unscheduled = (result.unscheduled || []) as Array<Record<string, unknown>>;

  const weekKeys = Object.keys(weeks).sort();

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-machine-dark" />
          <div>
            <p className="text-[12px] font-semibold leading-tight">{projectName}</p>
            <p className="text-[10px] text-muted-foreground">
              {scheduledItems}/{totalItems} scheduled
            </p>
          </div>
        </div>
      </div>

      {weekKeys.slice(0, 4).map((weekKey) => {
        const items = weeks[weekKey] as Array<Record<string, unknown>>;
        return (
          <div key={weekKey} className="mt-2">
            <p className="text-[10px] font-medium text-muted-foreground">{weekKey}</p>
            <div className="mt-0.5 space-y-1">
              {items.slice(0, 5).map((item, i) => (
                <div key={i} className="flex items-center justify-between rounded bg-muted/50 px-2 py-1">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[10px] font-medium">
                      {item.description as string}
                    </p>
                    {!!item.assigned_worker && (
                      <p className="flex items-center gap-1 text-[9px] text-muted-foreground">
                        <User className="h-2.5 w-2.5" />
                        {String(item.assigned_worker)}
                      </p>
                    )}
                  </div>
                  <Badge
                    variant={item.state === 'in_progress' ? 'default' : 'outline'}
                    className="ml-2 text-[8px] shrink-0"
                  >
                    {String(item.state || 'draft').replace(/_/g, ' ')}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {unscheduled.length > 0 && (
        <div className="mt-2">
          <p className="flex items-center gap-1 text-[10px] font-medium text-warn">
            <Clock className="h-3 w-3" />
            {unscheduled.length} unscheduled
          </p>
        </div>
      )}
    </div>
  );
}
