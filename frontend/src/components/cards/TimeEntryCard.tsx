/**
 * TimeEntryCard — rendered for record_time / time entry tool results.
 *
 * Shows worker name, clock in/out, hours, work item description.
 */

import { Clock, User } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface TimeEntryCardProps {
  result: Record<string, unknown>;
}

export function TimeEntryCard({ result }: TimeEntryCardProps) {
  const workerName = (result.worker_name || result.name || '') as string;
  const clockIn = (result.clock_in || '') as string;
  const clockOut = (result.clock_out || '') as string;
  const hours = result.hours ?? result.regular_hours;
  const date = (result.date || '') as string;
  const status = (result.status || 'open') as string;
  const workItemId = (result.work_item_id || '') as string;

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-machine-dark" />
          <div>
            <p className="text-[12px] font-semibold leading-tight">Time Entry</p>
            {date && <p className="font-mono text-[9px] text-muted-foreground">{date}</p>}
          </div>
        </div>
        <Badge variant="secondary" className="text-[9px] uppercase shrink-0">
          {status.replace(/_/g, ' ')}
        </Badge>
      </div>

      <div className="mt-2 space-y-1">
        {workerName && (
          <div className="flex items-center gap-1">
            <User className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground">{workerName}</span>
          </div>
        )}
        <div className="flex items-center gap-3">
          {clockIn && (
            <span className="font-mono text-[10px] text-muted-foreground">
              In: {clockIn}
            </span>
          )}
          {clockOut && (
            <span className="font-mono text-[10px] text-muted-foreground">
              Out: {clockOut}
            </span>
          )}
          {hours != null && (
            <span className="font-mono text-[12px] font-semibold">
              {String(hours)}h
            </span>
          )}
        </div>
        {workItemId && (
          <p className="font-mono text-[9px] text-muted-foreground truncate">
            Work item: {workItemId}
          </p>
        )}
      </div>
    </div>
  );
}
