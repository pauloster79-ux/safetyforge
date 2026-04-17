import { useState } from 'react';
import {
  Plus,
  Loader2,
  AlertTriangle,
  Check,
  X,
  Minus,
  Droplets,
  Activity,
  FileText,
  ArrowLeft,
  Send,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import {
  useEnvironmentalPrograms,
  useCreateEnvironmentalProgram,
  useExposureRecords,
  useCreateExposureRecord,
  useSwpppInspections,
  useCreateSwpppInspection,
} from '@/hooks/useEnvironmental';
import {
  ENVIRONMENTAL_PROGRAMS,
  EXPOSURE_LIMITS,
  SWPPP_BMP_ITEMS,
} from '@/lib/constants';
import type { ExposureRecord } from '@/lib/constants';
import { cn } from '@/lib/utils';

function ProgramStatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    active: { label: 'Active', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    needs_review: { label: 'Needs Review', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
    expired: { label: 'Expired', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
  };
  const { label, className } = config[status] || config.active;
  return <Badge className={className}>{label}</Badge>;
}

function ExposureStatusIcon({ record }: { record: ExposureRecord }) {
  if (record.exceeds_pel) {
    return <X className="h-4 w-4 text-[var(--fail)]" />;
  }
  if (record.exceeds_action_level) {
    return <AlertTriangle className="h-4 w-4 text-[var(--warn)]" />;
  }
  return <Check className="h-4 w-4 text-[var(--pass)]" />;
}

function ExposureBar({ value, actionLevel, pel }: { value: number; actionLevel: number; pel: number }) {
  const maxVal = Math.max(pel * 1.3, value * 1.1);
  const valuePct = Math.min((value / maxVal) * 100, 100);
  const actionPct = (actionLevel / maxVal) * 100;
  const pelPct = (pel / maxVal) * 100;

  let barColor = 'bg-[var(--pass)]';
  if (value > pel) barColor = 'bg-[var(--fail)]';
  else if (value > actionLevel) barColor = 'bg-[var(--warn)]';

  return (
    <div className="relative h-3 w-full rounded-full bg-muted">
      <div
        className={cn('absolute left-0 top-0 h-full rounded-full transition-all', barColor)}
        style={{ width: `${valuePct}%` }}
      />
      <div
        className="absolute top-0 h-full w-px bg-[var(--warn)]"
        style={{ left: `${actionPct}%` }}
        title={`Action Level: ${actionLevel}`}
      />
      <div
        className="absolute top-0 h-full w-px bg-[var(--fail)]"
        style={{ left: `${pelPct}%` }}
        title={`PEL: ${pel}`}
      />
    </div>
  );
}

function SwpppStatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    pass: { label: 'Pass', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    fail: { label: 'Fail', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
    partial: { label: 'Partial', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
  };
  const { label, className } = config[status] || config.pass;
  return <Badge className={className}>{label}</Badge>;
}

// ---- Tab: Programs ----

function ProgramsTab() {
  const { data: programs, isLoading } = useEnvironmentalPrograms();
  const createProgram = useCreateEnvironmentalProgram();

  const handleGenerate = (programId: string) => {
    const prog = ENVIRONMENTAL_PROGRAMS.find(p => p.id === programId);
    if (!prog) return;
    createProgram.mutate({
      program_type: prog.id,
      title: prog.name,
      content: { generated: true, standard: prog.standard },
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Manage environmental compliance programs required for your projects.
      </p>

      {/* Existing programs */}
      {programs && programs.length > 0 && (
        <div className="space-y-3">
          {programs.map((prog) => {
            const progDef = ENVIRONMENTAL_PROGRAMS.find(p => p.id === prog.program_type);
            return (
              <Card key={prog.id}>
                <CardContent className="flex items-center gap-4 py-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--pass-bg)]">
                    <FileText className="h-5 w-5 text-[var(--pass)]" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-foreground">{prog.title}</p>
                      <ProgramStatusBadge status={prog.status} />
                    </div>
                    <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                      {progDef && <span>{progDef.standard}</span>}
                      {prog.next_review_due && (
                        <span>Next review: {prog.next_review_due}</span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Generate new programs */}
      <Separator />
      <h3 className="text-sm font-semibold text-muted-foreground">Available Programs</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {ENVIRONMENTAL_PROGRAMS.map((prog) => {
          const exists = programs?.some(p => p.program_type === prog.id);
          return (
            <Card key={prog.id} className={cn(exists && 'opacity-50')}>
              <CardContent className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">{prog.name}</p>
                  <p className="text-xs text-muted-foreground">{prog.standard}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={exists || createProgram.isPending}
                  onClick={() => handleGenerate(prog.id)}
                >
                  {exists ? 'Active' : 'Generate'}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

// ---- Tab: Exposure Monitoring ----

function ExposureTab() {
  const { data: records, isLoading } = useExposureRecords();
  const createRecord = useCreateExposureRecord();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    monitoring_type: 'silica',
    monitoring_date: new Date().toISOString().split('T')[0],
    location: '',
    worker_name: '',
    sample_type: 'personal' as 'personal' | 'area',
    duration_hours: '8',
    result_value: '',
    controls_in_place: '',
    project_id: '',
  });

  const handleSubmit = () => {
    const limits = EXPOSURE_LIMITS[form.monitoring_type as keyof typeof EXPOSURE_LIMITS];
    if (!limits) return;
    createRecord.mutate({
      ...form,
      duration_hours: parseFloat(form.duration_hours) || 8,
      result_value: parseFloat(form.result_value) || 0,
      result_unit: limits.unit,
      action_level: limits.action_level,
      pel: limits.pel,
    }, {
      onSuccess: () => {
        setShowForm(false);
        setForm(prev => ({ ...prev, location: '', worker_name: '', result_value: '', controls_in_place: '' }));
      },
    });
  };

  if (showForm) {
    const limits = EXPOSURE_LIMITS[form.monitoring_type as keyof typeof EXPOSURE_LIMITS];
    return (
      <div className="mx-auto max-w-lg">
        <div className="mb-6 flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => setShowForm(false)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h2 className="text-lg font-bold text-foreground">Add Exposure Record</h2>
        </div>
        <Card>
          <CardContent className="space-y-4 pt-6">
            <div className="space-y-2">
              <Label>Monitoring Type</Label>
              <Select value={form.monitoring_type} onValueChange={v => setForm(prev => ({ ...prev, monitoring_type: v || 'silica' }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {Object.entries(EXPOSURE_LIMITS).map(([key, val]) => (
                    <SelectItem key={key} value={key}>
                      {key.charAt(0).toUpperCase() + key.slice(1)} ({val.unit})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Date</Label>
                <Input type="date" value={form.monitoring_date} onChange={e => setForm(prev => ({ ...prev, monitoring_date: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>Sample Type</Label>
                <Select value={form.sample_type} onValueChange={v => setForm(prev => ({ ...prev, sample_type: v as 'personal' | 'area' }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="personal">Personal</SelectItem>
                    <SelectItem value="area">Area</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Worker Name</Label>
              <Input value={form.worker_name} onChange={e => setForm(prev => ({ ...prev, worker_name: e.target.value }))} placeholder="Worker name" />
            </div>
            <div className="space-y-2">
              <Label>Location</Label>
              <Input value={form.location} onChange={e => setForm(prev => ({ ...prev, location: e.target.value }))} placeholder="Monitoring location" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Result Value ({limits?.unit})</Label>
                <Input type="number" step="0.1" value={form.result_value} onChange={e => setForm(prev => ({ ...prev, result_value: e.target.value }))} placeholder="0" />
              </div>
              <div className="space-y-2">
                <Label>Duration (hours)</Label>
                <Input type="number" value={form.duration_hours} onChange={e => setForm(prev => ({ ...prev, duration_hours: e.target.value }))} />
              </div>
            </div>
            {limits && (
              <div className="rounded-lg border border-border bg-muted/50 p-3 text-xs text-muted-foreground">
                <p>Action Level: {limits.action_level} {limits.unit} | PEL: {limits.pel} {limits.unit}</p>
              </div>
            )}
            <div className="space-y-2">
              <Label>Controls in Place</Label>
              <Textarea value={form.controls_in_place} onChange={e => setForm(prev => ({ ...prev, controls_in_place: e.target.value }))} placeholder="Engineering and administrative controls..." rows={2} />
            </div>
            <Separator />
            <Button
              className="h-12 w-full bg-primary hover:bg-[var(--machine-dark)]"
              disabled={!form.worker_name || !form.result_value || createRecord.isPending}
              onClick={handleSubmit}
            >
              {createRecord.isPending ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <Send className="mr-2 h-5 w-5" />}
              Save Record
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Track exposure monitoring results against OSHA action levels and PELs.
        </p>
        <Button className="bg-primary hover:bg-[var(--machine-dark)]" onClick={() => setShowForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Record
        </Button>
      </div>

      {records && records.length > 0 ? (
        <div className="space-y-3">
          {/* Header row */}
          <div className="hidden items-center gap-3 px-4 text-xs font-medium uppercase tracking-wider text-muted-foreground sm:flex">
            <span className="w-20">Date</span>
            <span className="w-16">Type</span>
            <span className="flex-1">Worker / Location</span>
            <span className="w-32">Result</span>
            <span className="w-40">Level</span>
            <span className="w-8" />
          </div>
          {records.map((record) => (
            <Card key={record.id}>
              <CardContent className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:gap-3">
                <span className="w-20 font-mono text-xs text-muted-foreground">{record.monitoring_date}</span>
                <span className="w-16">
                  <Badge variant="secondary" className="text-xs capitalize">{record.monitoring_type}</Badge>
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground">{record.worker_name}</p>
                  <p className="text-xs text-muted-foreground">{record.location}</p>
                </div>
                <span className="w-32 font-mono text-sm font-medium">
                  {record.result_value} {record.result_unit}
                </span>
                <div className="w-40">
                  <ExposureBar value={record.result_value} actionLevel={record.action_level} pel={record.pel} />
                  <div className="mt-0.5 flex justify-between text-[10px] text-muted-foreground">
                    <span>AL: {record.action_level}</span>
                    <span>PEL: {record.pel}</span>
                  </div>
                </div>
                <div className="w-8 flex items-center justify-center">
                  <ExposureStatusIcon record={record} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <Activity className="h-16 w-16 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium text-muted-foreground">No exposure records</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Start logging exposure monitoring results
          </p>
          <Button className="mt-4 bg-primary hover:bg-[var(--machine-dark)]" onClick={() => setShowForm(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Record
          </Button>
        </div>
      )}
    </div>
  );
}

// ---- Tab: SWPPP ----

function SwpppTab() {
  const { data: inspections, isLoading } = useSwpppInspections();
  const createInspection = useCreateSwpppInspection();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    inspection_date: new Date().toISOString().split('T')[0],
    inspector_name: '',
    inspection_type: 'Weekly routine',
    precipitation_last_24h: '0',
    corrective_actions: '',
    project_id: '',
  });
  const [bmpItems, setBmpItems] = useState(
    SWPPP_BMP_ITEMS.map(item => ({ name: item.name, status: 'pending' as string, notes: '' }))
  );

  const handleBmpStatus = (index: number, status: string) => {
    setBmpItems(prev => prev.map((item, i) => i === index ? { ...item, status } : item));
  };

  const handleBmpNotes = (index: number, notes: string) => {
    setBmpItems(prev => prev.map((item, i) => i === index ? { ...item, notes } : item));
  };

  const allBmpComplete = bmpItems.every(item => item.status !== 'pending');

  const handleSubmit = () => {
    createInspection.mutate({
      ...form,
      precipitation_last_24h: parseFloat(form.precipitation_last_24h) || 0,
      bmp_items: bmpItems.filter(i => i.status !== 'pending'),
    }, {
      onSuccess: () => {
        setShowForm(false);
        setForm(prev => ({ ...prev, inspector_name: '', corrective_actions: '', precipitation_last_24h: '0' }));
        setBmpItems(SWPPP_BMP_ITEMS.map(item => ({ name: item.name, status: 'pending', notes: '' })));
      },
    });
  };

  if (showForm) {
    return (
      <div className="mx-auto max-w-lg pb-24">
        <div className="mb-6 flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => setShowForm(false)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h2 className="text-lg font-bold text-foreground">New SWPPP Inspection</h2>
        </div>

        <Card className="mb-4">
          <CardContent className="space-y-4 pt-6">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Date</Label>
                <Input type="date" value={form.inspection_date} onChange={e => setForm(prev => ({ ...prev, inspection_date: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>Precip. Last 24h (in)</Label>
                <Input type="number" step="0.1" value={form.precipitation_last_24h} onChange={e => setForm(prev => ({ ...prev, precipitation_last_24h: e.target.value }))} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Inspector Name</Label>
              <Input value={form.inspector_name} onChange={e => setForm(prev => ({ ...prev, inspector_name: e.target.value }))} placeholder="Your name" />
            </div>
            <div className="space-y-2">
              <Label>Inspection Type</Label>
              <Select value={form.inspection_type} onValueChange={v => setForm(prev => ({ ...prev, inspection_type: v || 'Weekly routine' }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Weekly routine">Weekly Routine</SelectItem>
                  <SelectItem value="Post-rainfall">Post-Rainfall (0.5in+)</SelectItem>
                  <SelectItem value="Quarterly">Quarterly</SelectItem>
                  <SelectItem value="Pre-storm">Pre-Storm</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* BMP checklist */}
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          BMP Inspection Items
        </h3>
        <div className="mb-4 h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all duration-300"
            style={{ width: `${bmpItems.length > 0 ? (bmpItems.filter(i => i.status !== 'pending').length / bmpItems.length) * 100 : 0}%` }}
          />
        </div>

        <div className="space-y-2">
          {bmpItems.map((item, index) => (
            <div
              key={item.name}
              className={cn(
                'rounded-lg border p-3 transition-colors',
                item.status === 'pass' && 'border-[var(--pass)] bg-[var(--pass-bg)]/50',
                item.status === 'fail' && 'border-[var(--fail)] bg-[var(--fail-bg)]/50',
                item.status === 'na' && 'border-border bg-muted/50',
                item.status === 'pending' && 'border-border bg-white',
              )}
            >
              <p className="mb-3 text-sm font-medium text-[var(--concrete-600)]">{item.name}</p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleBmpStatus(index, 'pass')}
                  className={cn(
                    'flex h-10 flex-1 items-center justify-center gap-2 rounded-lg border-2 text-sm font-medium transition-all active:scale-95',
                    item.status === 'pass'
                      ? 'border-[var(--pass)] bg-[var(--pass)] text-white'
                      : 'border-border text-muted-foreground hover:border-[var(--pass)] hover:bg-[var(--pass-bg)]'
                  )}
                >
                  <Check className="h-4 w-4" />
                  Pass
                </button>
                <button
                  type="button"
                  onClick={() => handleBmpStatus(index, 'fail')}
                  className={cn(
                    'flex h-10 flex-1 items-center justify-center gap-2 rounded-lg border-2 text-sm font-medium transition-all active:scale-95',
                    item.status === 'fail'
                      ? 'border-[var(--fail)] bg-[var(--fail)] text-white'
                      : 'border-border text-muted-foreground hover:border-[var(--fail)] hover:bg-[var(--fail-bg)]'
                  )}
                >
                  <X className="h-4 w-4" />
                  Fail
                </button>
                <button
                  type="button"
                  onClick={() => handleBmpStatus(index, 'na')}
                  className={cn(
                    'flex h-10 w-14 shrink-0 items-center justify-center gap-1 rounded-lg border-2 text-sm font-medium transition-all active:scale-95',
                    item.status === 'na'
                      ? 'border-muted-foreground bg-muted-foreground text-white'
                      : 'border-border text-muted-foreground hover:border-border hover:bg-muted'
                  )}
                >
                  <Minus className="h-4 w-4" />
                  N/A
                </button>
              </div>
              {item.status === 'fail' && (
                <div className="mt-2">
                  <Textarea
                    placeholder="Describe the issue..."
                    value={item.notes}
                    onChange={e => handleBmpNotes(index, e.target.value)}
                    rows={2}
                    className="text-sm"
                  />
                </div>
              )}
            </div>
          ))}
        </div>

        {bmpItems.some(i => i.status === 'fail') && (
          <Card className="mt-4">
            <CardContent className="space-y-2 pt-4">
              <Label>Corrective Actions</Label>
              <Textarea
                value={form.corrective_actions}
                onChange={e => setForm(prev => ({ ...prev, corrective_actions: e.target.value }))}
                placeholder="Describe required corrective actions..."
                rows={3}
              />
            </CardContent>
          </Card>
        )}

        <div className="fixed bottom-0 left-0 right-0 border-t border-border bg-white p-4 lg:left-64">
          <div className="mx-auto max-w-lg">
            <Button
              className="h-12 w-full bg-primary text-base hover:bg-[var(--machine-dark)]"
              disabled={!allBmpComplete || !form.inspector_name || createInspection.isPending}
              onClick={handleSubmit}
            >
              {allBmpComplete ? (
                <>
                  <Send className="mr-2 h-5 w-5" />
                  Submit SWPPP Inspection
                </>
              ) : (
                `Complete all BMP items (${bmpItems.filter(i => i.status !== 'pending').length}/${bmpItems.length})`
              )}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Stormwater Pollution Prevention Plan inspection log.
        </p>
        <Button className="bg-primary hover:bg-[var(--machine-dark)]" onClick={() => setShowForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New SWPPP Inspection
        </Button>
      </div>

      {inspections && inspections.length > 0 ? (
        <div className="space-y-3">
          {inspections.map((insp) => {
            const passCount = (insp.bmp_items || []).filter(i => i.status === 'pass').length;
            const failCount = (insp.bmp_items || []).filter(i => i.status === 'fail').length;
            return (
              <Card key={insp.id}>
                <CardContent className="flex items-center gap-4 py-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--info-bg)]">
                    <Droplets className="h-5 w-5 text-[var(--info)]" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-foreground">{insp.inspection_type}</p>
                      <SwpppStatusBadge status={insp.overall_status} />
                    </div>
                    <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{insp.inspection_date}</span>
                      <span>{insp.inspector_name}</span>
                      <span>Precip: {insp.precipitation_last_24h}in</span>
                    </div>
                  </div>
                  <div className="text-right text-xs text-muted-foreground">
                    <p className="text-[var(--pass)]">{passCount} pass</p>
                    {failCount > 0 && <p className="text-[var(--fail)]">{failCount} fail</p>}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <Droplets className="h-16 w-16 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium text-muted-foreground">No SWPPP inspections</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Start logging stormwater inspections
          </p>
          <Button className="mt-4 bg-primary hover:bg-[var(--machine-dark)]" onClick={() => setShowForm(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New SWPPP Inspection
          </Button>
        </div>
      )}
    </div>
  );
}

// ---- Main Page ----

export function EnvironmentalPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Environmental Compliance</h1>
        <p className="text-sm text-muted-foreground">
          Manage environmental programs, exposure monitoring, and stormwater compliance
        </p>
      </div>

      <Tabs defaultValue="programs">
        <TabsList>
          <TabsTrigger value="programs" className="gap-2">
            <FileText className="h-4 w-4" />
            Programs
          </TabsTrigger>
          <TabsTrigger value="exposure" className="gap-2">
            <Activity className="h-4 w-4" />
            Exposure Monitoring
          </TabsTrigger>
          <TabsTrigger value="swppp" className="gap-2">
            <Droplets className="h-4 w-4" />
            SWPPP
          </TabsTrigger>
        </TabsList>

        <TabsContent value="programs" className="mt-6">
          <ProgramsTab />
        </TabsContent>
        <TabsContent value="exposure" className="mt-6">
          <ExposureTab />
        </TabsContent>
        <TabsContent value="swppp" className="mt-6">
          <SwpppTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
