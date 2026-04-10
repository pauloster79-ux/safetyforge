import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  AlertTriangle,
  Loader2,
  Clock,
  MapPin,
  FileText,
  Users,
  Eye,
  ShieldAlert,
  CheckCircle2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import { useCreateIncident } from '@/hooks/useIncidents';
import { useProject } from '@/hooks/useProjects';
import { ROUTES } from '@/lib/constants';
import type { Incident } from '@/lib/constants';
import { VoiceRecorder } from '@/components/voice/VoiceRecorder';
import { useParseIncident } from '@/hooks/useVoiceTranscription';

const SEVERITY_OPTIONS: { value: Incident['severity']; label: string }[] = [
  { value: 'fatality', label: 'Fatality' },
  { value: 'hospitalization', label: 'Hospitalization' },
  { value: 'medical_treatment', label: 'Medical Treatment' },
  { value: 'first_aid', label: 'First Aid' },
  { value: 'near_miss', label: 'Near Miss' },
  { value: 'property_damage', label: 'Property Damage' },
];

function OshaGuidance({ severity, visible }: { severity: Incident['severity']; visible: boolean }) {
  if (!visible) return null;

  const isRecordable = ['fatality', 'hospitalization', 'medical_treatment'].includes(severity);

  return (
    <Card className="border-[var(--warn)] bg-[var(--warn-bg)]">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base text-[var(--warn)]">
          <ShieldAlert className="h-5 w-5" />
          OSHA Reporting Guidance
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {severity === 'fatality' && (
          <div className="rounded-lg border border-[var(--fail)] bg-[var(--fail-bg)] p-3">
            <p className="font-bold text-[var(--fail)]">
              OSHA MUST be notified within 8 HOURS
            </p>
            <p className="mt-1 text-[var(--fail)]">
              Call 1-800-321-OSHA (1-800-321-6742) or report online at osha.gov
            </p>
          </div>
        )}
        {(severity === 'hospitalization') && (
          <div className="rounded-lg border border-[var(--fail)] bg-[var(--fail-bg)] p-3">
            <p className="font-bold text-[var(--fail)]">
              OSHA MUST be notified within 24 HOURS
            </p>
            <p className="mt-1 text-[var(--fail)]">
              In-patient hospitalization, amputation, or loss of an eye must be reported.
              Call 1-800-321-OSHA (1-800-321-6742) or report online at osha.gov
            </p>
          </div>
        )}
        {isRecordable && (
          <div className="rounded-lg border border-[var(--warn)] bg-[var(--warn-bg)] p-3">
            <p className="font-semibold text-[var(--warn)]">
              This incident should be added to the OSHA 300 Log
            </p>
            <p className="mt-1 text-[var(--warn)]">
              OSHA-recordable incidents must be documented on OSHA Form 300 within 7 calendar days.
            </p>
          </div>
        )}
        {!isRecordable && severity !== 'fatality' && (
          <div className="rounded-lg border border-[var(--pass)] bg-[var(--pass-bg)] p-3">
            <p className="font-semibold text-[var(--pass)]">
              <CheckCircle2 className="mr-1 inline h-4 w-4" />
              This incident is not OSHA recordable
            </p>
            <p className="mt-1 text-[var(--pass)]">
              However, documenting all incidents including near-misses is a best practice and demonstrates a strong safety culture.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function VoiceIncidentReporter({
  onParsed,
}: {
  onParsed: (data: {
    location?: string;
    severity?: string;
    description?: string;
    persons_involved?: string;
    witnesses?: string;
    immediate_actions_taken?: string;
  }) => void;
}) {
  const parseIncident = useParseIncident();

  const handleTranscript = async (transcript: string) => {
    try {
      const result = await parseIncident.mutateAsync({ transcript });
      onParsed(result);
    } catch {
      // Error shown by VoiceRecorder
    }
  };

  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardContent className="pt-5">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-primary" />
            <div>
              <p className="text-sm font-semibold text-foreground">Voice Report</p>
              <p className="text-xs text-muted-foreground">
                Describe what happened — AI will fill in the form
              </p>
            </div>
          </div>
          <VoiceRecorder
            onTranscript={handleTranscript}
            placeholder="Record incident report"
          />
          {parseIncident.isPending && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing report and filling form fields...
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function IncidentCreatePage() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const { data: project } = useProject(projectId);
  const createIncident = useCreateIncident(projectId || '');

  const today = new Date().toISOString().split('T')[0];
  const nowTime = new Date().toTimeString().slice(0, 5);

  const [form, setForm] = useState({
    incident_date: today,
    incident_time: nowTime,
    location: '',
    severity: '' as Incident['severity'] | '',
    description: '',
    persons_involved: '',
    witnesses: '',
    immediate_actions_taken: '',
  });

  const [submitted, setSubmitted] = useState(false);
  const [createdIncident, setCreatedIncident] = useState<Incident | null>(null);

  const canSubmit =
    form.incident_date &&
    form.incident_time &&
    form.location.trim() &&
    form.severity &&
    form.description.trim() &&
    form.persons_involved.trim() &&
    form.immediate_actions_taken.trim();

  const handleSubmit = async () => {
    if (!canSubmit || !form.severity) return;
    const result = await createIncident.mutateAsync({
      incident_date: form.incident_date,
      incident_time: form.incident_time,
      location: form.location,
      severity: form.severity as Incident['severity'],
      description: form.description,
      persons_involved: form.persons_involved,
      witnesses: form.witnesses,
      immediate_actions_taken: form.immediate_actions_taken,
    });
    setCreatedIncident(result);
    setSubmitted(true);
  };

  if (submitted && createdIncident) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(ROUTES.PROJECT_DETAIL(projectId || ''))}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Incident Reported</h1>
            <p className="text-sm text-muted-foreground">Incident has been logged successfully</p>
          </div>
        </div>

        <Card className="border-[var(--pass)] bg-[var(--pass-bg)]">
          <CardContent className="flex items-center gap-3 py-4">
            <CheckCircle2 className="h-6 w-6 text-[var(--pass)]" />
            <div>
              <p className="font-medium text-[var(--pass)]">Incident report submitted</p>
              <p className="text-sm text-[var(--pass)]">
                Incident ID: {createdIncident.id}
              </p>
            </div>
          </CardContent>
        </Card>

        <OshaGuidance severity={createdIncident.severity} visible={true} />

        <div className="flex gap-3">
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => navigate(ROUTES.INCIDENT_DETAIL(projectId || '', createdIncident.id))}
          >
            View Incident Details
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate(ROUTES.PROJECT_DETAIL(projectId || ''))}
          >
            Back to Project
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(ROUTES.PROJECT_DETAIL(projectId || ''))}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Report Incident</h1>
          <p className="text-sm text-muted-foreground">{project?.name}</p>
        </div>
      </div>

      <VoiceIncidentReporter
        onParsed={(data) =>
          setForm((prev) => ({
            ...prev,
            location: data.location || prev.location,
            severity: (data.severity as Incident['severity']) || prev.severity,
            description: data.description || prev.description,
            persons_involved: data.persons_involved || prev.persons_involved,
            witnesses: data.witnesses || prev.witnesses,
            immediate_actions_taken: data.immediate_actions_taken || prev.immediate_actions_taken,
          }))
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Incident Details</CardTitle>
          <CardDescription>
            Document the incident as accurately and completely as possible
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Date and Time */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="incident_date" className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" /> Date of Incident
              </Label>
              <Input
                id="incident_date"
                type="date"
                value={form.incident_date}
                onChange={(e) => setForm((p) => ({ ...p, incident_date: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="incident_time">Time of Incident</Label>
              <Input
                id="incident_time"
                type="time"
                value={form.incident_time}
                onChange={(e) => setForm((p) => ({ ...p, incident_time: e.target.value }))}
              />
            </div>
          </div>

          {/* Location */}
          <div className="space-y-2">
            <Label htmlFor="location" className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" /> Location
            </Label>
            <Input
              id="location"
              placeholder="e.g., Level 2, East Wing — near demolition staging area"
              value={form.location}
              onChange={(e) => setForm((p) => ({ ...p, location: e.target.value }))}
            />
          </div>

          {/* Severity */}
          <div className="space-y-2">
            <Label className="flex items-center gap-1">
              <AlertTriangle className="h-3.5 w-3.5" /> Severity
            </Label>
            <Select
              value={form.severity}
              onValueChange={(v) => setForm((p) => ({ ...p, severity: v as Incident['severity'] }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select severity level" />
              </SelectTrigger>
              <SelectContent>
                {SEVERITY_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="description" className="flex items-center gap-1">
                <FileText className="h-3.5 w-3.5" /> Description
              </Label>
              <VoiceRecorder
                compact
                onTranscript={(text) =>
                  setForm((p) => ({ ...p, description: p.description ? `${p.description}\n${text}` : text }))
                }
              />
            </div>
            <Textarea
              id="description"
              placeholder="Describe what happened... or tap the mic to dictate"
              className="min-h-[150px]"
              value={form.description}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
            />
          </div>

          {/* Persons Involved */}
          <div className="space-y-2">
            <Label htmlFor="persons_involved" className="flex items-center gap-1">
              <Users className="h-3.5 w-3.5" /> Persons Involved
            </Label>
            <Textarea
              id="persons_involved"
              placeholder="Names and roles of all persons directly involved"
              className="min-h-[80px]"
              value={form.persons_involved}
              onChange={(e) => setForm((p) => ({ ...p, persons_involved: e.target.value }))}
            />
          </div>

          {/* Witnesses */}
          <div className="space-y-2">
            <Label htmlFor="witnesses" className="flex items-center gap-1">
              <Eye className="h-3.5 w-3.5" /> Witnesses
            </Label>
            <Textarea
              id="witnesses"
              placeholder="Names and contact information of witnesses (optional)"
              className="min-h-[80px]"
              value={form.witnesses}
              onChange={(e) => setForm((p) => ({ ...p, witnesses: e.target.value }))}
            />
          </div>

          {/* Immediate Actions Taken */}
          <div className="space-y-2">
            <Label htmlFor="immediate_actions">Immediate Actions Taken</Label>
            <Textarea
              id="immediate_actions"
              placeholder="What actions were taken immediately after the incident?"
              className="min-h-[100px]"
              value={form.immediate_actions_taken}
              onChange={(e) => setForm((p) => ({ ...p, immediate_actions_taken: e.target.value }))}
            />
          </div>

          <Button
            className="w-full bg-primary hover:bg-[var(--machine-dark)]"
            disabled={!canSubmit || createIncident.isPending}
            onClick={handleSubmit}
          >
            {createIncident.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Reporting...
              </>
            ) : (
              <>
                <AlertTriangle className="mr-2 h-4 w-4" />
                Report Incident
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
