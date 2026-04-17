import { useState, useMemo, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import {
  ArrowLeft,
  ArrowRight,
  Loader2,
  Check,
  X,
  Minus,
  ClipboardCheck,
  Building,
  Zap,
  Wrench,
  Flame,
  Camera,
  Send,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useProject } from '@/hooks/useProjects';
import { useCreateInspection, useInspectionTemplate } from '@/hooks/useInspections';
import {
  ROUTES,
  INSPECTION_TYPES,
} from '@/lib/constants';
import { VoiceRecorder } from '@/components/voice/VoiceRecorder';
import { cn } from '@/lib/utils';

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  ClipboardCheck,
  Building,
  Zap,
  Wrench,
  Flame,
};

type Step = 'type' | 'header' | 'checklist' | 'summary';

interface ChecklistItemState {
  item_id: string;
  category: string;
  description: string;
  status: 'pass' | 'fail' | 'na' | 'pending';
  notes: string;
  photo_url: string | null;
}

export function InspectionCreatePage({ projectId: propProjectId }: { projectId?: string } = {}) {
  const navigate = useCanvasNavigate();
  const params = useParams<{ projectId: string }>();
  const projectId = propProjectId || params.projectId;
  const { data: project } = useProject(projectId);
  const createInspection = useCreateInspection(projectId || '');

  const [step, setStep] = useState<Step>('type');
  const [selectedType, setSelectedType] = useState('');
  const [expandedFail, setExpandedFail] = useState<string | null>(null);

  // Header info
  const [header, setHeader] = useState({
    inspection_date: new Date().toISOString().split('T')[0],
    inspector_name: '',
    weather_conditions: '',
    temperature: '',
    wind_conditions: '',
    workers_on_site: '',
  });

  // Checklist items
  const [items, setItems] = useState<ChecklistItemState[]>([]);

  // Summary
  const [overallNotes, setOverallNotes] = useState('');
  const [correctiveActions, setCorrectiveActions] = useState('');

  const { data: template, isLoading: isTemplateLoading } = useInspectionTemplate(selectedType);

  // Populate checklist items when template data arrives
  useEffect(() => {
    if (template && (template.items || []).length > 0) {
      setItems(
        (template.items || []).map((item) => ({
          ...item,
          status: 'pending' as const,
          notes: '',
          photo_url: null,
        }))
      );
    }
  }, [template]);

  const handleSelectType = (typeId: string) => {
    setSelectedType(typeId);
    setItems([]);
    setStep('header');
  };

  const handleHeaderChange = (field: string, value: string) => {
    setHeader((prev) => ({ ...prev, [field]: value }));
  };

  const isHeaderValid = header.inspector_name.trim() && header.inspection_date;

  const handleItemStatus = (itemId: string, status: 'pass' | 'fail' | 'na') => {
    setItems((prev) =>
      prev.map((item) =>
        item.item_id === itemId ? { ...item, status } : item
      )
    );
    if (status === 'fail') {
      setExpandedFail(itemId);
    } else if (expandedFail === itemId) {
      setExpandedFail(null);
    }
  };

  const handleItemNotes = (itemId: string, notes: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.item_id === itemId ? { ...item, notes } : item
      )
    );
  };

  const categories = useMemo(() => {
    const cats: { name: string; items: ChecklistItemState[] }[] = [];
    for (const item of items) {
      const existing = cats.find((c) => c.name === item.category);
      if (existing) {
        existing.items.push(item);
      } else {
        cats.push({ name: item.category, items: [item] });
      }
    }
    return cats;
  }, [items]);

  const completedCount = items.filter((i) => i.status !== 'pending').length;
  const failedCount = items.filter((i) => i.status === 'fail').length;
  const allComplete = items.length > 0 && completedCount === items.length;

  const overallStatus = (): 'pass' | 'fail' | 'partial' => {
    if (failedCount === 0) return 'pass';
    if (failedCount === items.filter((i) => i.status !== 'na').length) return 'fail';
    return 'partial';
  };

  const handleSubmit = async () => {
    if (!projectId) return;
    try {
      const inspection = await createInspection.mutateAsync({
        inspection_type: selectedType,
        inspection_date: header.inspection_date,
        inspector_name: header.inspector_name,
        weather_conditions: header.weather_conditions,
        temperature: header.temperature,
        wind_conditions: header.wind_conditions,
        workers_on_site: header.workers_on_site ? parseInt(header.workers_on_site, 10) : 0,
        items: items
          .filter((i) => i.status !== 'pending')
          .map((i) => ({
            item_id: i.item_id,
            category: i.category,
            description: i.description,
            status: i.status as 'pass' | 'fail' | 'na',
            notes: i.notes,
            photo_url: i.photo_url,
          })),
        overall_notes: overallNotes,
        corrective_actions_needed: correctiveActions,
        overall_status: overallStatus(),
      });
      navigate(ROUTES.INSPECTION_DETAIL(projectId, inspection.id));
    } catch {
      // Error handled by mutation
    }
  };

  // Step 1: Type selection
  if (step === 'type') {
    return (
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(projectId ? ROUTES.PROJECT_DETAIL(projectId) : ROUTES.PROJECTS)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">New Inspection</h1>
            <p className="text-sm text-muted-foreground">
              {project?.name || 'Select inspection type'}
            </p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {INSPECTION_TYPES.map((type) => {
            const IconComponent = ICON_MAP[type.icon] || ClipboardCheck;
            return (
              <Card
                key={type.id}
                className="cursor-pointer transition-all hover:shadow-md active:scale-[0.98]"
                onClick={() => handleSelectType(type.id)}
              >
                <CardContent className="flex items-center gap-4 py-5">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--machine-wash)]">
                    <IconComponent className="h-6 w-6 text-primary" />
                  </div>
                  <span className="text-sm font-semibold text-foreground">{type.name}</span>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    );
  }

  // Step 2: Header info
  if (step === 'header') {
    return (
      <div className="mx-auto max-w-lg">
        <div className="mb-6 flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => setStep('type')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-xl font-bold text-foreground">Inspection Details</h1>
            <p className="text-sm text-muted-foreground">
              {INSPECTION_TYPES.find((t) => t.id === selectedType)?.name}
            </p>
          </div>
        </div>

        <Card>
          <CardContent className="space-y-4 pt-6">
            <div className="space-y-2">
              <Label htmlFor="inspection_date">
                Date <span className="text-[var(--fail)]">*</span>
              </Label>
              <Input
                id="inspection_date"
                type="date"
                value={header.inspection_date}
                onChange={(e) => handleHeaderChange('inspection_date', e.target.value)}
                className="h-12 text-base"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="inspector_name">
                Inspector Name <span className="text-[var(--fail)]">*</span>
              </Label>
              <Input
                id="inspector_name"
                placeholder="Your name"
                value={header.inspector_name}
                onChange={(e) => handleHeaderChange('inspector_name', e.target.value)}
                className="h-12 text-base"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="weather_conditions">Weather</Label>
                <Input
                  id="weather_conditions"
                  placeholder="Sunny, Cloudy..."
                  value={header.weather_conditions}
                  onChange={(e) => handleHeaderChange('weather_conditions', e.target.value)}
                  className="h-12 text-base"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="temperature">Temperature</Label>
                <Input
                  id="temperature"
                  placeholder="72F"
                  value={header.temperature}
                  onChange={(e) => handleHeaderChange('temperature', e.target.value)}
                  className="h-12 text-base"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="wind_conditions">Wind</Label>
                <Input
                  id="wind_conditions"
                  placeholder="Calm, Light..."
                  value={header.wind_conditions}
                  onChange={(e) => handleHeaderChange('wind_conditions', e.target.value)}
                  className="h-12 text-base"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="workers_on_site">Workers on Site</Label>
                <Input
                  id="workers_on_site"
                  type="number"
                  placeholder="0"
                  value={header.workers_on_site}
                  onChange={(e) => handleHeaderChange('workers_on_site', e.target.value)}
                  className="h-12 text-base"
                />
              </div>
            </div>

            <Separator />

            <Button
              className="h-12 w-full bg-primary text-base hover:bg-[var(--machine-dark)]"
              disabled={!isHeaderValid}
              onClick={() => setStep('checklist')}
            >
              Start Checklist
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Step 3: Checklist
  if (step === 'checklist') {
    if (isTemplateLoading || items.length === 0) {
      return (
        <div className="mx-auto flex max-w-lg flex-col items-center gap-3 py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading checklist...</p>
        </div>
      );
    }

    return (
      <div className="mx-auto max-w-lg pb-24">
        <div className="mb-4 flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => setStep('header')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-lg font-bold text-foreground">Inspection Checklist</h1>
            <p className="text-xs text-muted-foreground">
              {completedCount} of {items.length} items completed
              {failedCount > 0 && (
                <span className="text-[var(--fail)]"> — {failedCount} failed</span>
              )}
            </p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-6 h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all duration-300"
            style={{ width: `${items.length > 0 ? (completedCount / items.length) * 100 : 0}%` }}
          />
        </div>

        <div className="space-y-6">
          {categories.map((cat) => (
            <div key={cat.name}>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {cat.name}
              </h3>
              <div className="space-y-2">
                {cat.items.map((item) => (
                  <div
                    key={item.item_id}
                    className={cn(
                      'rounded-lg border p-3 transition-colors',
                      item.status === 'pass' && 'border-[var(--pass)] bg-[var(--pass-bg)]/50',
                      item.status === 'fail' && 'border-[var(--fail)] bg-[var(--fail-bg)]/50',
                      item.status === 'na' && 'border-border bg-muted/50',
                      item.status === 'pending' && 'border-border bg-white'
                    )}
                  >
                    <p className="mb-3 text-sm font-medium text-[var(--concrete-600)]">
                      {item.description}
                    </p>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleItemStatus(item.item_id, 'pass')}
                        className={cn(
                          'flex h-12 flex-1 items-center justify-center gap-2 rounded-lg border-2 text-sm font-medium transition-all active:scale-95',
                          item.status === 'pass'
                            ? 'border-[var(--pass)] bg-[var(--pass)] text-white'
                            : 'border-border text-muted-foreground hover:border-[var(--pass)] hover:bg-[var(--pass-bg)]'
                        )}
                      >
                        <Check className="h-5 w-5" />
                        Pass
                      </button>
                      <button
                        type="button"
                        onClick={() => handleItemStatus(item.item_id, 'fail')}
                        className={cn(
                          'flex h-12 flex-1 items-center justify-center gap-2 rounded-lg border-2 text-sm font-medium transition-all active:scale-95',
                          item.status === 'fail'
                            ? 'border-[var(--fail)] bg-[var(--fail)] text-white'
                            : 'border-border text-muted-foreground hover:border-[var(--fail)] hover:bg-[var(--fail-bg)]'
                        )}
                      >
                        <X className="h-5 w-5" />
                        Fail
                      </button>
                      <button
                        type="button"
                        onClick={() => handleItemStatus(item.item_id, 'na')}
                        className={cn(
                          'flex h-12 w-16 shrink-0 items-center justify-center gap-1 rounded-lg border-2 text-sm font-medium transition-all active:scale-95',
                          item.status === 'na'
                            ? 'border-muted-foreground bg-muted-foreground text-white'
                            : 'border-border text-muted-foreground hover:border-border hover:bg-muted'
                        )}
                      >
                        <Minus className="h-4 w-4" />
                        N/A
                      </button>
                    </div>

                    {/* Fail notes expansion */}
                    {item.status === 'fail' && (
                      <div className="mt-3 space-y-2">
                        <Textarea
                          placeholder="Describe the issue found..."
                          value={item.notes}
                          onChange={(e) => handleItemNotes(item.item_id, e.target.value)}
                          rows={2}
                          className="text-sm"
                          autoFocus={expandedFail === item.item_id}
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-10 text-xs"
                          disabled
                        >
                          <Camera className="mr-1.5 h-4 w-4" />
                          Add Photo (Coming Soon)
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Fixed bottom bar */}
        <div className="fixed bottom-0 left-0 right-0 border-t border-border bg-white p-4 lg:left-64">
          <div className="mx-auto max-w-lg">
            <Button
              className="h-12 w-full bg-primary text-base hover:bg-[var(--machine-dark)]"
              disabled={!allComplete}
              onClick={() => setStep('summary')}
            >
              {allComplete ? (
                <>
                  Review & Submit
                  <ArrowRight className="ml-2 h-5 w-5" />
                </>
              ) : (
                `Complete all items (${completedCount}/${items.length})`
              )}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Step 4: Summary
  return (
    <div className="mx-auto max-w-lg pb-8">
      <div className="mb-6 flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => setStep('checklist')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-xl font-bold text-foreground">Review & Submit</h1>
          <p className="text-sm text-muted-foreground">Final review before submitting</p>
        </div>
      </div>

      {/* Summary stats */}
      <div className="mb-6 grid grid-cols-3 gap-3">
        <Card>
          <CardContent className="flex flex-col items-center py-4">
            <Check className="h-6 w-6 text-[var(--pass)]" />
            <p className="mt-1 text-xl font-bold text-foreground">
              {items.filter((i) => i.status === 'pass').length}
            </p>
            <p className="text-xs text-muted-foreground">Passed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-col items-center py-4">
            <X className="h-6 w-6 text-[var(--fail)]" />
            <p className="mt-1 text-xl font-bold text-foreground">{failedCount}</p>
            <p className="text-xs text-muted-foreground">Failed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-col items-center py-4">
            <Minus className="h-6 w-6 text-muted-foreground" />
            <p className="mt-1 text-xl font-bold text-foreground">
              {items.filter((i) => i.status === 'na').length}
            </p>
            <p className="text-xs text-muted-foreground">N/A</p>
          </CardContent>
        </Card>
      </div>

      {/* Failed items highlight */}
      {failedCount > 0 && (
        <Card className="mb-6 border-[var(--fail)] bg-[var(--fail-bg)]/50">
          <CardContent className="pt-4">
            <h3 className="mb-2 text-sm font-semibold text-[var(--fail)]">Failed Items</h3>
            <div className="space-y-2">
              {items
                .filter((i) => i.status === 'fail')
                .map((item) => (
                  <div key={item.item_id} className="rounded-md bg-white p-2">
                    <p className="text-sm font-medium text-[var(--concrete-600)]">{item.description}</p>
                    {item.notes && (
                      <p className="mt-1 text-xs text-muted-foreground">{item.notes}</p>
                    )}
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="space-y-4 pt-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="overall_notes">Overall Notes</Label>
              <VoiceRecorder
                compact
                placeholder="Dictate notes"
                onTranscript={(text) =>
                  setOverallNotes((prev) => (prev ? `${prev}\n${text}` : text))
                }
              />
            </div>
            <Textarea
              id="overall_notes"
              placeholder="General observations about site conditions... or tap the mic to dictate"
              value={overallNotes}
              onChange={(e) => setOverallNotes(e.target.value)}
              rows={3}
              className="text-sm"
            />
          </div>

          {failedCount > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="corrective_actions">Corrective Actions Needed</Label>
                <VoiceRecorder
                  compact
                  placeholder="Dictate actions"
                  onTranscript={(text) =>
                    setCorrectiveActions((prev) => (prev ? `${prev}\n${text}` : text))
                  }
                />
              </div>
              <Textarea
                id="corrective_actions"
                placeholder="Describe required corrective actions... or tap the mic to dictate"
                value={correctiveActions}
                onChange={(e) => setCorrectiveActions(e.target.value)}
                rows={3}
                className="text-sm"
              />
            </div>
          )}

          <Separator />

          <Button
            className="h-12 w-full bg-primary text-base hover:bg-[var(--machine-dark)]"
            disabled={createInspection.isPending}
            onClick={handleSubmit}
          >
            {createInspection.isPending ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="mr-2 h-5 w-5" />
                Submit Inspection
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
