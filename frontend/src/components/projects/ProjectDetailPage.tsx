import { useParams } from 'react-router-dom';
import {
  ArrowLeft,
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
  MessageSquare,
  Sun,
  Briefcase,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useProject } from '@/hooks/useProjects';
import { useInspections } from '@/hooks/useInspections';
import { useToolboxTalks } from '@/hooks/useToolboxTalks';
import { useDocuments } from '@/hooks/useDocuments';
import { useMorningBrief } from '@/hooks/useMorningBrief';
import { useDailyLogs } from '@/hooks/useDailyLogs';
import { INSPECTION_TYPES } from '@/lib/constants';
import type { Project, Inspection } from '@/lib/constants';
import { useShell } from '@/hooks/useShell';
import { useProjectActivity } from '@/hooks/useActivityStream';
import { ComplianceRing } from './ComplianceRing';
import { SafetyTab } from './SafetyTab';
import { TeamTab } from './TeamTab';
import { ContractTab } from './ContractTab';
import { WorkTab } from './WorkTab';
import { ActivityStream } from '@/components/activity/ActivityStream';
import { ProvenanceBadge } from '@/components/activity/ProvenanceBadge';
import { format } from 'date-fns';

function StateBadge({ state }: { state: string }) {
  const config: Record<string, { label: string; className: string }> = {
    active: { label: 'Active', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    on_hold: { label: 'On Hold', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
    completed: { label: 'Completed', className: 'bg-muted text-muted-foreground hover:bg-muted' },
    lead: { label: 'Lead', className: 'bg-blue-50 text-blue-700 hover:bg-blue-50' },
    quoted: { label: 'Quoted', className: 'bg-purple-50 text-purple-700 hover:bg-purple-50' },
    closed: { label: 'Closed', className: 'bg-muted text-muted-foreground hover:bg-muted' },
    lost: { label: 'Lost', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
  };
  const { label, className } = config[state] || { label: state, className: 'bg-muted text-muted-foreground hover:bg-muted' };
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

/**
 * Send a chat message programmatically. Finds the chat input, sets its value
 * via the native setter (so React picks up the change), then clicks Send.
 */
function sendChatMessage(message: string) {
  const input = document.querySelector<HTMLInputElement>('input[placeholder="Ask a question..."]');
  if (!input) return;
  const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
  nativeSetter?.call(input, message);
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.focus();
  setTimeout(() => {
    // Find the send button (last button in the input's form/row)
    const sendBtn = input.closest('form')?.querySelector('button[type="submit"]')
      || input.parentElement?.querySelector('button');
    (sendBtn as HTMLElement | null)?.click();
  }, 50);
}

function ContextualActions({ project }: { project: Project }) {
  const shell = useShell();

  switch (project.state) {
    case 'lead':
      return (
        <div className="flex flex-col gap-2">
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => sendChatMessage(`Help me build a quote for ${project.name}`)}
            title="Start a new quote for this lead — Kerf will help build the work items"
          >
            <Briefcase className="mr-2 h-4 w-4" />
            New Quote
          </Button>
          <Button
            variant="outline"
            onClick={() => sendChatMessage(`Qualify the ${project.name} lead — what do we know so far?`)}
            title="Ask Kerf what it knows about this lead — GC history, capacity, certifications, gaps"
          >
            Qualify Lead
          </Button>
        </div>
      );
    case 'quoted':
      return (
        <div className="flex flex-col gap-2">
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => sendChatMessage(`Mark ${project.name} as won — the client accepted the quote`)}
            title="Client accepted the quote — move project to awarded/active and set up the contract"
          >
            Mark as Won
          </Button>
          <Button
            variant="outline"
            onClick={() => sendChatMessage(`Follow up on the quote for ${project.name}`)}
            title="Still waiting on a decision — draft a follow-up message to the client"
          >
            Follow Up
          </Button>
        </div>
      );
    case 'active':
      return (
        <div className="flex flex-col gap-2">
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => sendChatMessage(`Record time on ${project.name}`)}
            title="Log time entries against this project's work items"
          >
            Record Time
          </Button>
          <Button
            variant="outline"
            onClick={() => shell.openCanvas({ component: 'InspectionCreatePage', props: { projectId: project.id }, label: 'New Inspection' })}
            title="Start a safety or quality inspection on this project"
          >
            New Inspection
          </Button>
          <Button
            variant="outline"
            onClick={() => shell.openCanvas({ component: 'DailyLogListPage', props: { projectId: project.id }, label: 'Daily Logs' })}
            title="Open daily logs for this project"
          >
            Daily Log
          </Button>
        </div>
      );
    case 'completed':
      return (
        <div className="flex flex-col gap-2">
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => sendChatMessage(`Generate the final invoice for ${project.name}`)}
            title="Build the final invoice from work item completion"
          >
            Generate Invoice
          </Button>
          <Button
            variant="outline"
            onClick={() => sendChatMessage(`Close out ${project.name} — run me through the checklist`)}
            title="Walk through the closeout checklist — deficiencies, warranty, as-builts"
          >
            Close Out
          </Button>
        </div>
      );
    default:
      return null;
  }
}

export function ProjectDetailPage({ projectId: propProjectId }: { projectId?: string } = {}) {
  const shell = useShell();
  const params = useParams<{ projectId: string }>();
  const projectId = propProjectId || params.projectId;
  const { data: project, isLoading } = useProject(projectId);
  const { data: inspections } = useInspections(projectId);
  const { data: toolboxTalks } = useToolboxTalks(projectId);
  const { data: documents } = useDocuments();
  const { data: morningBrief } = useMorningBrief(projectId);
  const { data: dailyLogs } = useDailyLogs(projectId);
  const activityQuery = useProjectActivity(projectId);

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
        <Button variant="outline" className="mt-4" onClick={() => shell.openCanvas({ component: 'ProjectListPage', props: {}, label: 'Projects' })}>
          Back to Projects
        </Button>
      </div>
    );
  }

  const inspectionTypeName = (typeId: string) =>
    INSPECTION_TYPES.find((t) => t.id === typeId)?.name || typeId;

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
            onClick={() => shell.goBack()}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">{project.name}</h1>
              <StateBadge state={project.state} />
            </div>
            <div className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
              <MapPin className="h-3.5 w-3.5" />
              {project.address}
            </div>
            {project.client_name && (
              <p className="mt-0.5 text-sm text-muted-foreground">{project.client_name}</p>
            )}
            {project.created_by && (
              <div className="mt-2">
                <ProvenanceBadge
                  actorType={project.created_by.startsWith('agent_') ? 'agent' : 'human'}
                  actorId={project.created_by}
                  timestamp={project.created_at}
                  variant="full"
                />
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div
            className="flex flex-col items-center"
            title={`Compliance score: ${project.compliance_score}/100 — based on worker certifications, inspections, incidents and hazards`}
          >
            <ComplianceRing score={project.compliance_score} size="lg" />
            <span className="mt-1 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
              Compliance
            </span>
          </div>
          <ContextualActions project={project} />
        </div>
      </div>

      {/* Tabs — 7 lifecycle tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="contract">Contract</TabsTrigger>
          <TabsTrigger value="work">Work</TabsTrigger>
          <TabsTrigger value="daily-logs">
            Daily Logs {dailyLogs ? `(${dailyLogs.length})` : ''}
          </TabsTrigger>
          <TabsTrigger value="safety">Safety</TabsTrigger>
          <TabsTrigger value="team">Team</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        {/* ═══════ Overview ═══════ */}
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
                  <span className="font-medium capitalize">{project.project_type}</span>
                </div>
                {project.start_date && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Start Date</span>
                    <span className="font-medium">
                      {format(new Date(project.start_date), 'MMM d, yyyy')}
                    </span>
                  </div>
                )}
                {project.end_date && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">End Date</span>
                    <span className="font-medium">
                      {format(new Date(project.end_date), 'MMM d, yyyy')}
                    </span>
                  </div>
                )}
                {project.trade_types?.length > 0 && (
                  <div>
                    <span className="text-muted-foreground">Trades</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {(project.trade_types || []).map((trade) => (
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
                    <p className="mt-1">{project.description}</p>
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
                      <span className="font-medium">Special Hazards</span>
                      <p className="mt-0.5 text-muted-foreground">{project.special_hazards}</p>
                    </div>
                  </div>
                )}
                {project.nearest_hospital && (
                  <div className="flex gap-2">
                    <Hospital className="mt-0.5 h-4 w-4 shrink-0 text-[var(--info)]" />
                    <div>
                      <span className="font-medium">Nearest Hospital</span>
                      <p className="mt-0.5 text-muted-foreground">{project.nearest_hospital}</p>
                    </div>
                  </div>
                )}
                {project.emergency_contact_name && (
                  <div className="flex gap-2">
                    <Phone className="mt-0.5 h-4 w-4 shrink-0 text-[var(--pass)]" />
                    <div>
                      <span className="font-medium">Emergency Contact</span>
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
              onClick={() => shell.openCanvas({ component: 'MorningBriefPage', props: { projectId: project.id }, label: 'Morning Brief' })}
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
                      {morningBrief.alerts?.filter(a => a.severity === 'critical').length ?? 0} critical,{' '}
                      {morningBrief.alerts?.filter(a => a.severity === 'warning').length ?? 0} warnings
                    </p>
                  </div>
                </div>
                <Button variant="outline" size="sm" className="border-primary text-[var(--machine-dark)] hover:bg-[var(--machine-wash)]">
                  View Brief
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Recent Inspections */}
          {inspections && inspections.length > 0 && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base">Recent Inspections</CardTitle>
                  <CardDescription>Latest inspection activity for this project</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {inspections.slice(0, 3).map((insp) => (
                    <button
                      key={insp.id}
                      className="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-muted"
                      onClick={() => shell.openCanvas({ component: 'InspectionDetailPage', props: { projectId: project.id, inspectionId: insp.id }, label: 'Inspection' })}
                    >
                      <InspectionStatusIcon status={insp.overall_status} />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">
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
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {toolboxTalks.slice(0, 3).map((talk) => (
                    <button
                      key={talk.id}
                      className="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-muted"
                      onClick={() => shell.openCanvas({
                        component: talk.status === 'completed' ? 'ToolboxTalkDetailPage' : 'ToolboxTalkDeliverPage',
                        props: { projectId: project.id, talkId: talk.id },
                        label: 'Toolbox Talk',
                      })}
                    >
                      <MessageSquare className={`h-5 w-5 ${talk.status === 'completed' ? 'text-[var(--pass)]' : 'text-[var(--info)]'}`} />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">{talk.topic}</p>
                        <p className="text-xs text-muted-foreground">
                          {(talk.attendees?.length ?? 0)} attendees
                        </p>
                      </div>
                      <Badge
                        className={
                          talk.status === 'completed'
                            ? 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]'
                            : 'bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)]'
                        }
                      >
                        {talk.status === 'completed' ? 'Completed' : 'Scheduled'}
                      </Badge>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ═══════ Contract ═══════ */}
        <TabsContent value="contract">
          <ContractTab project={project} />
        </TabsContent>

        {/* ═══════ Work ═══════ */}
        <TabsContent value="work">
          <WorkTab projectId={project.id} />
        </TabsContent>

        {/* ═══════ Daily Logs ═══════ */}
        <TabsContent value="daily-logs" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Daily Logs</h2>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => shell.openCanvas({ component: 'DailyLogListPage', props: { projectId: project.id }, label: 'Daily Logs' })}
              >
                View All
              </Button>
              <Button
                className="bg-primary hover:bg-[var(--machine-dark)]"
                onClick={() => shell.openCanvas({ component: 'DailyLogListPage', props: { projectId: project.id }, label: 'Daily Logs' })}
              >
                <Plus className="mr-2 h-4 w-4" />
                New Daily Log
              </Button>
            </div>
          </div>

          {dailyLogs && dailyLogs.length > 0 ? (
            <div className="space-y-3">
              {dailyLogs.slice(0, 5).map((log) => {
                const statusColors: Record<string, string> = {
                  draft: 'bg-yellow-100 text-yellow-800',
                  submitted: 'bg-blue-100 text-blue-800',
                  approved: 'bg-green-100 text-green-800',
                };
                return (
                  <Card
                    key={log.id}
                    className="cursor-pointer transition-colors hover:bg-muted/50"
                    onClick={() => shell.openCanvas({ component: 'DailyLogDetailPage', props: { projectId: project.id, dailyLogId: log.id }, label: 'Daily Log' })}
                  >
                    <CardContent className="flex items-center justify-between py-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <p className="text-sm font-medium text-foreground">
                            {format(new Date(log.log_date + 'T00:00:00'), 'EEEE, MMM d, yyyy')}
                          </p>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {log.superintendent_name} - {log.workers_on_site} workers - {log.weather.conditions}
                        </p>
                      </div>
                      <Badge className={statusColors[log.status]}>{log.status}</Badge>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">No daily logs yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Create your first daily log to track daily site activity
              </p>
            </div>
          )}
        </TabsContent>

        {/* ═══════ Safety ═══════ */}
        <TabsContent value="safety">
          <SafetyTab projectId={project.id} />
        </TabsContent>

        {/* ═══════ Team ═══════ */}
        <TabsContent value="team">
          <TeamTab projectId={project.id} />
        </TabsContent>

        {/* ═══════ Documents ═══════ */}
        <TabsContent value="documents" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Documents</h2>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={() => shell.openCanvas({ component: 'DocumentCreatePage', props: {}, label: 'New Document' })}
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
                  onClick={() => shell.openCanvas({ component: 'DocumentEditPage', props: { documentId: doc.id }, label: 'Edit Document' })}
                >
                  <CardContent className="flex items-center gap-3 py-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{doc.title}</p>
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

        {/* ═══════ Activity ═══════ */}
        <TabsContent value="activity">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Project Activity</CardTitle>
              <CardDescription>
                Everything that has happened on this project — inspections, incidents, daily logs, work items, and more.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ActivityStream
                data={activityQuery.data}
                isLoading={activityQuery.isLoading}
                error={activityQuery.error}
                emptyMessage="No activity recorded yet. Events will appear here as the project is worked on."
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
