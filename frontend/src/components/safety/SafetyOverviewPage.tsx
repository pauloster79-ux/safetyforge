import { useQuery } from '@tanstack/react-query';
import {
  ShieldCheck,
  AlertTriangle,
  Siren,
  ClipboardCheck,
  FileText,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useProjects } from '@/hooks/useProjects';
import { useShell } from '@/hooks/useShell';
import { api } from '@/lib/api';
import type { HazardReport, Incident, Inspection, Project } from '@/lib/constants';
import { format } from 'date-fns';

// ---------------------------------------------------------------------------
// Aggregated hooks — fetch safety data across all active projects
// ---------------------------------------------------------------------------

type ProjectHazards = { project: Project; hazards: HazardReport[] };
type ProjectIncidents = { project: Project; incidents: Incident[] };
type ProjectInspections = { project: Project; inspections: Inspection[] };

function useCrossProjectSafety(projects: Project[] | undefined) {
  const active = (projects ?? []).filter(
    (p) => p.state === 'active' || p.state === 'quoted',
  );
  return useQuery({
    queryKey: ['safety-overview', active.map((p) => p.id)],
    enabled: active.length > 0,
    staleTime: 30_000,
    queryFn: async () => {
      const hazards: ProjectHazards[] = [];
      const incidents: ProjectIncidents[] = [];
      const inspections: ProjectInspections[] = [];

      // Fetch all projects in parallel
      await Promise.all(
        active.map(async (project) => {
          const [hz, inc, ins] = await Promise.all([
            api
              .get<{ reports: HazardReport[]; total: number }>(
                `/me/projects/${project.id}/hazard-reports`,
              )
              .catch(() => ({ reports: [], total: 0 })),
            api
              .get<{ incidents: Incident[]; total: number }>(
                `/me/projects/${project.id}/incidents`,
              )
              .catch(() => ({ incidents: [], total: 0 })),
            api
              .get<{ inspections: Inspection[]; total: number }>(
                `/me/projects/${project.id}/inspections`,
              )
              .catch(() => ({ inspections: [], total: 0 })),
          ]);
          if (hz.reports.length) hazards.push({ project, hazards: hz.reports });
          if (inc.incidents.length) incidents.push({ project, incidents: inc.incidents });
          if (ins.inspections.length) inspections.push({ project, inspections: ins.inspections });
        }),
      );

      // Sort hazards by severity (open first, then imminent_danger → high → medium → low)
      const severityOrder: Record<string, number> = {
        imminent_danger: 0,
        high: 1,
        medium: 2,
        low: 3,
      };
      const openHazards = hazards
        .flatMap((h) =>
          h.hazards.map((hr) => ({ project: h.project, hazard: hr })),
        )
        .filter((x) => x.hazard.status === 'open' || x.hazard.status === 'in_progress')
        .sort(
          (a, b) =>
            (severityOrder[a.hazard.highest_severity] ?? 9) -
            (severityOrder[b.hazard.highest_severity] ?? 9),
        );

      const openIncidents = incidents
        .flatMap((i) =>
          i.incidents.map((inc) => ({ project: i.project, incident: inc })),
        )
        .filter((x) => x.incident.status !== 'closed')
        .sort((a, b) => (a.incident.incident_date < b.incident.incident_date ? 1 : -1));

      const recentInspections = inspections
        .flatMap((i) =>
          i.inspections.map((ins) => ({ project: i.project, inspection: ins })),
        )
        .sort((a, b) =>
          a.inspection.inspection_date < b.inspection.inspection_date ? 1 : -1,
        );

      const failedInspections = recentInspections.filter(
        (x) => x.inspection.overall_status === 'fail',
      );

      return {
        openHazards,
        openIncidents,
        recentInspections,
        failedInspections,
        projectCount: active.length,
      };
    },
  });
}

// ---------------------------------------------------------------------------
// Small helper components
// ---------------------------------------------------------------------------

function KpiCard({
  label,
  value,
  accent,
  icon,
}: {
  label: string;
  value: number;
  accent: 'pass' | 'warn' | 'fail' | 'info' | 'muted';
  icon: React.ReactNode;
}) {
  const accentBg: Record<string, string> = {
    pass: 'bg-[var(--pass-bg)]',
    warn: 'bg-[var(--warn-bg)]',
    fail: 'bg-[var(--fail-bg)]',
    info: 'bg-[var(--info-bg)]',
    muted: 'bg-muted',
  };
  const accentText: Record<string, string> = {
    pass: 'text-[var(--pass)]',
    warn: 'text-[var(--warn)]',
    fail: 'text-[var(--fail)]',
    info: 'text-[var(--info)]',
    muted: 'text-muted-foreground',
  };
  return (
    <Card>
      <CardContent className="flex items-center gap-3 pt-6">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${accentBg[accent]}`}>
          <span className={accentText[accent]}>{icon}</span>
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-xs text-muted-foreground">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// SafetyOverviewPage
// ---------------------------------------------------------------------------

export function SafetyOverviewPage() {
  const shell = useShell();
  const { data: projects, isLoading: loadingProjects } = useProjects();
  const { data, isLoading: loadingSafety } = useCrossProjectSafety(projects);

  const isLoading = loadingProjects || loadingSafety;

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const openHazards = data?.openHazards ?? [];
  const openIncidents = data?.openIncidents ?? [];
  const failedInspections = data?.failedInspections ?? [];
  const recentInspections = data?.recentInspections ?? [];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-[var(--machine-dark)]" />
          <h1 className="text-2xl font-bold">Safety Overview</h1>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Cross-project safety status across {data?.projectCount ?? 0} active project{data?.projectCount === 1 ? '' : 's'}
        </p>
      </div>

      {/* KPIs */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Open hazards"
          value={openHazards.length}
          accent={openHazards.length > 0 ? 'fail' : 'muted'}
          icon={<AlertTriangle className="h-5 w-5" />}
        />
        <KpiCard
          label="Open incidents"
          value={openIncidents.length}
          accent={openIncidents.length > 0 ? 'warn' : 'muted'}
          icon={<Siren className="h-5 w-5" />}
        />
        <KpiCard
          label="Failed inspections"
          value={failedInspections.length}
          accent={failedInspections.length > 0 ? 'fail' : 'muted'}
          icon={<ClipboardCheck className="h-5 w-5" />}
        />
        <KpiCard
          label="Total inspections"
          value={recentInspections.length}
          accent="info"
          icon={<FileText className="h-5 w-5" />}
        />
      </div>

      {/* Open hazards */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Open Hazards</CardTitle>
          {openHazards.length > 0 && (
            <Badge variant="secondary">{openHazards.length}</Badge>
          )}
        </CardHeader>
        <CardContent>
          {openHazards.length === 0 ? (
            <p className="text-sm text-muted-foreground">No open hazards across all projects.</p>
          ) : (
            <div className="space-y-2">
              {openHazards.slice(0, 8).map(({ project, hazard }) => (
                <button
                  key={hazard.id}
                  className="flex w-full items-center gap-3 rounded-lg border border-muted p-3 text-left transition-colors hover:bg-muted/50"
                  onClick={() =>
                    shell.openCanvas({
                      component: 'HazardReportPage',
                      props: { projectId: project.id, id: hazard.id },
                      label: 'Hazard Report',
                    })
                  }
                >
                  <div
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                      hazard.highest_severity === 'imminent_danger' || hazard.highest_severity === 'high'
                        ? 'bg-[var(--fail-bg)]'
                        : hazard.highest_severity === 'medium'
                          ? 'bg-[var(--warn-bg)]'
                          : 'bg-[var(--info-bg)]'
                    }`}
                  >
                    <AlertTriangle
                      className={`h-5 w-5 ${
                        hazard.highest_severity === 'imminent_danger' || hazard.highest_severity === 'high'
                          ? 'text-[var(--fail)]'
                          : hazard.highest_severity === 'medium'
                            ? 'text-[var(--warn)]'
                            : 'text-[var(--info)]'
                      }`}
                    />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{hazard.description || hazard.location}</p>
                    <p className="text-xs text-muted-foreground">
                      {project.name} · {hazard.hazard_count} hazard{hazard.hazard_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <Badge
                    className={
                      hazard.status === 'open'
                        ? 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]'
                        : 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]'
                    }
                  >
                    {hazard.status === 'in_progress' ? 'In Progress' : 'Open'}
                  </Badge>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Open incidents */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Open Incidents</CardTitle>
          {openIncidents.length > 0 && (
            <Badge variant="secondary">{openIncidents.length}</Badge>
          )}
        </CardHeader>
        <CardContent>
          {openIncidents.length === 0 ? (
            <p className="text-sm text-muted-foreground">No open incidents across all projects.</p>
          ) : (
            <div className="space-y-2">
              {openIncidents.slice(0, 8).map(({ project, incident }) => (
                <button
                  key={incident.id}
                  className="flex w-full items-center gap-3 rounded-lg border border-muted p-3 text-left transition-colors hover:bg-muted/50"
                  onClick={() =>
                    shell.openCanvas({
                      component: 'IncidentDetailPage',
                      props: { projectId: project.id, incidentId: incident.id },
                      label: 'Incident',
                    })
                  }
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--warn-bg)]">
                    <Siren className="h-5 w-5 text-[var(--warn)]" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{incident.description}</p>
                    <p className="text-xs text-muted-foreground">
                      {project.name} · {format(new Date(incident.incident_date), 'MMM d, yyyy')}
                    </p>
                  </div>
                  <Badge className="bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)] capitalize">
                    {incident.status.replace('_', ' ')}
                  </Badge>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick links to safety pages */}
      <div className="grid gap-3 sm:grid-cols-3">
        <Button
          variant="outline"
          className="h-auto justify-start gap-3 px-4 py-3"
          onClick={() =>
            shell.openCanvas({ component: 'InspectionListPage', props: {}, label: 'All Inspections' })
          }
        >
          <ClipboardCheck className="h-5 w-5 text-[var(--machine-dark)]" />
          <div className="text-left">
            <p className="text-sm font-medium">All Inspections</p>
            <p className="text-xs text-muted-foreground">View & create inspections</p>
          </div>
        </Button>
        <Button
          variant="outline"
          className="h-auto justify-start gap-3 px-4 py-3"
          onClick={() =>
            shell.openCanvas({ component: 'IncidentListPage', props: {}, label: 'All Incidents' })
          }
        >
          <Siren className="h-5 w-5 text-[var(--machine-dark)]" />
          <div className="text-left">
            <p className="text-sm font-medium">All Incidents</p>
            <p className="text-xs text-muted-foreground">OSHA log & reporting</p>
          </div>
        </Button>
        <Button
          variant="outline"
          className="h-auto justify-start gap-3 px-4 py-3"
          onClick={() =>
            shell.openCanvas({ component: 'GcPortalPage', props: {}, label: 'Compliance' })
          }
        >
          <ShieldCheck className="h-5 w-5 text-[var(--machine-dark)]" />
          <div className="text-left">
            <p className="text-sm font-medium">Compliance</p>
            <p className="text-xs text-muted-foreground">GC portal & certifications</p>
          </div>
        </Button>
      </div>
    </div>
  );
}
