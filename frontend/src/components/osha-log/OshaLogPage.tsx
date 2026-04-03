import { useState } from 'react';
import {
  ClipboardList,
  Plus,
  FileText,
  BarChart3,
  Printer,
  ShieldCheck,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { format } from 'date-fns';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useOshaLogEntries, useOsha300Summary, useCreateOshaLogEntry, useUpdateOshaLogEntry, useDeleteOshaLogEntry, useCertifySummary } from '@/hooks/useOshaLog';
import { useCompany } from '@/hooks/useCompany';
import type { OshaLogEntry } from '@/lib/constants';

const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 5 }, (_, i) => CURRENT_YEAR - i);

const CLASSIFICATION_OPTIONS: { value: OshaLogEntry['classification']; label: string }[] = [
  { value: 'death', label: 'Death' },
  { value: 'days_away_from_work', label: 'Days Away from Work' },
  { value: 'job_transfer_or_restriction', label: 'Job Transfer or Restriction' },
  { value: 'other_recordable', label: 'Other Recordable' },
];

const INJURY_TYPE_OPTIONS: { value: OshaLogEntry['injury_type']; label: string }[] = [
  { value: 'injury', label: 'Injury' },
  { value: 'skin_disorder', label: 'Skin Disorder' },
  { value: 'respiratory', label: 'Respiratory Condition' },
  { value: 'poisoning', label: 'Poisoning' },
  { value: 'hearing_loss', label: 'Hearing Loss' },
  { value: 'other_illness', label: 'Other Illness' },
];

const CLASSIFICATION_BADGE_STYLES: Record<OshaLogEntry['classification'], string> = {
  death: 'bg-[var(--concrete-900)] text-white hover:bg-[var(--concrete-900)]',
  days_away_from_work: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]',
  job_transfer_or_restriction: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]',
  other_recordable: 'bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)]',
};

const CLASSIFICATION_LABELS: Record<OshaLogEntry['classification'], string> = {
  death: 'Death',
  days_away_from_work: 'Days Away',
  job_transfer_or_restriction: 'Restricted',
  other_recordable: 'Other Recordable',
};

const INDUSTRY_AVG_TRIR = 3.0;
const INDUSTRY_AVG_DART = 2.0;

interface EntryFormData {
  employee_name: string;
  job_title: string;
  date_of_injury: string;
  where_event_occurred: string;
  description: string;
  classification: OshaLogEntry['classification'];
  injury_type: OshaLogEntry['injury_type'];
  days_away_from_work: number;
  days_of_restricted_work: number;
  died: boolean;
  privacy_case: boolean;
}

const EMPTY_FORM: EntryFormData = {
  employee_name: '',
  job_title: '',
  date_of_injury: new Date().toISOString().split('T')[0],
  where_event_occurred: '',
  description: '',
  classification: 'other_recordable',
  injury_type: 'injury',
  days_away_from_work: 0,
  days_of_restricted_work: 0,
  died: false,
  privacy_case: false,
};

function getRateColor(rate: number, avg: number): string {
  if (rate <= avg) return 'text-[var(--pass)]';
  if (rate <= avg * 1.67) return 'text-[var(--warn)]';
  return 'text-[var(--fail)]';
}

function getRateBgColor(rate: number, avg: number): string {
  if (rate <= avg) return 'bg-[var(--pass-bg)]';
  if (rate <= avg * 1.67) return 'bg-[var(--warn-bg)]';
  return 'bg-[var(--fail-bg)]';
}

function isPostingPeriod(): boolean {
  const now = new Date();
  const month = now.getMonth(); // 0-indexed: Jan=0
  const day = now.getDate();
  return (month === 1 && day >= 1) || (month === 2) || (month === 3 && day <= 30);
}

export function OshaLogPage() {
  const [selectedYear, setSelectedYear] = useState(CURRENT_YEAR);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<OshaLogEntry | null>(null);
  const [formData, setFormData] = useState<EntryFormData>(EMPTY_FORM);
  const [certifyName, setCertifyName] = useState('');
  const [showCertifyDialog, setShowCertifyDialog] = useState(false);

  const { data: entries, isLoading: entriesLoading } = useOshaLogEntries(selectedYear);
  const { data: summary } = useOsha300Summary(selectedYear);
  const { data: company } = useCompany();
  const createEntry = useCreateOshaLogEntry();
  const updateEntry = useUpdateOshaLogEntry();
  const deleteEntry = useDeleteOshaLogEntry();
  const certifySummary = useCertifySummary();

  const handleOpenAdd = () => {
    setEditingEntry(null);
    setFormData(EMPTY_FORM);
    setDialogOpen(true);
  };

  const handleOpenEdit = (entry: OshaLogEntry) => {
    setEditingEntry(entry);
    setFormData({
      employee_name: entry.employee_name,
      job_title: entry.job_title,
      date_of_injury: entry.date_of_injury,
      where_event_occurred: entry.where_event_occurred,
      description: entry.description,
      classification: entry.classification,
      injury_type: entry.injury_type,
      days_away_from_work: entry.days_away_from_work,
      days_of_restricted_work: entry.days_of_restricted_work,
      died: entry.died,
      privacy_case: entry.privacy_case,
    });
    setDialogOpen(true);
  };

  const handleSave = () => {
    const payload = {
      ...formData,
      employee_name: formData.privacy_case ? 'Privacy Case' : formData.employee_name,
    };

    if (editingEntry) {
      updateEntry.mutate({ id: editingEntry.id, ...payload }, {
        onSuccess: () => setDialogOpen(false),
      });
    } else {
      createEntry.mutate(payload, {
        onSuccess: () => setDialogOpen(false),
      });
    }
  };

  const handleDelete = (id: string) => {
    deleteEntry.mutate(id);
  };

  const handleCertify = () => {
    certifySummary.mutate(
      { certified_by: certifyName, year: selectedYear },
      { onSuccess: () => setShowCertifyDialog(false) }
    );
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
            <ClipboardList className="h-7 w-7 text-primary" />
            OSHA 300 Log
          </h1>
          <p className="text-sm text-muted-foreground">
            Recordkeeping for workplace injuries and illnesses
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={String(selectedYear)} onValueChange={(v) => setSelectedYear(Number(v))}>
            <SelectTrigger className="w-28">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {YEAR_OPTIONS.map((y) => (
                <SelectItem key={y} value={String(y)}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Posting Reminder */}
      {isPostingPeriod() && summary && !summary.posted && (
        <Alert className="border-[var(--warn)] bg-[var(--warn-bg)]">
          <AlertTriangle className="h-4 w-4 text-[var(--warn)]" />
          <AlertTitle className="text-[var(--warn)]">300A Posting Required</AlertTitle>
          <AlertDescription className="text-[var(--warn)]">
            The OSHA 300A Annual Summary must be posted in a visible location from February 1 through April 30.
            Certify and post your {selectedYear - 1} summary to stay compliant.
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="log">
        <TabsList>
          <TabsTrigger value="log">
            <ClipboardList className="mr-1.5 h-4 w-4" />
            300 Log
          </TabsTrigger>
          <TabsTrigger value="summary">
            <FileText className="mr-1.5 h-4 w-4" />
            300A Summary
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="mr-1.5 h-4 w-4" />
            Incidence Rates
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: OSHA 300 Log */}
        <TabsContent value="log">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">
                  Log of Work-Related Injuries and Illnesses — {selectedYear}
                </CardTitle>
                <CardDescription>
                  OSHA Form 300 — {entries?.length ?? 0} recordable {(entries?.length ?? 0) === 1 ? 'case' : 'cases'}
                </CardDescription>
              </div>
              <Button
                className="bg-primary hover:bg-[var(--machine-dark)]"
                onClick={handleOpenAdd}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Entry
              </Button>
            </CardHeader>
            <CardContent>
              {entriesLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="h-12 animate-pulse rounded bg-muted" />
                  ))}
                </div>
              ) : entries && entries.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-16">Case #</TableHead>
                      <TableHead>Employee</TableHead>
                      <TableHead>Job Title</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="hidden lg:table-cell">Location</TableHead>
                      <TableHead>Classification</TableHead>
                      <TableHead className="text-center">Days Away</TableHead>
                      <TableHead className="text-center">Days Restricted</TableHead>
                      <TableHead className="hidden md:table-cell">Type</TableHead>
                      <TableHead className="w-20" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {entries.map((entry) => (
                      <TableRow
                        key={entry.id}
                        className="cursor-pointer"
                        onClick={() => handleOpenEdit(entry)}
                      >
                        <TableCell className="font-medium">{entry.case_number}</TableCell>
                        <TableCell>
                          {entry.privacy_case ? (
                            <span className="italic text-muted-foreground">Privacy Case</span>
                          ) : (
                            entry.employee_name
                          )}
                        </TableCell>
                        <TableCell>{entry.job_title}</TableCell>
                        <TableCell>{format(new Date(entry.date_of_injury), 'MMM d, yyyy')}</TableCell>
                        <TableCell className="hidden max-w-[200px] truncate lg:table-cell">
                          {entry.where_event_occurred}
                        </TableCell>
                        <TableCell>
                          <Badge className={CLASSIFICATION_BADGE_STYLES[entry.classification]}>
                            {CLASSIFICATION_LABELS[entry.classification]}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">{entry.days_away_from_work}</TableCell>
                        <TableCell className="text-center">{entry.days_of_restricted_work}</TableCell>
                        <TableCell className="hidden capitalize md:table-cell">
                          {entry.injury_type.replace('_', ' ')}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-[var(--fail)] hover:text-[var(--fail)]"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(entry.id);
                            }}
                          >
                            Delete
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="flex flex-col items-center py-12 text-center">
                  <ClipboardList className="h-12 w-12 text-muted-foreground" />
                  <p className="mt-3 text-sm font-medium text-muted-foreground">No entries for {selectedYear}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Add recordable injuries and illnesses to your OSHA 300 Log
                  </p>
                  <Button
                    className="mt-4 bg-primary hover:bg-[var(--machine-dark)]"
                    onClick={handleOpenAdd}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add First Entry
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: 300A Summary */}
        <TabsContent value="summary">
          <div className="space-y-6 print:space-y-4">
            {/* Official 300A Header */}
            <Card className="print:border-2 print:border-[var(--concrete-800)]">
              <CardHeader className="text-center">
                <CardTitle className="text-xl">
                  OSHA&apos;s Form 300A — Summary of Work-Related Injuries and Illnesses
                </CardTitle>
                <CardDescription className="text-base">
                  Calendar Year {selectedYear}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Company Info */}
                <div className="rounded-lg border p-4">
                  <h3 className="mb-2 text-sm font-semibold text-muted-foreground uppercase">Establishment Information</h3>
                  <p className="text-lg font-semibold text-foreground">
                    {company?.name || summary?.company_name || 'Company Name'}
                  </p>
                  <p className="text-sm text-muted-foreground">{company?.address || ''}</p>
                </div>

                {/* Totals Grid */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-lg border p-4 text-center">
                    <p className="text-3xl font-bold text-foreground">{summary?.total_deaths ?? 0}</p>
                    <p className="mt-1 text-xs font-medium text-muted-foreground">Total Deaths</p>
                  </div>
                  <div className="rounded-lg border p-4 text-center">
                    <p className="text-3xl font-bold text-[var(--fail)]">{summary?.total_days_away ?? 0}</p>
                    <p className="mt-1 text-xs font-medium text-muted-foreground">Cases with Days Away</p>
                  </div>
                  <div className="rounded-lg border p-4 text-center">
                    <p className="text-3xl font-bold text-[var(--warn)]">{summary?.total_restricted ?? 0}</p>
                    <p className="mt-1 text-xs font-medium text-muted-foreground">Cases with Restriction</p>
                  </div>
                  <div className="rounded-lg border p-4 text-center">
                    <p className="text-3xl font-bold text-[var(--info)]">{summary?.total_other_recordable ?? 0}</p>
                    <p className="mt-1 text-xs font-medium text-muted-foreground">Other Recordable</p>
                  </div>
                </div>

                {/* Days Counts */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border p-4 text-center">
                    <p className="text-3xl font-bold text-foreground">{summary?.total_days_away_count ?? 0}</p>
                    <p className="mt-1 text-xs font-medium text-muted-foreground">Total Days Away from Work</p>
                  </div>
                  <div className="rounded-lg border p-4 text-center">
                    <p className="text-3xl font-bold text-foreground">{summary?.total_restricted_days_count ?? 0}</p>
                    <p className="mt-1 text-xs font-medium text-muted-foreground">Total Days of Restriction/Transfer</p>
                  </div>
                </div>

                <Separator />

                {/* Injury/Illness Type Breakdown */}
                <div>
                  <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase">Injury and Illness Types</h3>
                  <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
                    {[
                      { label: 'Injuries', value: summary?.total_injuries ?? 0 },
                      { label: 'Skin Disorders', value: summary?.total_skin_disorders ?? 0 },
                      { label: 'Respiratory', value: summary?.total_respiratory ?? 0 },
                      { label: 'Poisonings', value: summary?.total_poisonings ?? 0 },
                      { label: 'Hearing Loss', value: summary?.total_hearing_loss ?? 0 },
                      { label: 'Other Illnesses', value: summary?.total_other_illnesses ?? 0 },
                    ].map((item) => (
                      <div key={item.label} className="rounded-lg border p-3 text-center">
                        <p className="text-2xl font-bold text-foreground">{item.value}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{item.label}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <Separator />

                {/* TRIR and DART — Prominent */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className={`rounded-xl border-2 p-6 text-center ${getRateBgColor(summary?.trir ?? 0, INDUSTRY_AVG_TRIR)}`}>
                    <p className="text-xs font-semibold text-muted-foreground uppercase">Total Recordable Incident Rate</p>
                    <p className={`mt-2 text-5xl font-bold ${getRateColor(summary?.trir ?? 0, INDUSTRY_AVG_TRIR)}`}>
                      {summary?.trir?.toFixed(1) ?? '0.0'}
                    </p>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Industry average: ~{INDUSTRY_AVG_TRIR.toFixed(1)}
                    </p>
                    <div className="mt-1 flex items-center justify-center gap-1">
                      {(summary?.trir ?? 0) <= INDUSTRY_AVG_TRIR ? (
                        <>
                          <TrendingDown className="h-4 w-4 text-[var(--pass)]" />
                          <span className="text-xs font-medium text-[var(--pass)]">Below average</span>
                        </>
                      ) : (
                        <>
                          <TrendingUp className="h-4 w-4 text-[var(--fail)]" />
                          <span className="text-xs font-medium text-[var(--fail)]">Above average</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className={`rounded-xl border-2 p-6 text-center ${getRateBgColor(summary?.dart ?? 0, INDUSTRY_AVG_DART)}`}>
                    <p className="text-xs font-semibold text-muted-foreground uppercase">DART Rate</p>
                    <p className={`mt-2 text-5xl font-bold ${getRateColor(summary?.dart ?? 0, INDUSTRY_AVG_DART)}`}>
                      {summary?.dart?.toFixed(1) ?? '0.0'}
                    </p>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Industry average: ~{INDUSTRY_AVG_DART.toFixed(1)}
                    </p>
                    <div className="mt-1 flex items-center justify-center gap-1">
                      {(summary?.dart ?? 0) <= INDUSTRY_AVG_DART ? (
                        <>
                          <TrendingDown className="h-4 w-4 text-[var(--pass)]" />
                          <span className="text-xs font-medium text-[var(--pass)]">Below average</span>
                        </>
                      ) : (
                        <>
                          <TrendingUp className="h-4 w-4 text-[var(--fail)]" />
                          <span className="text-xs font-medium text-[var(--fail)]">Above average</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Employment Info */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border p-4">
                    <p className="text-sm text-muted-foreground">Annual Average Employees</p>
                    <p className="text-2xl font-bold text-foreground">{summary?.annual_average_employees ?? 0}</p>
                  </div>
                  <div className="rounded-lg border p-4">
                    <p className="text-sm text-muted-foreground">Total Hours Worked</p>
                    <p className="text-2xl font-bold text-foreground">
                      {(summary?.total_hours_worked ?? 0).toLocaleString()}
                    </p>
                  </div>
                </div>

                <Separator />

                {/* Certification Status */}
                <div className="rounded-lg border p-4">
                  <h3 className="mb-2 text-sm font-semibold text-muted-foreground uppercase">Certification</h3>
                  {summary?.certified_date ? (
                    <div className="flex items-center gap-3">
                      <ShieldCheck className="h-6 w-6 text-[var(--pass)]" />
                      <div>
                        <p className="font-medium text-[var(--pass)]">
                          Certified by {summary.certified_by} on{' '}
                          {format(new Date(summary.certified_date), 'MMMM d, yyyy')}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          This summary has been verified and is ready for posting.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-6 w-6 text-[var(--warn)]" />
                      <div>
                        <p className="font-medium text-[var(--warn)]">Not yet certified</p>
                        <p className="text-xs text-muted-foreground">
                          A company executive must certify this summary before it can be posted.
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 print:hidden">
                  {!summary?.certified_date && (
                    <Button
                      className="bg-primary hover:bg-[var(--machine-dark)]"
                      onClick={() => setShowCertifyDialog(true)}
                    >
                      <ShieldCheck className="mr-2 h-4 w-4" />
                      Certify Summary
                    </Button>
                  )}
                  <Button variant="outline" onClick={handlePrint}>
                    <Printer className="mr-2 h-4 w-4" />
                    Print 300A
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 3: Incidence Rates (Analytics) */}
        <TabsContent value="analytics">
          <div className="space-y-6">
            {/* Current Year Metrics */}
            <div className="grid gap-4 sm:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">TRIR — Total Recordable Incident Rate</CardTitle>
                  <CardDescription>
                    (Recordable cases x 200,000) / Total hours worked
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className={`rounded-xl p-6 text-center ${getRateBgColor(summary?.trir ?? 0, INDUSTRY_AVG_TRIR)}`}>
                    <p className={`text-6xl font-bold ${getRateColor(summary?.trir ?? 0, INDUSTRY_AVG_TRIR)}`}>
                      {summary?.trir?.toFixed(1) ?? '0.0'}
                    </p>
                    <p className="mt-2 text-sm text-muted-foreground">Your {selectedYear} TRIR</p>
                  </div>
                  <div className="mt-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Your rate</span>
                      <span className="font-medium">{summary?.trir?.toFixed(1) ?? '0.0'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Industry average</span>
                      <span className="font-medium">{INDUSTRY_AVG_TRIR.toFixed(1)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Best-in-class</span>
                      <span className="font-medium">1.0</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">DART Rate</CardTitle>
                  <CardDescription>
                    Days Away, Restricted, or Transferred rate
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className={`rounded-xl p-6 text-center ${getRateBgColor(summary?.dart ?? 0, INDUSTRY_AVG_DART)}`}>
                    <p className={`text-6xl font-bold ${getRateColor(summary?.dart ?? 0, INDUSTRY_AVG_DART)}`}>
                      {summary?.dart?.toFixed(1) ?? '0.0'}
                    </p>
                    <p className="mt-2 text-sm text-muted-foreground">Your {selectedYear} DART</p>
                  </div>
                  <div className="mt-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Your rate</span>
                      <span className="font-medium">{summary?.dart?.toFixed(1) ?? '0.0'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Industry average</span>
                      <span className="font-medium">{INDUSTRY_AVG_DART.toFixed(1)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Best-in-class</span>
                      <span className="font-medium">0.5</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* EMR Impact Explanation */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">EMR Impact</CardTitle>
                <CardDescription>
                  How your incidence rates affect your Experience Modification Rate
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Your TRIR of{' '}
                  <span className={`font-bold ${getRateColor(summary?.trir ?? 0, INDUSTRY_AVG_TRIR)}`}>
                    {summary?.trir?.toFixed(1) ?? '0.0'}
                  </span>{' '}
                  is {(summary?.trir ?? 0) > INDUSTRY_AVG_TRIR ? 'above' : 'at or below'} the
                  industry average of {INDUSTRY_AVG_TRIR.toFixed(1)}.
                </p>
                {(summary?.trir ?? 0) > INDUSTRY_AVG_TRIR && (
                  <div className="rounded-lg border border-[var(--warn)] bg-[var(--warn-bg)] p-4">
                    <p className="text-sm text-[var(--warn)]">
                      A TRIR above the industry average may increase your EMR, resulting in higher
                      workers&apos; compensation premiums. Reducing your TRIR to{' '}
                      {INDUSTRY_AVG_TRIR.toFixed(1)} could save approximately{' '}
                      <span className="font-bold">
                        ${Math.round((((summary?.trir ?? 0) - INDUSTRY_AVG_TRIR) / INDUSTRY_AVG_TRIR) * 15000).toLocaleString()}
                      </span>{' '}
                      in annual premiums based on a typical subcontractor payroll.
                    </p>
                  </div>
                )}
                {(summary?.trir ?? 0) <= INDUSTRY_AVG_TRIR && (
                  <div className="rounded-lg border border-[var(--pass)] bg-[var(--pass-bg)] p-4">
                    <p className="text-sm text-[var(--pass)]">
                      Your TRIR is at or below the industry average. This helps keep your EMR low,
                      which means lower workers&apos; compensation premiums and better competitiveness
                      when bidding on projects.
                    </p>
                  </div>
                )}

                <Separator />

                <div>
                  <h4 className="mb-2 text-sm font-semibold text-[var(--concrete-600)]">What Drives Your Rates</h4>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-lg border p-3 text-center">
                      <p className="text-2xl font-bold text-foreground">
                        {(summary?.total_deaths ?? 0) + (summary?.total_days_away ?? 0) + (summary?.total_restricted ?? 0) + (summary?.total_other_recordable ?? 0)}
                      </p>
                      <p className="text-xs text-muted-foreground">Recordable Cases</p>
                    </div>
                    <div className="rounded-lg border p-3 text-center">
                      <p className="text-2xl font-bold text-foreground">
                        {(summary?.total_hours_worked ?? 0).toLocaleString()}
                      </p>
                      <p className="text-xs text-muted-foreground">Hours Worked</p>
                    </div>
                    <div className="rounded-lg border p-3 text-center">
                      <p className="text-2xl font-bold text-foreground">{summary?.annual_average_employees ?? 0}</p>
                      <p className="text-xs text-muted-foreground">Avg Employees</p>
                    </div>
                  </div>
                </div>

                <div className="rounded-lg bg-muted p-4">
                  <h4 className="mb-1 text-sm font-semibold text-[var(--concrete-600)]">How to Improve</h4>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li>1. Increase near-miss reporting to catch hazards before injuries occur</li>
                    <li>2. Conduct regular safety training and toolbox talks</li>
                    <li>3. Perform daily site inspections with corrective action follow-up</li>
                    <li>4. Implement a return-to-work program to reduce lost time</li>
                    <li>5. Review incident root causes and address systemic issues</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Add/Edit Entry Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingEntry ? 'Edit Entry' : 'Add OSHA 300 Log Entry'}</DialogTitle>
            <DialogDescription>
              Record a work-related injury or illness
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[60vh] space-y-4 overflow-y-auto py-2">
            {/* Privacy Case toggle */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="privacy_case"
                checked={formData.privacy_case}
                onChange={(e) => setFormData({ ...formData, privacy_case: e.target.checked })}
                className="h-4 w-4 rounded border-border"
              />
              <Label htmlFor="privacy_case" className="text-sm">
                Privacy Case (employee name will be redacted on the log)
              </Label>
            </div>

            {!formData.privacy_case && (
              <div>
                <Label htmlFor="employee_name">Employee Name</Label>
                <Input
                  id="employee_name"
                  value={formData.employee_name}
                  onChange={(e) => setFormData({ ...formData, employee_name: e.target.value })}
                  placeholder="Full name"
                />
              </div>
            )}

            <div>
              <Label htmlFor="job_title">Job Title</Label>
              <Input
                id="job_title"
                value={formData.job_title}
                onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                placeholder="e.g., Laborer, Electrician"
              />
            </div>

            <div>
              <Label htmlFor="date_of_injury">Date of Injury</Label>
              <Input
                id="date_of_injury"
                type="date"
                value={formData.date_of_injury}
                onChange={(e) => setFormData({ ...formData, date_of_injury: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="where_event_occurred">Where Event Occurred</Label>
              <Input
                id="where_event_occurred"
                value={formData.where_event_occurred}
                onChange={(e) => setFormData({ ...formData, where_event_occurred: e.target.value })}
                placeholder="e.g., Building A, East Wing, Ground Level"
              />
            </div>

            <div>
              <Label htmlFor="description">Description of Injury/Illness</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe what happened and how..."
                rows={3}
              />
            </div>

            <div>
              <Label>Classification</Label>
              <Select
                value={formData.classification}
                onValueChange={(v) => setFormData({ ...formData, classification: v as OshaLogEntry['classification'] })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CLASSIFICATION_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Injury Type</Label>
              <Select
                value={formData.injury_type}
                onValueChange={(v) => setFormData({ ...formData, injury_type: v as OshaLogEntry['injury_type'] })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {INJURY_TYPE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {(formData.classification === 'days_away_from_work' || formData.classification === 'death') && (
              <div>
                <Label htmlFor="days_away">Days Away from Work</Label>
                <Input
                  id="days_away"
                  type="number"
                  min={0}
                  value={formData.days_away_from_work}
                  onChange={(e) => setFormData({ ...formData, days_away_from_work: parseInt(e.target.value) || 0 })}
                />
              </div>
            )}

            {formData.classification === 'job_transfer_or_restriction' && (
              <div>
                <Label htmlFor="days_restricted">Days of Restricted Work</Label>
                <Input
                  id="days_restricted"
                  type="number"
                  min={0}
                  value={formData.days_of_restricted_work}
                  onChange={(e) => setFormData({ ...formData, days_of_restricted_work: parseInt(e.target.value) || 0 })}
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button className="bg-primary hover:bg-[var(--machine-dark)]" onClick={handleSave}>
              {editingEntry ? 'Update' : 'Save'} Entry
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Certify Summary Dialog */}
      <Dialog open={showCertifyDialog} onOpenChange={setShowCertifyDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Certify 300A Summary</DialogTitle>
            <DialogDescription>
              I certify that I have examined this document and that to the best of my knowledge
              the entries are true, accurate, and complete.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label htmlFor="certify_name">Certified By (Company Executive)</Label>
              <Input
                id="certify_name"
                value={certifyName}
                onChange={(e) => setCertifyName(e.target.value)}
                placeholder="Full name and title"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Date: {format(new Date(), 'MMMM d, yyyy')}
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCertifyDialog(false)}>
              Cancel
            </Button>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={handleCertify}
              disabled={!certifyName.trim()}
            >
              <ShieldCheck className="mr-2 h-4 w-4" />
              Certify
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
