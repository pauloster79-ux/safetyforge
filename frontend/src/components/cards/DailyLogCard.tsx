/**
 * DailyLogCard — rendered for get_daily_log_status / create_daily_log / auto_populate_daily_log.
 *
 * Shows missing log dates, recent log status dots, auto-populate summary.
 */

import { ClipboardList, CheckCircle, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface DailyLogCardProps {
  result: Record<string, unknown>;
}

export function DailyLogCard({ result }: DailyLogCardProps) {
  const missingDates = (result.missing_dates || result.missing || []) as string[];
  const missingCount = (result.missing_count ?? missingDates.length) as number;
  // Tool returns `recent_logs` (array of {log_date, status})
  const recentLogs = (result.recent_logs || result.recent_days || result.last_7_days || []) as Array<Record<string, unknown>>;
  const projectName = (result.project_name || result.name || '') as string;

  // Compute completion rate from missing_count if not provided
  const completionRate = result.completion_rate ?? result.rate ??
    (missingCount != null ? Math.round((7 - Math.min(missingCount, 7)) / 7 * 100) : null);

  // Auto-populate results have different shape
  const isAutoPopulate = result.time_entries != null || result.crew_count != null;

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <ClipboardList className="h-4 w-4 text-machine-dark" />
          <div>
            <p className="text-[12px] font-semibold leading-tight">
              {isAutoPopulate ? 'Daily Log Auto-Populated' : 'Daily Log Status'}
            </p>
            {projectName && <p className="text-[10px] text-muted-foreground">{projectName}</p>}
          </div>
        </div>
        {completionRate != null && !isAutoPopulate && (
          <Badge variant="secondary" className="text-[9px] font-mono shrink-0">
            {String(completionRate)}%
          </Badge>
        )}
      </div>

      {/* Auto-populate summary */}
      {isAutoPopulate && (
        <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-muted-foreground">
          {result.crew_count != null && <span>Crew: {String(result.crew_count)}</span>}
          {result.time_entries != null && <span>Time entries: {String(result.time_entries)}</span>}
          {result.inspections != null && <span>Inspections: {String(result.inspections)}</span>}
          {result.incidents != null && <span>Incidents: {String(result.incidents)}</span>}
        </div>
      )}

      {/* Missing dates */}
      {!isAutoPopulate && Array.isArray(missingDates) && missingDates.length > 0 && (
        <div className="mt-2">
          <p className="text-[10px] font-medium text-fail">
            Missing logs ({missingDates.length})
          </p>
          <div className="mt-1 flex flex-wrap gap-1">
            {missingDates.slice(0, 7).map((date, i) => (
              <span
                key={i}
                className="rounded-sm bg-fail-bg px-1.5 py-0.5 font-mono text-[9px] text-fail"
              >
                {date}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recent log status dots */}
      {!isAutoPopulate && Array.isArray(recentLogs) && recentLogs.length > 0 && (
        <div className="mt-2 flex gap-1">
          {recentLogs.slice(0, 7).map((day, i) => {
            const filled = day.filled || day.status === 'submitted' || day.status === 'approved' || day.status === 'complete';
            return (
              <div
                key={i}
                title={String(day.date || day.log_date || '')}
                className="flex h-6 w-6 items-center justify-center rounded-sm"
              >
                {filled ? (
                  <CheckCircle className="h-4 w-4 text-pass" />
                ) : (
                  <XCircle className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
