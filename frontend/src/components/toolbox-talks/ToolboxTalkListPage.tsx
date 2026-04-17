import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import { Search, Plus, Loader2, MessageSquare } from 'lucide-react';
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
import { useProjects } from '@/hooks/useProjects';
import { useToolboxTalks } from '@/hooks/useToolboxTalks';
import { ROUTES } from '@/lib/constants';
import type { ToolboxTalk } from '@/lib/constants';

const STATUS_BADGE_CLASSES: Record<ToolboxTalk['status'], string> = {
  completed: 'bg-green-100 text-green-800',
  in_progress: 'bg-blue-100 text-blue-800',
  scheduled: 'bg-gray-100 text-gray-800',
};

const STATUS_LABELS: Record<ToolboxTalk['status'], string> = {
  completed: 'Completed',
  in_progress: 'In Progress',
  scheduled: 'Scheduled',
};

function ProjectToolboxTalks({
  projectId,
  projectName,
  search,
  statusFilter,
}: {
  projectId: string;
  projectName: string;
  search: string;
  statusFilter: string;
}) {
  const { data: talks, isLoading } = useToolboxTalks(projectId);
  const navigate = useCanvasNavigate();

  const filtered = useMemo(() => {
    if (!talks) return [];
    let result = [...talks];

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (t) =>
          t.topic.toLowerCase().includes(q) ||
          t.presented_by.toLowerCase().includes(q) ||
          projectName.toLowerCase().includes(q),
      );
    }

    if (statusFilter) {
      result = result.filter((t) => t.status === statusFilter);
    }

    return result;
  }, [talks, search, statusFilter, projectName]);

  if (isLoading || filtered.length === 0) return null;

  return (
    <>
      {filtered.map((talk) => (
        <tr
          key={talk.id}
          className="cursor-pointer border-b border-border last:border-0 hover:bg-muted/50"
          onClick={() =>
            navigate(ROUTES.TOOLBOX_TALK_DETAIL(projectId, talk.id))
          }
        >
          <td className="px-4 py-3 text-sm text-foreground">{talk.topic}</td>
          <td className="hidden px-4 py-3 text-sm text-foreground md:table-cell">
            {new Date(talk.scheduled_date).toLocaleDateString()}
          </td>
          <td className="hidden px-4 py-3 text-sm text-foreground lg:table-cell">
            {talk.duration_minutes} min
          </td>
          <td className="px-4 py-3 text-sm">
            <Badge
              variant="secondary"
              className={STATUS_BADGE_CLASSES[talk.status]}
            >
              {STATUS_LABELS[talk.status]}
            </Badge>
          </td>
          <td className="hidden px-4 py-3 text-sm text-foreground md:table-cell">
            {talk.attendees?.length || 0}
          </td>
          <td className="px-4 py-3 text-sm text-muted-foreground">
            {projectName}
          </td>
        </tr>
      ))}
    </>
  );
}

export function ToolboxTalkListPage() {
  const navigate = useCanvasNavigate();
  const { data: projects, isLoading: projectsLoading } = useProjects();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [projectPickerOpen, setProjectPickerOpen] = useState(false);

  const handleStatusFilter = (value: string | null) => {
    if (value === null) return;
    setStatusFilter(value.startsWith('All') ? '' : value);
  };

  const handleNewTalk = (projectId: string) => {
    setProjectPickerOpen(false);
    navigate(ROUTES.TOOLBOX_TALK_NEW(projectId));
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Toolbox Talks</h1>
          <p className="text-sm text-muted-foreground">
            View toolbox talks across all projects
          </p>
        </div>
        <div className="relative">
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => setProjectPickerOpen(!projectPickerOpen)}
          >
            <Plus className="mr-2 h-4 w-4" />
            New Talk
          </Button>
          {projectPickerOpen && projects && projects.length > 0 && (
            <div className="absolute right-0 top-full z-10 mt-1 w-64 rounded-lg border border-border bg-card p-2 shadow-lg">
              <p className="mb-2 px-2 text-xs font-medium text-muted-foreground">
                Select a project
              </p>
              {projects.map((project) => (
                <button
                  key={project.id}
                  className="w-full rounded-md px-2 py-1.5 text-left text-sm text-foreground hover:bg-muted"
                  onClick={() => handleNewTalk(project.id)}
                >
                  {project.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search toolbox talks..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex gap-2">
          <Select
            value={statusFilter || 'All'}
            onValueChange={handleStatusFilter}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All Status">All Status</SelectItem>
              <SelectItem value="scheduled">Scheduled</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {projectsLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : projects && projects.length > 0 ? (
        <div className="overflow-hidden rounded-lg border border-border bg-card">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted">
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Topic
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground md:table-cell">
                  Date
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground lg:table-cell">
                  Duration
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Status
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground md:table-cell">
                  Attendees
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Project
                </th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <ProjectToolboxTalks
                  key={project.id}
                  projectId={project.id}
                  projectName={project.name}
                  search={search}
                  statusFilter={statusFilter}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <MessageSquare className="h-16 w-16 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium text-muted-foreground">
            No toolbox talks found
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || statusFilter
              ? 'Try adjusting your filters or search query'
              : 'Create your first toolbox talk to get started'}
          </p>
        </div>
      )}
    </div>
  );
}
