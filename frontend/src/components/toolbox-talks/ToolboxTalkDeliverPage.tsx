import { useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import {
  ArrowLeft,
  ArrowRight,
  Loader2,
  Clock,
  Users,
  CheckCircle2,
  UserPlus,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useProject } from '@/hooks/useProjects';
import { useToolboxTalk, useAddAttendee, useCompleteTalk } from '@/hooks/useToolboxTalks';
import { ROUTES } from '@/lib/constants';
import type { ToolboxTalkContent } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

type ContentLang = 'en' | 'es' | 'both';
type Section = 'overview' | 'points' | 'questions' | 'reminders';

const SECTIONS: { id: Section; labelEn: string; labelEs: string }[] = [
  { id: 'overview', labelEn: 'Topic Overview', labelEs: 'Resumen del Tema' },
  { id: 'points', labelEn: 'Key Points', labelEs: 'Puntos Clave' },
  { id: 'questions', labelEn: 'Discussion Questions', labelEs: 'Preguntas de Discusion' },
  { id: 'reminders', labelEn: 'Safety Reminders', labelEs: 'Recordatorios de Seguridad' },
];

export function ToolboxTalkDeliverPage({ projectId: propProjectId, talkId: propTalkId }: { projectId?: string; talkId?: string } = {}) {
  const navigate = useCanvasNavigate();
  const params = useParams<{ projectId: string; talkId: string }>();
  const projectId = propProjectId || params.projectId;
  const talkId = propTalkId || params.talkId;
  const { data: project } = useProject(projectId);
  const { data: talk, isLoading } = useToolboxTalk(projectId, talkId);
  const addAttendee = useAddAttendee(projectId || '');
  const completeTalk = useCompleteTalk(projectId || '');

  const [contentLang, setContentLang] = useState<ContentLang>('both');
  const [currentSection, setCurrentSection] = useState<Section>('overview');
  const [workerName, setWorkerName] = useState('');
  const [workerLang, setWorkerLang] = useState<'en' | 'es'>('en');
  const [attendanceOpen, setAttendanceOpen] = useState(false);

  const handleAddAttendee = useCallback(async () => {
    if (!talkId || !workerName.trim()) return;
    try {
      await addAttendee.mutateAsync({
        id: talkId,
        worker_name: workerName.trim(),
        language_preference: workerLang,
      });
      setWorkerName('');
    } catch {
      // Error handled by mutation
    }
  }, [talkId, workerName, workerLang, addAttendee]);

  const handleComplete = useCallback(async () => {
    if (!talkId || !projectId) return;
    try {
      await completeTalk.mutateAsync(talkId);
      navigate(ROUTES.TOOLBOX_TALK_DETAIL(projectId, talkId));
    } catch {
      // Error handled by mutation
    }
  }, [talkId, projectId, completeTalk, navigate]);

  const sectionIndex = SECTIONS.findIndex((s) => s.id === currentSection);

  const goNext = () => {
    if (sectionIndex < SECTIONS.length - 1) {
      setCurrentSection(SECTIONS[sectionIndex + 1].id);
    }
  };

  const goPrev = () => {
    if (sectionIndex > 0) {
      setCurrentSection(SECTIONS[sectionIndex - 1].id);
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

  const showEn = contentLang === 'en' || contentLang === 'both';
  const showEs = contentLang === 'es' || contentLang === 'both';
  const isBoth = contentLang === 'both';

  const renderContent = (
    content: ToolboxTalkContent,
    lang: 'en' | 'es',
    section: Section
  ) => {
    switch (section) {
      case 'overview':
        return (
          <div className="space-y-4">
            <p className="text-lg leading-relaxed text-[var(--concrete-600)] sm:text-xl">
              {content.topic_overview}
            </p>
          </div>
        );

      case 'points':
        return (
          <div className="space-y-6">
            {(content.key_points || []).map((point, idx) => (
              <div key={idx} className="space-y-3">
                <div className="flex items-start gap-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-base font-bold text-primary-foreground">
                    {idx + 1}
                  </span>
                  <div className="space-y-2">
                    <h4 className="text-lg font-bold text-foreground sm:text-xl">
                      {point.point_title}
                    </h4>
                    <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
                      {point.explanation}
                    </p>
                    {point.real_world_example && (
                      <div className="rounded-lg border-l-4 border-[var(--warn)] bg-[var(--warn-bg)] p-3">
                        <p className="text-sm font-medium text-[var(--warn)] sm:text-base">
                          {lang === 'en' ? 'Real-World Example' : 'Ejemplo del Mundo Real'}
                        </p>
                        <p className="mt-1 text-sm text-[var(--warn)] sm:text-base">
                          {point.real_world_example}
                        </p>
                      </div>
                    )}
                    {point.osha_reference && (
                      <Badge className="bg-[var(--machine-wash)] text-primary hover:bg-[var(--machine-wash)]">
                        {point.osha_reference}
                      </Badge>
                    )}
                  </div>
                </div>
                {idx < (content.key_points || []).length - 1 && <Separator />}
              </div>
            ))}
          </div>
        );

      case 'questions':
        return (
          <div className="space-y-4">
            {(content.discussion_questions || []).map((question, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 rounded-lg border border-border bg-white p-4"
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--concrete-800)] text-base font-bold text-white">
                  {idx + 1}
                </span>
                <p className="pt-0.5 text-base leading-relaxed text-[var(--concrete-600)] sm:text-lg">
                  {question}
                </p>
              </div>
            ))}
          </div>
        );

      case 'reminders':
        return (
          <div className="space-y-3">
            {(content.safety_reminders || []).map((reminder, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 rounded-lg bg-[var(--pass-bg)] p-4"
              >
                <CheckCircle2 className="mt-0.5 h-6 w-6 shrink-0 text-[var(--pass)]" />
                <p className="text-base leading-relaxed text-[var(--concrete-600)] sm:text-lg">
                  {reminder}
                </p>
              </div>
            ))}
            {(content.osha_references || []).length > 0 && (
              <div className="mt-6 space-y-2">
                <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                  {lang === 'en' ? 'OSHA References' : 'Referencias OSHA'}
                </h4>
                <div className="flex flex-wrap gap-2">
                  {(content.osha_references || []).map((ref, idx) => (
                    <Badge
                      key={idx}
                      className="bg-[var(--machine-wash)] text-primary hover:bg-[var(--machine-wash)]"
                    >
                      {ref}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
    }
  };

  const currentSectionData = SECTIONS[sectionIndex];
  const attendeeCount = (talk.attendees || []).length;

  return (
    <div className="mx-auto max-w-5xl pb-28">
      {/* Header */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
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
            <h1 className="text-xl font-bold text-foreground sm:text-2xl">{talk.topic}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <span>{project?.name}</span>
              <span className="text-muted-foreground">|</span>
              <span>{format(new Date(talk.scheduled_date), 'MMM d, yyyy')}</span>
              <Badge variant="secondary" className="text-xs">
                <Clock className="mr-1 h-3 w-3" />
                {talk.duration_minutes} min
              </Badge>
              {talk.status === 'completed' && (
                <Badge className="bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]">
                  Completed
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Language Toggle — big and prominent */}
      <div className="mb-6 flex items-center justify-center gap-2">
        <div className="inline-flex items-center rounded-xl border-2 border-border bg-muted p-1">
          {(['en', 'both', 'es'] as ContentLang[]).map((lang) => (
            <button
              key={lang}
              type="button"
              onClick={() => setContentLang(lang)}
              className={cn(
                'rounded-lg px-5 py-2.5 text-sm font-semibold transition-all sm:px-6 sm:text-base',
                contentLang === lang
                  ? 'bg-white text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-muted-foreground'
              )}
            >
              {lang === 'en' ? 'English' : lang === 'es' ? 'Espanol' : 'Both / Ambos'}
            </button>
          ))}
        </div>
      </div>

      {/* Section Navigation */}
      <div className="mb-4 flex items-center gap-2 overflow-x-auto">
        {SECTIONS.map((section, idx) => (
          <button
            key={section.id}
            type="button"
            onClick={() => setCurrentSection(section.id)}
            className={cn(
              'whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition-colors sm:px-4',
              currentSection === section.id
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted'
            )}
          >
            <span className="mr-1.5">{idx + 1}.</span>
            {showEn ? section.labelEn : section.labelEs}
          </button>
        ))}
      </div>

      {/* Progress bar */}
      <div className="mb-6 h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all duration-300"
          style={{ width: `${((sectionIndex + 1) / SECTIONS.length) * 100}%` }}
        />
      </div>

      {/* Content Area */}
      <div className={cn('gap-6', isBoth ? 'grid lg:grid-cols-2' : '')}>
        {showEn && (
          <Card className="border-2">
            <CardContent className="pt-6">
              {isBoth && (
                <div className="mb-4 flex items-center gap-2">
                  <Badge className="bg-[var(--concrete-800)] text-white hover:bg-[var(--concrete-800)]">
                    English
                  </Badge>
                </div>
              )}
              <h3 className="mb-4 text-lg font-bold text-foreground sm:text-xl">
                {currentSectionData.labelEn}
              </h3>
              {renderContent(talk.content_en, 'en', currentSection)}
            </CardContent>
          </Card>
        )}

        {showEs && (
          <Card className="border-2">
            <CardContent className="pt-6">
              {isBoth && (
                <div className="mb-4 flex items-center gap-2">
                  <Badge className="bg-primary text-primary-foreground hover:bg-primary">
                    Espanol
                  </Badge>
                </div>
              )}
              <h3 className="mb-4 text-lg font-bold text-foreground sm:text-xl">
                {currentSectionData.labelEs}
              </h3>
              {renderContent(talk.content_es, 'es', currentSection)}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Section navigation arrows */}
      <div className="mt-6 flex items-center justify-between">
        <Button
          variant="outline"
          size="lg"
          className="h-12 text-base"
          disabled={sectionIndex === 0}
          onClick={goPrev}
        >
          <ArrowLeft className="mr-2 h-5 w-5" />
          Previous
        </Button>
        <span className="text-sm text-muted-foreground">
          {sectionIndex + 1} / {SECTIONS.length}
        </span>
        <Button
          variant="outline"
          size="lg"
          className="h-12 text-base"
          disabled={sectionIndex === SECTIONS.length - 1}
          onClick={goNext}
        >
          Next
          <ArrowRight className="ml-2 h-5 w-5" />
        </Button>
      </div>

      {/* Fixed bottom bar */}
      <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-white p-4 lg:left-64">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3">
          {/* Attendance button */}
          <Sheet open={attendanceOpen} onOpenChange={setAttendanceOpen}>
            <SheetTrigger
              className="inline-flex h-12 items-center justify-center gap-2 rounded-md border border-border bg-white px-4 text-base font-medium text-[var(--concrete-600)] transition-colors hover:bg-muted"
            >
              <Users className="h-5 w-5" />
              <span className="hidden sm:inline">Attendance</span>
              {attendeeCount > 0 && (
                <Badge className="ml-1 bg-primary text-primary-foreground hover:bg-primary">
                  {attendeeCount}
                </Badge>
              )}
            </SheetTrigger>
            <SheetContent side="bottom" className="max-h-[80vh] overflow-y-auto sm:max-h-[60vh]">
              <SheetHeader>
                <SheetTitle className="flex items-center gap-2 text-lg">
                  <UserPlus className="h-5 w-5 text-primary" />
                  Record Attendance
                </SheetTitle>
              </SheetHeader>

              <div className="mt-4 space-y-4">
                {/* Add attendee form */}
                <div className="flex gap-2">
                  <Input
                    placeholder="Worker name..."
                    value={workerName}
                    onChange={(e) => setWorkerName(e.target.value)}
                    className="h-12 flex-1 text-base"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleAddAttendee();
                    }}
                  />
                  <Select value={workerLang} onValueChange={(v) => v && setWorkerLang(v as 'en' | 'es')}>
                    <SelectTrigger className="h-12 w-20">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">EN</SelectItem>
                      <SelectItem value="es">ES</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button
                    className="h-12 bg-primary px-6 hover:bg-[var(--machine-dark)]"
                    disabled={!workerName.trim() || addAttendee.isPending}
                    onClick={handleAddAttendee}
                  >
                    {addAttendee.isPending ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      'Sign'
                    )}
                  </Button>
                </div>

                {/* Attendee list */}
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">
                    {attendeeCount} worker{attendeeCount !== 1 ? 's' : ''} signed
                  </p>
                  {(talk.attendees || []).map((attendee, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-lg bg-muted px-3 py-2"
                    >
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-[var(--pass)]" />
                        <span className="text-sm font-medium text-[var(--concrete-600)]">
                          {attendee.worker_name}
                        </span>
                        <Badge
                          variant="secondary"
                          className="text-xs"
                        >
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
              </div>
            </SheetContent>
          </Sheet>

          {/* Complete button */}
          {talk.status !== 'completed' ? (
            <Button
              size="lg"
              className="h-12 bg-[var(--pass)] px-6 text-base hover:bg-[var(--pass)] sm:px-8"
              disabled={completeTalk.isPending}
              onClick={handleComplete}
            >
              {completeTalk.isPending ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Completing...
                </>
              ) : (
                <>
                  <CheckCircle2 className="mr-2 h-5 w-5" />
                  Complete Talk
                </>
              )}
            </Button>
          ) : (
            <Badge className="bg-[var(--pass-bg)] px-4 py-2 text-base text-[var(--pass)] hover:bg-[var(--pass-bg)]">
              <CheckCircle2 className="mr-2 h-5 w-5" />
              Talk Completed
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}
