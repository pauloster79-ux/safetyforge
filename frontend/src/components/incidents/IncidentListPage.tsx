import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, Loader2, AlertTriangle } from 'lucide-react';
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
import { useIncidents } from '@/hooks/useIncidents';
import { ROUTES } from '@/lib/constants';
import type { Incident } from '@/lib/constants';

const SEVERITY_BADGE_CLASSES: Record<string, string> = {
  fatality: 'bg-red-100 text-red-800',
  hospitalization: 'bg-red-100 text-red-800',
  medical_treatment: 'bg-orange-100 text-orange-800',
  first_aid: 'bg-orange-100 text-orange-800',
  near_miss: 'bg-blue-100 text-blue-800',
  property_damage: 'bg-yellow-100 text-yellow-800',
};

const SEVERITY_LABELS: Record<string, string> = {
  fatality: 'Fatality',
  hospitalization: 'Hospitalization',
  medical_treatment: 'Medical Treatment',
  first_aid: 'First Aid',
  near_miss: 'Near Miss',
  property_damage: 'Property Damage',
};

const STATUS_LABELS: Record<Incident['status'], string> = {
  reported: 'Reported',
  investigating: 'Investigating',
  corrective_actions: 'Corrective Actions',
  closed: 'Closed',
};

function ProjectIncidents({
  projectId,
  projectName,
  search,
  severityFilter,
  statusFilter,
}: {
  projectId: string;
  projectName: string;
  search: string;
  severityFilter: string;
  statusFilter: string;
}) {
  const { data: incidents, isLoading } = useIncidents(projectId);
  const navigate = useNavigate();

  const filtered = useMemo(() => {
    if (!incidents) return [];
    let result = [...incidents];

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (i) =>
          i.location.toLowerCase().includes(q) ||
          i.description.toLowerCase().includes(q) ||
          projectName.toLowerCase().includes(q),
      );
    }

    if (severityFilter) {
      result = result.filter((i) => i.severity === severityFilter);
    }

    if (statusFilter) {
      result = result.filter((i) => i.status === statusFilter);
    }

    return result;
  }, [incidents, search, severityFilter, statusFilter, projectName]);

  if (isLoading || filtered.length === 0) return null;

  return (
    <>
      {filtered.map((incident) => (
        <tr
          key={incident.id}
          className="cursor-pointer border-b border-border last:border-0 hover:bg-muted/50"
          onClick={() =>
            navigate(ROUTES.INCIDENT_DETAIL(projectId, incident.id))
          }
        >
          <td className="px-4 py-3 text-sm text-foreground">
            {new Date(incident.incident_date).toLocaleDateString()}
          </td>
          <td className="hidden px-4 py-3 text-sm text-foreground md:table-cell">
            {incident.location}
          </td>
          <td className="px-4 py-3 text-sm">
            <Badge
              variant="secondary"
              className={
                SEVERITY_BADGE_CLASSES[incident.severity] ||
                'bg-gray-100 text-gray-800'
              }
            >
              {SEVERITY_LABELS[incident.severity] || incident.severity}
            </Badge>
          </td>
          <td className="hidden px-4 py-3 text-sm text-foreground lg:table-cell">
            {STATUS_LABELS[incident.status] || incident.status}
          </td>
          <td className="px-4 py-3 text-sm text-muted-foreground">
            {projectName}
          </td>
        </tr>
      ))}
    </>
  );
}

export function IncidentListPage() {
  const navigate = useNavigate();
  const { data: projects, isLoading: projectsLoading } = useProjects();

  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [projectPickerOpen, setProjectPickerOpen] = useState(false);

  const handleSeverityFilter = (value: string) => {
    setSeverityFilter(value.startsWith('All') ? '' : value);
  };

  const handleStatusFilter = (value: string) => {
    setStatusFilter(value.startsWith('All') ? '' : value);
  };

  const handleNewIncident = (projectId: string) => {
    setProjectPickerOpen(false);
    navigate(ROUTES.INCIDENT_NEW(projectId));
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Incidents</h1>
          <p className="text-sm text-muted-foreground">
            View incidents across all projects
          </p>
        </div>
        <div className="relative">
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => setProjectPickerOpen(!projectPickerOpen)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Report Incident
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
                  onClick={() => handleNewIncident(project.id)}
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
            placeholder="Search incidents..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex gap-2">
          <Select
            value={severityFilter || 'All'}
            onValueChange={handleSeverityFilter}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All Severity">All Severity</SelectItem>
              <SelectItem value="fatality">Fatality</SelectItem>
              <SelectItem value="hospitalization">Hospitalization</SelectItem>
              <SelectItem value="medical_treatment">
                Medical Treatment
              </SelectItem>
              <SelectItem value="first_aid">First Aid</SelectItem>
              <SelectItem value="near_miss">Near Miss</SelectItem>
              <SelectItem value="property_damage">Property Damage</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={statusFilter || 'All'}
            onValueChange={handleStatusFilter}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All Status">All Status</SelectItem>
              <SelectItem value="reported">Reported</SelectItem>
              <SelectItem value="investigating">Investigating</SelectItem>
              <SelectItem value="corrective_actions">
                Corrective Actions
              </SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
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
                  Location
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Severity
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground lg:table-cell">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Project
                </th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <ProjectIncidents
                  key={project.id}
                  projectId={project.id}
                  projectName={project.name}
                  search={search}
                  severityFilter={severityFilter}
                  statusFilter={statusFilter}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <AlertTriangle className="h-16 w-16 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium text-muted-foreground">
            No incidents found
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || severityFilter || statusFilter
              ? 'Try adjusting your filters or search query'
              : 'No incidents have been reported yet'}
          </p>
        </div>
      )}
    </div>
  );
}
