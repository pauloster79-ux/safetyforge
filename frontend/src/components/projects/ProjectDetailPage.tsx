import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  ClipboardCheck,
  FileText,
  MapPin,
  Users,
  Phone,
  Hospital,
  AlertTriangle,
  Loader2,
  Plus,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Calendar,
  Save,
  MessageSquare,
  Shield,
  Camera,
  Sun,
  Siren,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useProject, useUpdateProject } from '@/hooks/useProjects';
import { useInspections } from '@/hooks/useInspections';
import { useToolboxTalks } from '@/hooks/useToolboxTalks';
import { useDocuments } from '@/hooks/useDocuments';
import { useHazardReports } from '@/hooks/useHazardReports';
import { useIncidents } from '@/hooks/useIncidents';
import { useMorningBrief } from '@/hooks/useMorningBrief';
import { ROUTES, PROJECT_TYPES, INSPECTION_TYPES } from '@/lib/constants';
import type { Project, Inspection, Incident } from '@/lib/constants';
import { ComplianceRing } from './ComplianceRing';
import { format } from 'date-fns';

function StatusBadge({ status }: { status: Project['status'] }) {
  const config = {
    active: { label: 'Active', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    on_hold: { label: 'On Hold', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
    completed: { label: 'Completed', className: 'bg-muted text-muted-foreground hover:bg-muted' },
  };
  const { label, className } = config[status];
  return <Badge className={className}>{label}</Badge>;
}

function InspectionStatusIcon({ status }: { status: Inspection['overall_status'] }) {
  switch (status) {
    case 'pass':
      return <CheckCircle2 className="h-5 w-5 text-[var(--pass)]" />;
    case 'fail':
      return <XCircle className="h-5 w-5 text-[var(--fail)]" />;
    case 'partial':
      return <AlertCircle className="h-5 w-5 text-[var(--warn)]" />;
  }
}

function InspectionStatusBadge({ status }: { status: Inspection['overall_status'] }) {
  const config = {
    pass: { label: 'Pass', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    fail: { label: 'Fail', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
    partial: { label: 'Partial', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
  };
  const { label, className } = config[status];
  return <Badge className={className}>{label}</Badge>;
}

export function ProjectDetailPage() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const { data: project, isLoading } = useProject(projectId);
  const { data: inspections } = useInspections(projectId);
  const { data: toolboxTalks } = useToolboxTalks(projectId);
  const { data: documents } = useDocuments();
  const { data: hazardReports } = useHazardReports(projectId);
  const { data: incidents } = useIncidents(projectId);
  const { data: morningBrief } = useMorningBrief(projectId);
  const updateProject = useUpdateProject();

  const [editForm, setEditForm] = useState<Partial<Project> | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <p className="text-sm text-muted-foreground">Project not found</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate(ROUTES.PROJECTS)}>
          Back to Projects
        </Button>
      </div>
    );
  }

  const inspectionTypeName = (typeId: string) =>
    INSPECTION_TYPES.find((t) => t.id === typeId)?.name || typeId;

  const handleEditChange = (field: string, value: unknown) => {
    setEditForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSaveSettings = async () => {
    if (!editForm || !projectId) return;
    await updateProject.mutateAsync({ id: projectId, ...editForm });
    setEditForm(null);
  };

  const passCount = inspections?.filter((i) => i.overall_status === 'pass').length ?? 0;
  const failCount = inspections?.filter((i) => i.overall_status === 'fail').length ?? 0;
  const partialCount = inspections?.filter((i) => i.overall_status === 'partial').length ?? 0;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="mt-1"
            onClick={() => navigate(ROUTES.PROJECTS)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">{project.name}</h1>
              <StatusBadge status={project.status} />
            </div>
            <div className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
              <MapPin className="h-3.5 w-3.5" />
              {project.address}
            </div>
            {project.client_name && (
              <p className="mt-0.5 text-sm text-muted-foreground">{project.client_name}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ComplianceRing score={project.compliance_score} size="lg" />
          <div className="flex flex-col gap-2">
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={() => navigate(ROUTES.INSPECTION_NEW(project.id))}
            >
              <ClipboardCheck className="mr-2 h-4 w-4" />
              New Inspection
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(ROUTES.TOOLBOX_TALK_NEW(project.id))}
            >
              <MessageSquare className="mr-2 h-4 w-4" />
              New Toolbox Talk
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(ROUTES.HAZARD_REPORT_NEW(project.id))}
            >
              <Camera className="mr-2 h-4 w-4" />
              Photo Assessment
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(ROUTES.INCIDENT_NEW(project.id))}
            >
              <Siren className="mr-2 h-4 w-4" />
              Report Incident
            </Button>
            <Button
              variant="outline"
              className="border-primary text-[var(--machine-dark)] hover:bg-[var(--machine-wash)]"
              onClick={() => navigate(`${ROUTES.MOCK_INSPECTION}?project=${project.id}`)}
            >
              <Shield className="mr-2 h-4 w-4" />
              Mock Inspection
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="inspections">
            Inspections {inspections ? `(${inspections.length})` : ''}
          </TabsTrigger>
          <TabsTrigger value="toolbox-talks">
            Toolbox Talks {toolboxTalks ? `(${toolboxTalks.length})` : ''}
          </TabsTrigger>
          <TabsTrigger value="hazards">
            Hazards {hazardReports ? `(${hazardReports.length})` : ''}
          </TabsTrigger>
          <TabsTrigger value="incidents">
            Incidents {incidents ? `(${incidents.length})` : ''}
          </TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--pass-bg)]">
                    <CheckCircle2 className="h-5 w-5 text-[var(--pass)]" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{passCount}</p>
                    <p className="text-xs text-muted-foreground">Passed</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--warn-bg)]">
                    <AlertCircle className="h-5 w-5 text-[var(--warn)]" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{partialCount}</p>
                    <p className="text-xs text-muted-foreground">Partial</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--fail-bg)]">
                    <XCircle className="h-5 w-5 text-[var(--fail)]" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{failCount}</p>
                    <p className="text-xs text-muted-foreground">Failed</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                    <Users className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{project.estimated_workers}</p>
                    <p className="text-xs text-muted-foreground">Workers</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Project Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type</span>
                  <span className="font-medium text-[var(--concrete-600)] capitalize">{project.project_type}</span>
                </div>
                {project.start_date && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Start Date</span>
                    <span className="font-medium text-[var(--concrete-600)]">
                      {format(new Date(project.start_date), 'MMM d, yyyy')}
                    </span>
                  </div>
                )}
                {project.end_date && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">End Date</span>
                    <span className="font-medium text-[var(--concrete-600)]">
                      {format(new Date(project.end_date), 'MMM d, yyyy')}
                    </span>
                  </div>
                )}
                {project.trade_types.length > 0 && (
                  <div>
                    <span className="text-muted-foreground">Trades</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {project.trade_types.map((trade) => (
                        <Badge key={trade} variant="secondary" className="text-xs capitalize">
                          {trade.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {project.description && (
                  <div>
                    <span className="text-muted-foreground">Description</span>
                    <p className="mt-1 text-[var(--concrete-600)]">{project.description}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Safety & Emergency</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {project.special_hazards && (
                  <div className="flex gap-2">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--warn)]" />
                    <div>
                      <span className="font-medium text-[var(--concrete-600)]">Special Hazards</span>
                      <p className="mt-0.5 text-muted-foreground">{project.special_hazards}</p>
                    </div>
                  </div>
                )}
                {project.nearest_hospital && (
                  <div className="flex gap-2">
                    <Hospital className="mt-0.5 h-4 w-4 shrink-0 text-[var(--info)]" />
                    <div>
                      <span className="font-medium text-[var(--concrete-600)]">Nearest Hospital</span>
                      <p className="mt-0.5 text-muted-foreground">{project.nearest_hospital}</p>
                    </div>
                  </div>
                )}
                {project.emergency_contact_name && (
                  <div className="flex gap-2">
                    <Phone className="mt-0.5 h-4 w-4 shrink-0 text-[var(--pass)]" />
                    <div>
                      <span className="font-medium text-[var(--concrete-600)]">Emergency Contact</span>
                      <p className="mt-0.5 text-muted-foreground">
                        {project.emergency_contact_name} — {project.emergency_contact_phone}
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Morning Brief Card */}
          {morningBrief && (
            <Card
              className="cursor-pointer border-primary bg-gradient-to-r from-[var(--machine-wash)] to-[var(--warn-bg)] transition-shadow hover:shadow-md"
              onClick={() => navigate(ROUTES.MORNING_BRIEF(project.id))}
            >
              <CardContent className="flex items-center justify-between py-5">
                <div className="flex items-center gap-4">
                  <div className={`flex h-14 w-14 items-center justify-center rounded-xl ${
                    morningBrief.risk_score <= 3 ? 'bg-[var(--pass-bg)]' :
                    morningBrief.risk_score <= 5 ? 'bg-[var(--warn-bg)]' :
                    morningBrief.risk_score <= 7 ? 'bg-[var(--machine-wash)]' :
                    'bg-[var(--fail-bg)]'
                  }`}>
                    <span className={`text-2xl font-bold ${
                      morningBrief.risk_score <= 3 ? 'text-[var(--pass)]' :
                      morningBrief.risk_score <= 5 ? 'text-[var(--warn)]' :
                      morningBrief.risk_score <= 7 ? 'text-[var(--machine-dark)]' :
                      'text-[var(--fail)]'
                    }`}>
                      {morningBrief.risk_score.toFixed(1)}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <Sun className="h-4 w-4 text-[var(--warn)]" />
                      <p className="text-sm font-semibold text-foreground">Morning Safety Brief</p>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {morningBrief.alerts.filter(a => a.severity === 'critical').length} critical,{' '}
                      {morningBrief.alerts.filter(a => a.severity === 'warning').length} warnings
                    </p>
                  </div>
                </div>
                <Button variant="outline" size="sm" className="border-primary text-[var(--machine-dark)] hover:bg-[var(--machine-wash)]">
                  View Brief
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Recent Activity */}
          {inspections && inspections.length > 0 && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base">Recent Inspections</CardTitle>
                  <CardDescription>Latest inspection activity for this project</CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-[var(--machine-dark)] hover:text-primary"
                  onClick={() => {
                    const tabsTrigger = document.querySelector('[data-state][value="inspections"]') as HTMLElement;
                    tabsTrigger?.click();
                  }}
                >
                  View All
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {inspections.slice(0, 3).map((insp) => (
                    <button
                      key={insp.id}
                      className="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-muted"
                      onClick={() => navigate(ROUTES.INSPECTION_DETAIL(project.id, insp.id))}
                    >
                      <InspectionStatusIcon status={insp.overall_status} />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-[var(--concrete-600)]">
                          {inspectionTypeName(insp.inspection_type)}
                        </p>
                        <p className="text-xs text-muted-foreground">{insp.inspector_name}</p>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {format(new Date(insp.inspection_date), 'MMM d')}
                      </span>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          {/* Recent Toolbox Talks */}
          {toolboxTalks && toolboxTalks.length > 0 && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base">Recent Toolbox Talks</CardTitle>
                  <CardDescription>Latest safety talks for this project</CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-[var(--machine-dark)] hover:text-primary"
                  onClick={() => {
                    const tabsTrigger = document.querySelector('[data-state][value="toolbox-talks"]') as HTMLElement;
                    tabsTrigger?.click();
                  }}
                >
                  View All
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {toolboxTalks.slice(0, 3).map((talk) => (
                    <button
                      key={talk.id}
                      className="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-muted"
                      onClick={() => navigate(
                        talk.status === 'completed'
                          ? ROUTES.TOOLBOX_TALK_DETAIL(project.id, talk.id)
                          : ROUTES.TOOLBOX_TALK_DELIVER(project.id, talk.id)
                      )}
                    >
                      <MessageSquare className={`h-5 w-5 ${talk.status === 'completed' ? 'text-[var(--pass)]' : 'text-[var(--info)]'}`} />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-[var(--concrete-600)]">
                          {talk.topic}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {talk.attendees.length} attendees
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge
                          className={
                            talk.status === 'completed'
                              ? 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]'
                              : 'bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)]'
                          }
                        >
                          {talk.status === 'completed' ? 'Completed' : 'Scheduled'}
                        </Badge>
                      </div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Inspections Tab */}
        <TabsContent value="inspections" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Inspections</h2>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={() => navigate(ROUTES.INSPECTION_NEW(project.id))}
            >
              <Plus className="mr-2 h-4 w-4" />
              New Inspection
            </Button>
          </div>

          {inspections && inspections.length > 0 ? (
            <div className="space-y-3">
              {inspections.map((insp) => {
                const failedItems = insp.items.filter((i) => i.status === 'fail').length;
                const totalItems = insp.items.length;

                return (
                  <Card
                    key={insp.id}
                    className="cursor-pointer transition-shadow hover:shadow-md"
                    onClick={() => navigate(ROUTES.INSPECTION_DETAIL(project.id, insp.id))}
                  >
                    <CardContent className="flex items-center gap-4 py-4">
                      <InspectionStatusIcon status={insp.overall_status} />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-foreground">
                            {inspectionTypeName(insp.inspection_type)}
                          </p>
                          <InspectionStatusBadge status={insp.overall_status} />
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {insp.inspector_name} — {totalItems} items checked
                          {failedItems > 0 && (
                            <span className="text-[var(--fail)]"> ({failedItems} failed)</span>
                          )}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                          <Calendar className="h-3.5 w-3.5" />
                          {format(new Date(insp.inspection_date), 'MMM d, yyyy')}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {insp.workers_on_site} workers on site
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center py-12 text-center">
              <ClipboardCheck className="h-12 w-12 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">No inspections yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Complete your first daily inspection to track compliance
              </p>
              <Button
                className="mt-4 bg-primary hover:bg-[var(--machine-dark)]"
                onClick={() => navigate(ROUTES.INSPECTION_NEW(project.id))}
              >
                <Plus className="mr-2 h-4 w-4" />
                New Inspection
              </Button>
            </div>
          )}
        </TabsContent>

        {/* Toolbox Talks Tab */}
        <TabsContent value="toolbox-talks" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Toolbox Talks</h2>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={() => navigate(ROUTES.TOOLBOX_TALK_NEW(project.id))}
            >
              <Plus className="mr-2 h-4 w-4" />
              New Toolbox Talk
            </Button>
          </div>

          {toolboxTalks && toolboxTalks.length > 0 ? (
            <div className="space-y-3">
              {toolboxTalks.map((talk) => (
                <Card
                  key={talk.id}
                  className="cursor-pointer transition-shadow hover:shadow-md"
                  onClick={() => navigate(
                    talk.status === 'completed'
                      ? ROUTES.TOOLBOX_TALK_DETAIL(project.id, talk.id)
                      : ROUTES.TOOLBOX_TALK_DELIVER(project.id, talk.id)
                  )}
                >
                  <CardContent className="flex items-center gap-4 py-4">
                    <MessageSquare className={`h-5 w-5 ${talk.status === 'completed' ? 'text-[var(--pass)]' : 'text-[var(--info)]'}`} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-foreground">{talk.topic}</p>
                        <Badge
                          className={
                            talk.status === 'completed'
                              ? 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]'
                              : talk.status === 'in_progress'
                                ? 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]'
                                : 'bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)]'
                          }
                        >
                          {talk.status === 'completed' ? 'Completed' : talk.status === 'in_progress' ? 'In Progress' : 'Scheduled'}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {talk.attendees.length} attendees
                        {talk.presented_by && ` — ${talk.presented_by}`}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Calendar className="h-3.5 w-3.5" />
                        {format(new Date(talk.scheduled_date), 'MMM d, yyyy')}
                      </div>
                      <p className="text-xs text-muted-foreground">{talk.duration_minutes} min</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center py-12 text-center">
              <MessageSquare className="h-12 w-12 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">No toolbox talks yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Schedule your first toolbox talk to keep your crew safe
              </p>
              <Button
                className="mt-4 bg-primary hover:bg-[var(--machine-dark)]"
                onClick={() => navigate(ROUTES.TOOLBOX_TALK_NEW(project.id))}
              >
                <Plus className="mr-2 h-4 w-4" />
                New Toolbox Talk
              </Button>
            </div>
          )}
        </TabsContent>

        {/* Hazards Tab */}
        <TabsContent value="hazards" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Hazard Reports</h2>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={() => navigate(ROUTES.HAZARD_REPORT_NEW(project.id))}
            >
              <Plus className="mr-2 h-4 w-4" />
              New Photo Assessment
            </Button>
          </div>

          {hazardReports && hazardReports.length > 0 ? (
            <div className="space-y-3">
              {hazardReports.map((report) => (
                <Card
                  key={report.id}
                  className="cursor-pointer transition-shadow hover:shadow-md"
                  onClick={() => navigate(ROUTES.HAZARD_REPORT_DETAIL(project.id, report.id))}
                >
                  <CardContent className="flex items-center gap-4 py-4">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                      report.highest_severity === 'imminent_danger' || report.highest_severity === 'high'
                        ? 'bg-[var(--fail-bg)]' : report.highest_severity === 'medium'
                        ? 'bg-[var(--warn-bg)]' : 'bg-[var(--info-bg)]'
                    }`}>
                      <Camera className={`h-5 w-5 ${
                        report.highest_severity === 'imminent_danger' || report.highest_severity === 'high'
                          ? 'text-[var(--fail)]' : report.highest_severity === 'medium'
                          ? 'text-[var(--warn)]' : 'text-[var(--info)]'
                      }`} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-foreground">{report.description || report.location}</p>
                        <Badge className={
                          report.status === 'open' ? 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' :
                          report.status === 'in_progress' ? 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' :
                          report.status === 'corrected' ? 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' :
                          'bg-muted text-[var(--concrete-600)] hover:bg-muted'
                        }>
                          {report.status === 'in_progress' ? 'In Progress' : report.status.charAt(0).toUpperCase() + report.status.slice(1)}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {report.hazard_count} hazard{report.hazard_count !== 1 ? 's' : ''} identified
                        {report.highest_severity && ` — Highest: ${report.highest_severity}`}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Calendar className="h-3.5 w-3.5" />
                        {format(new Date(report.created_at), 'MMM d, yyyy')}
                      </div>
                      <p className="text-xs text-muted-foreground">{report.location}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center py-12 text-center">
              <Camera className="h-12 w-12 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">No hazard reports yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Take a photo to identify hazards with AI analysis
              </p>
              <Button
                className="mt-4 bg-primary hover:bg-[var(--machine-dark)]"
                onClick={() => navigate(ROUTES.HAZARD_REPORT_NEW(project.id))}
              >
                <Plus className="mr-2 h-4 w-4" />
                New Photo Assessment
              </Button>
            </div>
          )}
        </TabsContent>

        {/* Incidents Tab */}
        <TabsContent value="incidents" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Incidents</h2>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={() => navigate(ROUTES.INCIDENT_NEW(project.id))}
            >
              <Plus className="mr-2 h-4 w-4" />
              Report Incident
            </Button>
          </div>

          {incidents && incidents.length > 0 ? (
            <div className="space-y-3">
              {incidents.map((incident) => {
                const severityColors: Record<Incident['severity'], string> = {
                  fatality: 'bg-black text-white hover:bg-black',
                  hospitalization: 'bg-[var(--fail)] text-white hover:bg-[var(--fail)]',
                  medical_treatment: 'bg-primary text-primary-foreground hover:bg-primary',
                  first_aid: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]',
                  near_miss: 'bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)]',
                  property_damage: 'bg-muted text-[var(--concrete-600)] hover:bg-muted',
                };
                const severityLabels: Record<Incident['severity'], string> = {
                  fatality: 'Fatality',
                  hospitalization: 'Hospitalization',
                  medical_treatment: 'Medical Treatment',
                  first_aid: 'First Aid',
                  near_miss: 'Near Miss',
                  property_damage: 'Property Damage',
                };
                const statusLabels: Record<Incident['status'], string> = {
                  reported: 'Reported',
                  investigating: 'Investigating',
                  corrective_actions: 'Corrective Actions',
                  closed: 'Closed',
                };
                const statusColors: Record<Incident['status'], string> = {
                  reported: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]',
                  investigating: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]',
                  corrective_actions: 'bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)]',
                  closed: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]',
                };

                return (
                  <Card
                    key={incident.id}
                    className="cursor-pointer transition-shadow hover:shadow-md"
                    onClick={() => navigate(ROUTES.INCIDENT_DETAIL(project.id, incident.id))}
                  >
                    <CardContent className="flex items-center gap-4 py-4">
                      <Siren className={`h-5 w-5 ${
                        incident.severity === 'fatality' || incident.severity === 'hospitalization'
                          ? 'text-[var(--fail)]'
                          : incident.severity === 'near_miss'
                            ? 'text-[var(--info)]'
                            : 'text-[var(--warn)]'
                      }`} />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-medium text-foreground">
                            {incident.description.length > 80
                              ? incident.description.slice(0, 80) + '...'
                              : incident.description}
                          </p>
                          <Badge className={severityColors[incident.severity]}>
                            {severityLabels[incident.severity]}
                          </Badge>
                          <Badge className={statusColors[incident.status]}>
                            {statusLabels[incident.status]}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{incident.location}</p>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                          <Calendar className="h-3.5 w-3.5" />
                          {format(new Date(incident.incident_date), 'MMM d, yyyy')}
                        </div>
                        <p className="text-xs text-muted-foreground">{incident.incident_time}</p>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center py-12 text-center">
              <Siren className="h-12 w-12 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">No incidents reported</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Report incidents to track safety performance and identify trends
              </p>
              <Button
                className="mt-4 bg-primary hover:bg-[var(--machine-dark)]"
                onClick={() => navigate(ROUTES.INCIDENT_NEW(project.id))}
              >
                <Plus className="mr-2 h-4 w-4" />
                Report Incident
              </Button>
            </div>
          )}
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Documents</h2>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={() => navigate(ROUTES.DOCUMENT_NEW)}
            >
              <Plus className="mr-2 h-4 w-4" />
              New Document
            </Button>
          </div>

          {documents && documents.length > 0 ? (
            <div className="space-y-2">
              {documents.map((doc) => (
                <Card
                  key={doc.id}
                  className="cursor-pointer transition-shadow hover:shadow-md"
                  onClick={() => navigate(ROUTES.DOCUMENT_EDIT(doc.id))}
                >
                  <CardContent className="flex items-center gap-3 py-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-[var(--concrete-600)]">{doc.title}</p>
                      <p className="text-xs text-muted-foreground">{doc.document_type.toUpperCase()}</p>
                    </div>
                    <Badge
                      variant={doc.status === 'final' ? 'default' : 'secondary'}
                      className={
                        doc.status === 'final'
                          ? 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]'
                          : ''
                      }
                    >
                      {doc.status === 'final' ? 'Final' : 'Draft'}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">No documents yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Generate safety documents for this project
              </p>
            </div>
          )}
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Project Settings</CardTitle>
              <CardDescription>Update project details and status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Project Name</Label>
                  <Input
                    value={editForm?.name ?? project.name}
                    onChange={(e) => handleEditChange('name', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select
                    value={editForm?.status ?? project.status}
                    onValueChange={(v) => handleEditChange('status', v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="on_hold">On Hold</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Address</Label>
                <Input
                  value={editForm?.address ?? project.address}
                  onChange={(e) => handleEditChange('address', e.target.value)}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Client Name</Label>
                  <Input
                    value={editForm?.client_name ?? project.client_name}
                    onChange={(e) => handleEditChange('client_name', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Project Type</Label>
                  <Select
                    value={editForm?.project_type ?? project.project_type}
                    onValueChange={(v) => handleEditChange('project_type', v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PROJECT_TYPES.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  value={editForm?.description ?? project.description}
                  onChange={(e) => handleEditChange('description', e.target.value)}
                  rows={3}
                />
              </div>

              <Separator />

              <div className="flex justify-end">
                <Button
                  className="bg-primary hover:bg-[var(--machine-dark)]"
                  disabled={!editForm || updateProject.isPending}
                  onClick={handleSaveSettings}
                >
                  {updateProject.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
