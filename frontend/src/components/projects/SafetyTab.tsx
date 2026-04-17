import {
  Plus,
  ClipboardCheck,
  Calendar,
  Camera,
  MessageSquare,
  Siren,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useInspections } from '@/hooks/useInspections';
import { useToolboxTalks } from '@/hooks/useToolboxTalks';
import { useHazardReports } from '@/hooks/useHazardReports';
import { useIncidents } from '@/hooks/useIncidents';
import { INSPECTION_TYPES } from '@/lib/constants';
import type { Incident } from '@/lib/constants';
import { useShell } from '@/hooks/useShell';
import { format } from 'date-fns';

function InspectionStatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'pass':
      return <CheckCircle2 className="h-5 w-5 text-[var(--pass)]" />;
    case 'fail':
      return <XCircle className="h-5 w-5 text-[var(--fail)]" />;
    case 'partial':
      return <AlertCircle className="h-5 w-5 text-[var(--warn)]" />;
    default:
      return null;
  }
}

function InspectionStatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    pass: { label: 'Pass', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    fail: { label: 'Fail', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
    partial: { label: 'Partial', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
  };
  const { label, className } = config[status] || { label: status, className: 'bg-muted text-muted-foreground hover:bg-muted' };
  return <Badge className={className}>{label}</Badge>;
}

export function SafetyTab({ projectId }: { projectId: string }) {
  const shell = useShell();
  const { data: inspections } = useInspections(projectId);
  const { data: toolboxTalks } = useToolboxTalks(projectId);
  const { data: hazardReports } = useHazardReports(projectId);
  const { data: incidents } = useIncidents(projectId);

  const inspectionTypeName = (typeId: string) =>
    INSPECTION_TYPES.find((t) => t.id === typeId)?.name || typeId;

  return (
    <div className="space-y-8">
      {/* ── Inspections ── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Inspections</h2>
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => shell.openCanvas({ component: 'InspectionCreatePage', props: { projectId }, label: 'New Inspection' })}
          >
            <Plus className="mr-2 h-4 w-4" />
            New Inspection
          </Button>
        </div>

        {inspections && inspections.length > 0 ? (
          <div className="space-y-3">
            {inspections.map((insp) => {
              const failedItems = (insp.items?.filter((i) => i.status === 'fail').length ?? 0);
              const totalItems = (insp.items?.length ?? 0);
              return (
                <Card
                  key={insp.id}
                  className="cursor-pointer transition-shadow hover:shadow-md"
                  onClick={() => shell.openCanvas({ component: 'InspectionDetailPage', props: { projectId, inspectionId: insp.id }, label: 'Inspection' })}
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
          </div>
        )}
      </section>

      {/* ── Toolbox Talks ── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Toolbox Talks</h2>
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => shell.openCanvas({ component: 'ToolboxTalkCreatePage', props: { projectId }, label: 'New Toolbox Talk' })}
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
                onClick={() => shell.openCanvas({
                  component: talk.status === 'completed' ? 'ToolboxTalkDetailPage' : 'ToolboxTalkDeliverPage',
                  props: { projectId, talkId: talk.id },
                  label: 'Toolbox Talk',
                })}
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
                      {(talk.attendees?.length ?? 0)} attendees
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
          </div>
        )}
      </section>

      {/* ── Hazard Reports ── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Hazard Reports</h2>
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => shell.openCanvas({ component: 'HazardReportPage', props: { projectId }, label: 'New Photo Assessment' })}
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
                onClick={() => shell.openCanvas({ component: 'HazardReportPage', props: { projectId, id: report.id }, label: 'Hazard Report' })}
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
          </div>
        )}
      </section>

      {/* ── Incidents ── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Incidents</h2>
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => shell.openCanvas({ component: 'IncidentCreatePage', props: { projectId }, label: 'Report Incident' })}
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
                  onClick={() => shell.openCanvas({ component: 'IncidentDetailPage', props: { projectId, incidentId: incident.id }, label: 'Incident' })}
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
          </div>
        )}
      </section>
    </div>
  );
}
