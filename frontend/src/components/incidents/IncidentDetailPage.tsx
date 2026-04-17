import { useNavigate, useParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import {
  ArrowLeft,
  AlertTriangle,
  Loader2,
  Clock,
  MapPin,
  Users,
  Eye,
  ShieldAlert,
  CheckCircle2,
  Circle,
  Search,
  Wrench,
  XCircle,
  Brain,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useIncident, useUpdateIncident, useInvestigateIncident } from '@/hooks/useIncidents';
import { useProject } from '@/hooks/useProjects';
import { ROUTES } from '@/lib/constants';
import type { Incident } from '@/lib/constants';
import { ProvenanceBadge } from '@/components/activity/ProvenanceBadge';
import { format } from 'date-fns';

const SEVERITY_CONFIG: Record<Incident['severity'], { label: string; className: string }> = {
  fatality: { label: 'Fatality', className: 'bg-black text-white hover:bg-black' },
  hospitalization: { label: 'Hospitalization', className: 'bg-[var(--fail)] text-white hover:bg-[var(--fail)]' },
  medical_treatment: { label: 'Medical Treatment', className: 'bg-primary text-primary-foreground hover:bg-primary' },
  first_aid: { label: 'First Aid', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
  near_miss: { label: 'Near Miss', className: 'bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)]' },
  property_damage: { label: 'Property Damage', className: 'bg-muted text-[var(--concrete-600)] hover:bg-muted' },
};

const STATUS_STEPS: { key: Incident['status']; label: string; icon: typeof Circle }[] = [
  { key: 'reported', label: 'Reported', icon: AlertTriangle },
  { key: 'investigating', label: 'Investigating', icon: Search },
  { key: 'corrective_actions', label: 'Corrective Actions', icon: Wrench },
  { key: 'closed', label: 'Closed', icon: CheckCircle2 },
];

function StatusStepper({ currentStatus }: { currentStatus: Incident['status'] }) {
  const statusOrder: Incident['status'][] = ['reported', 'investigating', 'corrective_actions', 'closed'];
  const currentIdx = statusOrder.indexOf(currentStatus);

  return (
    <div className="flex items-center gap-2">
      {STATUS_STEPS.map((step, idx) => {
        const isComplete = idx < currentIdx;
        const isCurrent = idx === currentIdx;
        const StepIcon = step.icon;

        return (
          <div key={step.key} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-full ${
                  isComplete
                    ? 'bg-[var(--pass-bg)] text-[var(--pass)]'
                    : isCurrent
                      ? 'bg-[var(--machine-wash)] text-[var(--machine-dark)] ring-2 ring-primary'
                      : 'bg-muted text-muted-foreground'
                }`}
              >
                <StepIcon className="h-5 w-5" />
              </div>
              <span
                className={`mt-1 text-xs font-medium ${
                  isComplete ? 'text-[var(--pass)]' : isCurrent ? 'text-[var(--machine-dark)]' : 'text-muted-foreground'
                }`}
              >
                {step.label}
              </span>
            </div>
            {idx < STATUS_STEPS.length - 1 && (
              <div
                className={`mx-2 h-0.5 w-8 ${
                  idx < currentIdx ? 'bg-[var(--pass)]' : 'bg-muted'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function IncidentDetailPage({ projectId: propProjectId, incidentId: propIncidentId }: { projectId?: string; incidentId?: string } = {}) {
  const navigate = useCanvasNavigate();
  const params = useParams<{ projectId: string; id: string }>();
  const projectId = propProjectId || params.projectId;
  const id = propIncidentId || params.id;
  const { data: incident, isLoading } = useIncident(projectId, id);
  const { data: project } = useProject(projectId);
  const updateIncident = useUpdateIncident(projectId || '');
  const investigateIncident = useInvestigateIncident(projectId || '');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <p className="text-sm text-muted-foreground">Incident not found</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate(ROUTES.PROJECT_DETAIL(projectId || ''))}>
          Back to Project
        </Button>
      </div>
    );
  }

  const severityConfig = SEVERITY_CONFIG[incident.severity];
  const statusOrder: Incident['status'][] = ['reported', 'investigating', 'corrective_actions', 'closed'];
  const currentIdx = statusOrder.indexOf(incident.status);
  const nextStatus = currentIdx < statusOrder.length - 1 ? statusOrder[currentIdx + 1] : null;
  const nextStatusLabel = nextStatus
    ? STATUS_STEPS.find((s) => s.key === nextStatus)?.label || nextStatus
    : null;

  const isRecordable = ['fatality', 'hospitalization', 'medical_treatment'].includes(incident.severity);
  const isReportable = ['fatality', 'hospitalization'].includes(incident.severity);

  const hasAiAnalysis = incident.ai_analysis && Object.keys(incident.ai_analysis).length > 0;
  const aiAnalysis = incident.ai_analysis as {
    immediate_cause?: string;
    contributing_factors?: string[];
    root_causes?: string[];
    corrective_action_recommendations?: string[];
    severity_assessment?: string;
  };

  const handleAdvanceStatus = async () => {
    if (!nextStatus || !id) return;
    await updateIncident.mutateAsync({ id, status: nextStatus });
  };

  const handleInvestigate = async () => {
    if (!id) return;
    await investigateIncident.mutateAsync(id);
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="mt-1"
            onClick={() => navigate(ROUTES.PROJECT_DETAIL(projectId || ''))}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">Incident Report</h1>
              <Badge className={severityConfig.className}>{severityConfig.label}</Badge>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{project?.name}</p>
            <div className="mt-1 flex items-center gap-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                {format(new Date(incident.incident_date), 'MMM d, yyyy')} at {incident.incident_time}
              </span>
              <span className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                {incident.location}
              </span>
            </div>
            {incident.created_by && (
              <div className="mt-2">
                <ProvenanceBadge
                  actorType={incident.created_by.startsWith('agent_') ? 'agent' : 'human'}
                  actorId={incident.created_by}
                  timestamp={incident.created_at}
                  variant="full"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status Stepper */}
      <Card>
        <CardContent className="flex flex-col items-center gap-4 py-6 sm:flex-row sm:justify-between">
          <StatusStepper currentStatus={incident.status} />
          {nextStatus && (
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              disabled={updateIncident.isPending}
              onClick={handleAdvanceStatus}
            >
              {updateIncident.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Move to {nextStatusLabel}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* OSHA Status */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card className={isReportable ? 'border-[var(--fail)] bg-[var(--fail-bg)]' : isRecordable ? 'border-[var(--warn)] bg-[var(--warn-bg)]' : 'border-[var(--pass)] bg-[var(--pass-bg)]'}>
          <CardContent className="flex items-center gap-3 py-4">
            <ShieldAlert className={`h-5 w-5 ${isReportable ? 'text-[var(--fail)]' : isRecordable ? 'text-[var(--warn)]' : 'text-[var(--pass)]'}`} />
            <div>
              <p className={`text-sm font-medium ${isReportable ? 'text-[var(--fail)]' : isRecordable ? 'text-[var(--warn)]' : 'text-[var(--pass)]'}`}>
                {isReportable ? 'OSHA Reportable' : isRecordable ? 'OSHA Recordable' : 'Not OSHA Recordable'}
              </p>
              <p className={`text-xs ${isReportable ? 'text-[var(--fail)]' : isRecordable ? 'text-[var(--warn)]' : 'text-[var(--pass)]'}`}>
                {isReportable && incident.severity === 'fatality'
                  ? 'Must report within 8 hours — 1-800-321-OSHA'
                  : isReportable
                    ? 'Must report within 24 hours — 1-800-321-OSHA'
                    : isRecordable
                      ? 'Record on OSHA 300 Log within 7 days'
                      : 'Document for safety records'}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-4">
            <AlertTriangle className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">
                Status: {STATUS_STEPS.find((s) => s.key === incident.status)?.label}
              </p>
              <p className="text-xs text-muted-foreground">
                Reported {format(new Date(incident.created_at), 'MMM d, yyyy h:mm a')}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Incident Details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Incident Description</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <p className="text-[var(--concrete-600)] leading-relaxed">{incident.description}</p>

          <Separator />

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <Users className="h-3.5 w-3.5" />
                <span className="font-medium">Persons Involved</span>
              </div>
              <p className="mt-1 text-[var(--concrete-600)]">{incident.persons_involved}</p>
            </div>
            <div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <Eye className="h-3.5 w-3.5" />
                <span className="font-medium">Witnesses</span>
              </div>
              <p className="mt-1 text-[var(--concrete-600)]">{incident.witnesses || 'None recorded'}</p>
            </div>
          </div>

          <Separator />

          <div>
            <p className="font-medium text-muted-foreground">Immediate Actions Taken</p>
            <p className="mt-1 text-[var(--concrete-600)]">{incident.immediate_actions_taken}</p>
          </div>

          {incident.root_cause && (
            <>
              <Separator />
              <div>
                <p className="font-medium text-muted-foreground">Root Cause</p>
                <p className="mt-1 text-[var(--concrete-600)]">{incident.root_cause}</p>
              </div>
            </>
          )}

          {incident.corrective_actions && (
            <div>
              <p className="font-medium text-muted-foreground">Corrective Actions</p>
              <p className="mt-1 text-[var(--concrete-600)]">{incident.corrective_actions}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI Investigation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Brain className="h-5 w-5 text-purple-500" />
            AI Root Cause Investigation
          </CardTitle>
          <CardDescription>
            AI-powered analysis of the incident to identify root causes and recommend corrective actions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {hasAiAnalysis ? (
            <div className="space-y-4 text-sm">
              {aiAnalysis.immediate_cause && (
                <div>
                  <p className="font-semibold text-[var(--concrete-600)]">Immediate Cause</p>
                  <p className="mt-1 text-muted-foreground">{aiAnalysis.immediate_cause}</p>
                </div>
              )}
              {aiAnalysis.contributing_factors && aiAnalysis.contributing_factors.length > 0 && (
                <div>
                  <p className="font-semibold text-[var(--concrete-600)]">Contributing Factors</p>
                  <ul className="mt-1 space-y-1">
                    {aiAnalysis.contributing_factors.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-muted-foreground">
                        <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--warn)]" />
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {aiAnalysis.root_causes && aiAnalysis.root_causes.length > 0 && (
                <div>
                  <p className="font-semibold text-[var(--concrete-600)]">Root Causes</p>
                  <ul className="mt-1 space-y-1">
                    {aiAnalysis.root_causes.map((c, i) => (
                      <li key={i} className="flex items-start gap-2 text-muted-foreground">
                        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--fail)]" />
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {aiAnalysis.corrective_action_recommendations && aiAnalysis.corrective_action_recommendations.length > 0 && (
                <div>
                  <p className="font-semibold text-[var(--concrete-600)]">Recommended Corrective Actions</p>
                  <ul className="mt-1 space-y-1">
                    {aiAnalysis.corrective_action_recommendations.map((r, i) => (
                      <li key={i} className="flex items-start gap-2 text-muted-foreground">
                        <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--pass)]" />
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {aiAnalysis.severity_assessment && (
                <div className="rounded-lg bg-purple-50 p-3">
                  <p className="font-semibold text-purple-800">Severity Assessment</p>
                  <p className="mt-1 text-sm text-purple-700">{aiAnalysis.severity_assessment}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center py-8 text-center">
              <Brain className="h-12 w-12 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">No AI analysis yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Run an AI investigation to generate root cause analysis and corrective action recommendations
              </p>
              <Button
                className="mt-4 bg-purple-600 hover:bg-purple-700"
                disabled={investigateIncident.isPending}
                onClick={handleInvestigate}
              >
                {investigateIncident.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Brain className="mr-2 h-4 w-4" />
                    Run AI Investigation
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
