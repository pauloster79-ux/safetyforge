import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import {
  ArrowLeft,
  Loader2,
  Clock,
  Users,
  CheckCircle2,
  Calendar,
  User,
  Printer,
  Download,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useProject } from '@/hooks/useProjects';
import { useToolboxTalk } from '@/hooks/useToolboxTalks';
import { ROUTES } from '@/lib/constants';
import type { ToolboxTalkContent } from '@/lib/constants';
import { downloadPdf } from '@/lib/pdf';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

type ContentLang = 'en' | 'es';

export function ToolboxTalkDetailPage({ projectId: propProjectId, talkId: propTalkId }: { projectId?: string; talkId?: string } = {}) {
  const navigate = useCanvasNavigate();
  const params = useParams<{ projectId: string; talkId: string }>();
  const projectId = propProjectId || params.projectId;
  const talkId = propTalkId || params.talkId;
  const { data: project } = useProject(projectId);
  const { data: talk, isLoading } = useToolboxTalk(projectId, talkId);

  const [contentLang, setContentLang] = useState<ContentLang>('en');
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    try {
      await downloadPdf(
        `/me/toolbox-talks/${talkId}/pdf`,
        `ToolboxTalk-${talk?.topic || talkId}.pdf`,
      );
    } catch {
      // error handling at caller level
    } finally {
      setIsDownloading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!talk) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <p className="text-sm text-muted-foreground">Toolbox talk not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate(projectId ? ROUTES.PROJECT_DETAIL(projectId) : ROUTES.PROJECTS)}
        >
          Back to Project
        </Button>
      </div>
    );
  }

  const hasEnglish = talk.content_en && Object.keys(talk.content_en).length > 0;
  const hasSpanish = talk.content_es && Object.keys(talk.content_es).length > 0;
  const hasBoth = hasEnglish && hasSpanish;

  // If only one language exists, force that language selection
  const effectiveLang: ContentLang = hasBoth
    ? contentLang
    : hasEnglish
      ? 'en'
      : 'es';

  const content: ToolboxTalkContent = (effectiveLang === 'en' ? talk.content_en : talk.content_es) || { key_points: [], discussion_questions: [], safety_reminders: [] } as ToolboxTalkContent;
  const statusConfig: Record<string, { label: string; className: string }> = {
    scheduled: { label: 'Scheduled', className: 'bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)]' },
    in_progress: { label: 'In Progress', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
    completed: { label: 'Completed', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
  };
  const { label: statusLabel, className: statusClassName } = statusConfig[talk.status] || { label: talk.status, className: 'bg-muted text-muted-foreground hover:bg-muted' };

  return (
    <div className="mx-auto max-w-4xl space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="mt-0.5"
            onClick={() =>
              navigate(projectId ? ROUTES.PROJECT_DETAIL(projectId) : ROUTES.PROJECTS)
            }
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">{talk.topic}</h1>
              <Badge className={statusClassName}>{statusLabel}</Badge>
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <span>{project?.name}</span>
              <span className="text-muted-foreground">|</span>
              <span>{format(new Date(talk.scheduled_date), 'MMM d, yyyy')}</span>
              <Badge variant="secondary" className="text-xs">
                <Clock className="mr-1 h-3 w-3" />
                {talk.duration_minutes} min
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {talk.status !== 'completed' && projectId && talkId && (
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={() => navigate(ROUTES.TOOLBOX_TALK_DELIVER(projectId, talkId))}
            >
              Deliver Talk
            </Button>
          )}
          <Button variant="outline" onClick={() => window.print()}>
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
          <Button variant="outline" onClick={handleDownloadPdf} disabled={isDownloading}>
            {isDownloading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
            Download PDF
          </Button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="flex items-center gap-3 pt-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--machine-wash)]">
              <Users className="h-5 w-5 text-[var(--machine-dark)]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{talk.attendees.length}</p>
              <p className="text-xs text-muted-foreground">Attendees</p>
            </div>
          </CardContent>
        </Card>
        {talk.presented_by && (
          <Card>
            <CardContent className="flex items-center gap-3 pt-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                <User className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-bold text-foreground">{talk.presented_by}</p>
                <p className="text-xs text-muted-foreground">Presenter</p>
              </div>
            </CardContent>
          </Card>
        )}
        {talk.presented_at && (
          <Card>
            <CardContent className="flex items-center gap-3 pt-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--pass-bg)]">
                <Calendar className="h-5 w-5 text-[var(--pass)]" />
              </div>
              <div>
                <p className="text-sm font-bold text-foreground">
                  {format(new Date(talk.presented_at), 'MMM d, h:mm a')}
                </p>
                <p className="text-xs text-muted-foreground">Completed</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Language toggle — only shown when both languages have content */}
      {hasBoth && (
        <div className="flex justify-center">
          <div className="inline-flex items-center rounded-lg border border-border bg-muted p-0.5">
            <button
              type="button"
              onClick={() => setContentLang('en')}
              className={cn(
                'rounded-md px-4 py-2 text-sm font-medium transition-all',
                effectiveLang === 'en'
                  ? 'bg-white text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-[var(--concrete-600)]'
              )}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => setContentLang('es')}
              className={cn(
                'rounded-md px-4 py-2 text-sm font-medium transition-all',
                effectiveLang === 'es'
                  ? 'bg-white text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-[var(--concrete-600)]'
              )}
            >
              Espanol
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {effectiveLang === 'en' ? 'Topic Overview' : 'Resumen del Tema'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="leading-relaxed text-muted-foreground">{content.topic_overview}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {effectiveLang === 'en' ? 'Key Points' : 'Puntos Clave'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {(content.key_points || []).map((point, idx) => (
            <div key={idx} className="space-y-2">
              <div className="flex items-start gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                  {idx + 1}
                </span>
                <div className="space-y-1">
                  <h4 className="font-semibold text-foreground">{point.point_title}</h4>
                  <p className="text-sm text-muted-foreground">{point.explanation}</p>
                  {point.real_world_example && (
                    <div className="rounded-md border-l-4 border-[var(--warn)] bg-[var(--warn-bg)] p-2">
                      <p className="text-xs text-[var(--warn)]">{point.real_world_example}</p>
                    </div>
                  )}
                  {point.osha_reference && (
                    <Badge className="bg-[var(--machine-wash)] text-xs text-primary hover:bg-[var(--machine-wash)]">
                      {point.osha_reference}
                    </Badge>
                  )}
                </div>
              </div>
              {idx < content.key_points.length - 1 && <Separator />}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {effectiveLang === 'en' ? 'Discussion Questions' : 'Preguntas de Discusion'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {(content.discussion_questions || []).map((q, idx) => (
            <div key={idx} className="flex items-start gap-3 rounded-md bg-muted p-3">
              <span className="text-sm font-semibold text-muted-foreground">{idx + 1}.</span>
              <p className="text-sm text-[var(--concrete-600)]">{q}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {effectiveLang === 'en' ? 'Safety Reminders' : 'Recordatorios de Seguridad'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {(content.safety_reminders || []).map((reminder, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[var(--pass)]" />
              <p className="text-sm text-[var(--concrete-600)]">{reminder}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Attendance */}
      {(talk.attendees?.length ?? 0) > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Attendance ({talk.attendees.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {(talk.attendees || []).map((attendee, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between rounded-md bg-muted px-3 py-2"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[var(--pass)]" />
                    <span className="text-sm font-medium text-[var(--concrete-600)]">
                      {attendee.worker_name}
                    </span>
                    <Badge variant="secondary" className="text-xs">
                      {attendee.language_preference.toUpperCase()}
                    </Badge>
                  </div>
                  {attendee.signed_at && (
                    <span className="text-xs text-muted-foreground">
                      {format(new Date(attendee.signed_at), 'h:mm a')}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notes */}
      {talk.overall_notes && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{talk.overall_notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
