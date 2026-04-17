import { useState, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import { Plus, Loader2, Calendar, Search, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useProject } from '@/hooks/useProjects';
import { useShell } from '@/hooks/useShell';
import { useDailyLogs } from '@/hooks/useDailyLogs';
import { ROUTES, DAILY_LOG_STATUSES } from '@/lib/constants';
import type { DailyLog } from '@/lib/constants';

const STATUS_BADGE_CLASSES: Record<DailyLog['status'], string> = {
  draft: 'bg-yellow-100 text-yellow-800',
  submitted: 'bg-blue-100 text-blue-800',
  approved: 'bg-green-100 text-green-800',
};

export function DailyLogListPage({ projectId: propProjectId }: { projectId?: string } = {}) {
  const navigate = useCanvasNavigate();
  const shell = useShell();
  const params = useParams<{ projectId: string }>();
  const projectId = propProjectId || params.projectId;
  const { data: project } = useProject(projectId);
  const { data: dailyLogs, isLoading } = useDailyLogs(projectId);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const handleStatusFilter = (value: string | null) => {
    setStatusFilter(!value || value.startsWith('All') ? '' : value);
  };

  const filtered = useMemo(() => {
    if (!dailyLogs) return [];
    let result = [...dailyLogs];

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (d) =>
          d.superintendent_name.toLowerCase().includes(q) ||
          d.work_performed.toLowerCase().includes(q) ||
          d.log_date.includes(q),
      );
    }

    if (statusFilter) {
      result = result.filter((d) => d.status === statusFilter);
    }

    // Sort by date descending
    result.sort((a, b) => b.log_date.localeCompare(a.log_date));

    return result;
  }, [dailyLogs, search, statusFilter]);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Daily Logs</h1>
          <p className="text-sm text-muted-foreground">
            {project ? project.name : 'Project daily logs'}
          </p>
        </div>
        <Button
          className="bg-primary hover:bg-[var(--machine-dark)]"
          onClick={() =>
            projectId &&
            shell.openCanvas({
              component: 'DailyLogForm',
              props: { projectId },
              label: 'New Daily Log',
            })
          }
        >
          <Plus className="mr-2 h-4 w-4" />
          New Daily Log
        </Button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search daily logs..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <Select
          value={statusFilter || 'All'}
          onValueChange={handleStatusFilter}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="All Status">All Status</SelectItem>
            {DAILY_LOG_STATUSES.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : filtered.length > 0 ? (
        <div className="overflow-hidden rounded-lg border border-border bg-card">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted">
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Date
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground md:table-cell">
                  Superintendent
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground lg:table-cell">
                  Workers
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground lg:table-cell">
                  Weather
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((log) => (
                <tr
                  key={log.id}
                  className="cursor-pointer border-b border-border last:border-0 hover:bg-muted/50"
                  onClick={() =>
                    projectId &&
                    shell.openCanvas({
                      component: 'DailyLogDetailPage',
                      props: { projectId, dailyLogId: log.id },
                      label: 'Daily Log',
                    })
                  }
                >
                  <td className="px-4 py-3 text-sm text-foreground">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                      {new Date(log.log_date + 'T00:00:00').toLocaleDateString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </div>
                  </td>
                  <td className="hidden px-4 py-3 text-sm text-foreground md:table-cell">
                    {log.superintendent_name}
                  </td>
                  <td className="hidden px-4 py-3 text-sm text-foreground lg:table-cell">
                    {log.workers_on_site}
                  </td>
                  <td className="hidden px-4 py-3 text-sm text-foreground lg:table-cell">
                    {log.weather.conditions}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Badge
                      variant="secondary"
                      className={STATUS_BADGE_CLASSES[log.status]}
                    >
                      {log.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <FileText className="h-16 w-16 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium text-muted-foreground">
            No daily logs found
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || statusFilter
              ? 'Try adjusting your filters or search query'
              : 'Create your first daily log to get started'}
          </p>
        </div>
      )}
    </div>
  );
}
