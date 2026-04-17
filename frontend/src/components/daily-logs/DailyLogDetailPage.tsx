import { useNavigate, useParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import {
  ArrowLeft,
  Calendar,
  Cloud,
  Thermometer,
  Wind,
  Users,
  Loader2,
  Pencil,
  Send,
  CheckCircle2,
  ClipboardCheck,
  AlertTriangle,
  Truck,
  Clock,
  UserCheck,
  Wrench,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useProject } from '@/hooks/useProjects';
import { useShell } from '@/hooks/useShell';
import { useDailyLog, useSubmitDailyLog, useApproveDailyLog } from '@/hooks/useDailyLogs';
import { ROUTES } from '@/lib/constants';
import type { DailyLog } from '@/lib/constants';

const STATUS_BADGE_CONFIG: Record<DailyLog['status'], { label: string; className: string }> = {
  draft: { label: 'DRAFT', className: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100' },
  submitted: { label: 'SUBMITTED', className: 'bg-blue-100 text-blue-800 hover:bg-blue-100' },
  approved: { label: 'APPROVED', className: 'bg-green-100 text-green-800 hover:bg-green-100' },
};

export function DailyLogDetailPage({ projectId: propProjectId, dailyLogId: propDailyLogId }: { projectId?: string; dailyLogId?: string } = {}) {
  const navigate = useCanvasNavigate();
  const shell = useShell();
  const params = useParams<{ projectId: string; dailyLogId: string }>();
  const projectId = propProjectId || params.projectId;
  const dailyLogId = propDailyLogId || params.dailyLogId;
  const { data: project } = useProject(projectId);
  const { data: dailyLog, isLoading } = useDailyLog(projectId, dailyLogId);
  const submitMutation = useSubmitDailyLog(projectId || '');
  const approveMutation = useApproveDailyLog(projectId || '');

  const handleSubmit = () => {
    if (!dailyLogId) return;
    submitMutation.mutate(dailyLogId, {
      onSuccess: () => toast.success('Daily log submitted'),
    });
  };

  const handleApprove = () => {
    if (!dailyLogId) return;
    approveMutation.mutate(dailyLogId, {
      onSuccess: () => toast.success('Daily log approved'),
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!dailyLog) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <p className="text-sm text-muted-foreground">Daily log not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate(projectId ? ROUTES.DAILY_LOGS(projectId) : ROUTES.PROJECTS)}
        >
          Back to Daily Logs
        </Button>
      </div>
    );
  }

  const statusConfig = STATUS_BADGE_CONFIG[dailyLog.status];

  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="mt-1"
            onClick={() => navigate(projectId ? ROUTES.DAILY_LOGS(projectId) : ROUTES.PROJECTS)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Daily Log - {new Date(dailyLog.log_date + 'T00:00:00').toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                year: 'numeric',
              })}
            </h1>
            {project && (
              <p className="mt-0.5 text-sm text-muted-foreground">{project.name}</p>
            )}
            <div className="mt-2">
              <Badge className={`${statusConfig.className} px-3 py-1 text-sm`}>
                {statusConfig.label}
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          {dailyLog.status === 'draft' && projectId && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  shell.openCanvas({
                    component: 'DailyLogForm',
                    props: { projectId, dailyLogId: dailyLog.id },
                    label: 'Edit Daily Log',
                  })
                }
              >
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </Button>
              <Button
                size="sm"
                className="bg-primary hover:bg-[var(--machine-dark)]"
                onClick={handleSubmit}
                disabled={submitMutation.isPending}
              >
                <Send className="mr-2 h-4 w-4" />
                Submit
              </Button>
            </>
          )}
          {dailyLog.status === 'submitted' && (
            <Button
              size="sm"
              className="bg-green-600 hover:bg-green-700"
              onClick={handleApprove}
              disabled={approveMutation.isPending}
            >
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Approve
            </Button>
          )}
        </div>
      </div>

      {/* Meta info */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-3 py-3">
            <UserCheck className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Superintendent</p>
              <p className="text-sm font-medium text-[var(--concrete-600)]">{dailyLog.superintendent_name}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-3">
            <Users className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Workers on Site</p>
              <p className="text-sm font-medium text-[var(--concrete-600)]">{dailyLog.workers_on_site}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-3">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Date</p>
              <p className="text-sm font-medium text-[var(--concrete-600)]">
                {new Date(dailyLog.log_date + 'T00:00:00').toLocaleDateString()}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-3">
            <Wrench className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Equipment</p>
              <p className="text-sm font-medium text-[var(--concrete-600)]">{dailyLog.equipment_used || '-'}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Weather */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Cloud className="h-4 w-4" />
            Weather Conditions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <div>
              <p className="text-xs text-muted-foreground">Conditions</p>
              <p className="text-sm font-medium text-[var(--concrete-600)]">{dailyLog.weather.conditions || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">High</p>
              <p className="flex items-center gap-1 text-sm font-medium text-[var(--concrete-600)]">
                <Thermometer className="h-3.5 w-3.5" />
                {dailyLog.weather.temperature_high || '-'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Low</p>
              <p className="flex items-center gap-1 text-sm font-medium text-[var(--concrete-600)]">
                <Thermometer className="h-3.5 w-3.5" />
                {dailyLog.weather.temperature_low || '-'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Wind</p>
              <p className="flex items-center gap-1 text-sm font-medium text-[var(--concrete-600)]">
                <Wind className="h-3.5 w-3.5" />
                {dailyLog.weather.wind || '-'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Precipitation</p>
              <p className="text-sm font-medium text-[var(--concrete-600)]">{dailyLog.weather.precipitation || '-'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Work Performed */}
      {dailyLog.work_performed && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Work Performed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm text-[var(--concrete-600)]">{dailyLog.work_performed}</p>
          </CardContent>
        </Card>
      )}

      {/* Materials Delivered */}
      {(dailyLog.materials_delivered || []).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Truck className="h-4 w-4" />
              Materials Delivered
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(dailyLog.materials_delivered || []).map((m, idx) => (
                <div key={idx}>
                  <div className="grid gap-2 sm:grid-cols-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Material</p>
                      <p className="text-sm font-medium text-[var(--concrete-600)]">{m.material}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Quantity</p>
                      <p className="text-sm text-[var(--concrete-600)]">{m.quantity}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Supplier</p>
                      <p className="text-sm text-[var(--concrete-600)]">{m.supplier}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Received By</p>
                      <p className="text-sm text-[var(--concrete-600)]">{m.received_by}</p>
                    </div>
                  </div>
                  {idx < (dailyLog.materials_delivered || []).length - 1 && <Separator className="mt-3" />}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Delays */}
      {(dailyLog.delays || []).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Clock className="h-4 w-4" />
              Delays
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(dailyLog.delays || []).map((d, idx) => (
                <div key={idx}>
                  <div className="grid gap-2 sm:grid-cols-2">
                    <div>
                      <p className="text-xs text-muted-foreground">Type</p>
                      <p className="text-sm font-medium capitalize text-[var(--concrete-600)]">{d.delay_type}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Duration</p>
                      <p className="text-sm text-[var(--concrete-600)]">{d.duration_hours} hours</p>
                    </div>
                    <div className="sm:col-span-2">
                      <p className="text-xs text-muted-foreground">Description</p>
                      <p className="text-sm text-[var(--concrete-600)]">{d.description}</p>
                    </div>
                    {d.impact && (
                      <div className="sm:col-span-2">
                        <p className="text-xs text-muted-foreground">Impact</p>
                        <p className="text-sm text-[var(--concrete-600)]">{d.impact}</p>
                      </div>
                    )}
                  </div>
                  {idx < (dailyLog.delays || []).length - 1 && <Separator className="mt-3" />}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Visitors */}
      {(dailyLog.visitors || []).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Users className="h-4 w-4" />
              Visitors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(dailyLog.visitors || []).map((v, idx) => (
                <div key={idx}>
                  <div className="grid gap-2 sm:grid-cols-3">
                    <div>
                      <p className="text-xs text-muted-foreground">Name</p>
                      <p className="text-sm font-medium text-[var(--concrete-600)]">{v.name}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Company</p>
                      <p className="text-sm text-[var(--concrete-600)]">{v.company}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Purpose</p>
                      <p className="text-sm text-[var(--concrete-600)]">{v.purpose}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Time In</p>
                      <p className="text-sm text-[var(--concrete-600)]">{v.time_in}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Time Out</p>
                      <p className="text-sm text-[var(--concrete-600)]">{v.time_out}</p>
                    </div>
                  </div>
                  {idx < (dailyLog.visitors || []).length - 1 && <Separator className="mt-3" />}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Safety Incidents */}
      {dailyLog.safety_incidents && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-4 w-4" />
              Safety Incidents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm text-[var(--concrete-600)]">{dailyLog.safety_incidents}</p>
          </CardContent>
        </Card>
      )}

      {/* Auto-populated summaries */}
      {((dailyLog.inspections_summary || []).length > 0 || (dailyLog.toolbox_talks_summary || []).length > 0 || (dailyLog.incidents_summary || []).length > 0) && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Activity Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {(dailyLog.inspections_summary || []).length > 0 && (
              <div>
                <p className="flex items-center gap-1 text-xs font-semibold uppercase text-muted-foreground">
                  <ClipboardCheck className="h-3.5 w-3.5" />
                  Inspections
                </p>
                <div className="mt-1 space-y-1">
                  {(dailyLog.inspections_summary || []).map((insp) => (
                    <div key={insp.id} className="flex items-center gap-2 text-sm text-[var(--concrete-600)]">
                      <Badge variant="secondary" className={insp.status === 'pass' ? 'bg-green-100 text-green-800' : insp.status === 'fail' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}>
                        {insp.status}
                      </Badge>
                      <span>{insp.type}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {(dailyLog.toolbox_talks_summary || []).length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase text-muted-foreground">Toolbox Talks</p>
                <div className="mt-1 space-y-1">
                  {(dailyLog.toolbox_talks_summary || []).map((talk) => (
                    <p key={talk.id} className="text-sm text-[var(--concrete-600)]">
                      {talk.topic} ({talk.attendees} attendees)
                    </p>
                  ))}
                </div>
              </div>
            )}
            {(dailyLog.incidents_summary || []).length > 0 && (
              <div>
                <p className="flex items-center gap-1 text-xs font-semibold uppercase text-[var(--fail)]">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Incidents
                </p>
                <div className="mt-1 space-y-1">
                  {(dailyLog.incidents_summary || []).map((inc) => (
                    <p key={inc.id} className="text-sm text-[var(--concrete-600)]">
                      [{inc.severity}] {inc.description}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Notes */}
      {dailyLog.notes && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm text-[var(--concrete-600)]">{dailyLog.notes}</p>
          </CardContent>
        </Card>
      )}

      {/* Audit trail */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Audit Trail
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-xs text-muted-foreground">
          <p>Created: {new Date(dailyLog.created_at).toLocaleString()}</p>
          <p>Updated: {new Date(dailyLog.updated_at).toLocaleString()}</p>
          {dailyLog.submitted_at && <p>Submitted: {new Date(dailyLog.submitted_at).toLocaleString()}</p>}
          {dailyLog.approved_at && <p>Approved: {new Date(dailyLog.approved_at).toLocaleString()}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
