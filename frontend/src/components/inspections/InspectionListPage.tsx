import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import { Search, Plus, Loader2, ClipboardCheck } from 'lucide-react';
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
import { useInspections } from '@/hooks/useInspections';
import { ROUTES, INSPECTION_TYPES } from '@/lib/constants';
import type { Inspection } from '@/lib/constants';

const STATUS_BADGE_CLASSES: Record<Inspection['overall_status'], string> = {
  pass: 'bg-green-100 text-green-800',
  fail: 'bg-red-100 text-red-800',
  partial: 'bg-yellow-100 text-yellow-800',
};

function ProjectInspections({
  projectId,
  projectName,
  search,
  typeFilter,
  statusFilter,
}: {
  projectId: string;
  projectName: string;
  search: string;
  typeFilter: string;
  statusFilter: string;
}) {
  const { data: inspections, isLoading } = useInspections(projectId);
  const navigate = useCanvasNavigate();

  const filtered = useMemo(() => {
    if (!inspections) return [];
    let result = [...inspections];

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (i) =>
          i.inspector_name.toLowerCase().includes(q) ||
          i.inspection_type.toLowerCase().includes(q) ||
          projectName.toLowerCase().includes(q),
      );
    }

    if (typeFilter) {
      result = result.filter((i) => i.inspection_type === typeFilter);
    }

    if (statusFilter) {
      result = result.filter((i) => i.overall_status === statusFilter);
    }

    return result;
  }, [inspections, search, typeFilter, statusFilter, projectName]);

  if (isLoading || filtered.length === 0) return null;

  return (
    <>
      {filtered.map((inspection) => {
        const typeName =
          INSPECTION_TYPES.find((t) => t.id === inspection.inspection_type)
            ?.name || inspection.inspection_type;

        return (
          <tr
            key={inspection.id}
            className="cursor-pointer border-b border-border last:border-0 hover:bg-muted/50"
            onClick={() =>
              navigate(ROUTES.INSPECTION_DETAIL(projectId, inspection.id))
            }
          >
            <td className="px-4 py-3 text-sm text-foreground">
              {new Date(inspection.inspection_date).toLocaleDateString()}
            </td>
            <td className="hidden px-4 py-3 text-sm text-foreground md:table-cell">
              {inspection.inspector_name}
            </td>
            <td className="hidden px-4 py-3 text-sm text-foreground lg:table-cell">
              {typeName}
            </td>
            <td className="px-4 py-3 text-sm">
              <Badge
                variant="secondary"
                className={STATUS_BADGE_CLASSES[inspection.overall_status]}
              >
                {inspection.overall_status}
              </Badge>
            </td>
            <td className="px-4 py-3 text-sm text-muted-foreground">
              {projectName}
            </td>
          </tr>
        );
      })}
    </>
  );
}

export function InspectionListPage() {
  const navigate = useCanvasNavigate();
  const { data: projects, isLoading: projectsLoading } = useProjects();

  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [projectPickerOpen, setProjectPickerOpen] = useState(false);

  const handleTypeFilter = (value: string | null) => {
    if (value === null) return;
    setTypeFilter(value.startsWith('All') ? '' : value);
  };

  const handleStatusFilter = (value: string | null) => {
    if (value === null) return;
    setStatusFilter(value.startsWith('All') ? '' : value);
  };

  const handleNewInspection = (projectId: string) => {
    setProjectPickerOpen(false);
    navigate(ROUTES.INSPECTION_NEW(projectId));
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Inspections</h1>
          <p className="text-sm text-muted-foreground">
            View inspections across all projects
          </p>
        </div>
        <div className="relative">
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => setProjectPickerOpen(!projectPickerOpen)}
          >
            <Plus className="mr-2 h-4 w-4" />
            New Inspection
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
                  onClick={() => handleNewInspection(project.id)}
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
            placeholder="Search inspections..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex gap-2">
          <Select value={typeFilter || 'All'} onValueChange={handleTypeFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All Types">All Types</SelectItem>
              {INSPECTION_TYPES.map((type) => (
                <SelectItem key={type.id} value={type.id}>
                  {type.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={statusFilter || 'All'}
            onValueChange={handleStatusFilter}
          >
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All Status">All Status</SelectItem>
              <SelectItem value="pass">Pass</SelectItem>
              <SelectItem value="fail">Fail</SelectItem>
              <SelectItem value="partial">Partial</SelectItem>
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
                  Date
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground md:table-cell">
                  Inspector
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground lg:table-cell">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Project
                </th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <ProjectInspections
                  key={project.id}
                  projectId={project.id}
                  projectName={project.name}
                  search={search}
                  typeFilter={typeFilter}
                  statusFilter={statusFilter}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <ClipboardCheck className="h-16 w-16 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium text-muted-foreground">
            No inspections found
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || typeFilter || statusFilter
              ? 'Try adjusting your filters or search query'
              : 'Create your first inspection to get started'}
          </p>
        </div>
      )}
    </div>
  );
}
