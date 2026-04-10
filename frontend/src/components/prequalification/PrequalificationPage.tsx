import { useState } from 'react';
import {
  FileCheck,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Minus,
  ChevronDown,
  ChevronUp,
  ExternalLink,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useGeneratePackage, usePrequalPackages } from '@/hooks/usePrequalification';
import type { PrequalPackage, PrequalDocument } from '@/lib/constants';
import { ComplianceRing } from '@/components/projects/ComplianceRing';

const PLATFORMS = [
  { value: 'isnetworld', label: 'ISNetworld' },
  { value: 'avetta', label: 'Avetta' },
  { value: 'browz', label: 'BROWZ' },
  { value: 'generic', label: 'Generic GC' },
] as const;

function StatusIcon({ status }: { status: PrequalDocument['status'] }) {
  switch (status) {
    case 'ready':
      return <CheckCircle2 className="h-4 w-4 text-[var(--pass)]" />;
    case 'outdated':
      return <AlertTriangle className="h-4 w-4 text-[var(--warn)]" />;
    case 'missing':
      return <XCircle className="h-4 w-4 text-[var(--fail)]" />;
    case 'na':
      return <Minus className="h-4 w-4 text-muted-foreground" />;
  }
}

function StatusBadge({ status }: { status: PrequalDocument['status'] }) {
  const config = {
    ready: { label: 'Ready', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    outdated: { label: 'Outdated', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
    missing: { label: 'Missing', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
    na: { label: 'N/A', className: 'bg-muted text-muted-foreground hover:bg-muted' },
  };
  const { label, className } = config[status];
  return <Badge className={className}>{label}</Badge>;
}

function ActionButton({ status }: { status: PrequalDocument['status'] }) {
  switch (status) {
    case 'ready':
      return (
        <Button variant="outline" size="sm" className="text-xs">
          <ExternalLink className="mr-1 h-3 w-3" />
          View
        </Button>
      );
    case 'outdated':
      return (
        <Button variant="outline" size="sm" className="border-[var(--warn)] text-[var(--warn)] text-xs hover:bg-[var(--warn-bg)]">
          Update
        </Button>
      );
    case 'missing':
      return (
        <Button variant="outline" size="sm" className="border-[var(--fail)] text-[var(--fail)] text-xs hover:bg-[var(--fail-bg)]">
          Generate
        </Button>
      );
    default:
      return null;
  }
}

function DocumentCategory({ category, documents }: { category: string; documents: PrequalDocument[] }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="rounded-lg border">
      <button
        className="flex w-full items-center justify-between p-3 text-left hover:bg-muted"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-[var(--concrete-600)]">{category}</span>
          <span className="text-xs text-muted-foreground">
            ({documents.filter(d => d.status === 'ready').length}/{documents.length} ready)
          </span>
        </div>
        {expanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
      </button>
      {expanded && (
        <div className="border-t">
          {documents.map((doc, i) => (
            <div
              key={doc.document_name}
              className={`flex items-center gap-3 px-3 py-2 ${i < documents.length - 1 ? 'border-b border-border' : ''}`}
            >
              <StatusIcon status={doc.status} />
              <div className="min-w-0 flex-1">
                <p className="text-sm text-[var(--concrete-600)]">{doc.document_name}</p>
                {doc.notes && <p className="text-xs text-muted-foreground">{doc.notes}</p>}
              </div>
              <StatusBadge status={doc.status} />
              <ActionButton status={doc.status} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function QuestionnaireSection({ questionnaire }: { questionnaire: Record<string, unknown> }) {
  const [expanded, setExpanded] = useState(false);

  const FIELD_LABELS: Record<string, string> = {
    company_legal_name: 'Company Legal Name',
    dba_name: 'DBA Name',
    ein: 'EIN',
    address: 'Address',
    phone: 'Phone',
    email: 'Email',
    website: 'Website',
    year_established: 'Year Established',
    number_of_employees: 'Number of Employees',
    annual_revenue: 'Annual Revenue',
    naics_code: 'NAICS Code',
    sic_code: 'SIC Code',
    primary_trade: 'Primary Trade',
    license_number: 'License Number',
    license_state: 'License State',
    safety_director_name: 'Safety Director Name',
    safety_director_phone: 'Safety Director Phone',
    safety_director_email: 'Safety Director Email',
    has_written_safety_program: 'Written Safety Program',
    safety_program_last_reviewed: 'Safety Program Last Reviewed',
    has_safety_committee: 'Safety Committee',
    safety_committee_meets: 'Committee Meeting Frequency',
    osha_citation_last_3_years: 'OSHA Citations (Last 3 Years)',
    fatalities_last_3_years: 'Fatalities (Last 3 Years)',
    current_emr: 'Current EMR',
    emr_year: 'EMR Year',
    previous_emr: 'Previous EMR',
    trir_current: 'Current TRIR',
    trir_previous: 'Previous TRIR',
    dart_current: 'Current DART',
    dart_previous: 'Previous DART',
    hours_worked_current_year: 'Hours Worked (Current Year)',
    drug_testing_program: 'Drug Testing Program',
    drug_testing_provider: 'Drug Testing Provider',
    background_check_policy: 'Background Check Policy',
    new_hire_orientation: 'New Hire Orientation',
    toolbox_talk_frequency: 'Toolbox Talk Frequency',
    incident_investigation_procedure: 'Incident Investigation',
    near_miss_reporting: 'Near-Miss Reporting',
    subcontractor_management: 'Subcontractor Management',
  };

  const entries = Object.entries(questionnaire);
  const displayedEntries = expanded ? entries : entries.slice(0, 8);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Pre-Filled Questionnaire</CardTitle>
        <CardDescription>
          {entries.length} answers auto-filled from your Kerf data. All fields are editable.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-3 sm:grid-cols-2">
          {displayedEntries.map(([key, value]) => (
            <div key={key} className="space-y-1">
              <Label className="text-xs text-muted-foreground">
                {FIELD_LABELS[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Label>
              <Input
                defaultValue={String(value || '')}
                className="text-sm"
              />
            </div>
          ))}
        </div>
        {entries.length > 8 && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-[var(--machine-dark)] hover:text-primary"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Show Less' : `Show All ${entries.length} Fields`}
            {expanded ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export function PrequalificationPage() {
  const [platform, setPlatform] = useState<string>('isnetworld');
  const [clientName, setClientName] = useState('');
  const [activePackage, setActivePackage] = useState<PrequalPackage | null>(null);

  const generatePackage = useGeneratePackage();
  const { data: existingPackages } = usePrequalPackages();

  const handleGenerate = async () => {
    const result = await generatePackage.mutateAsync({
      platform,
      client_name: clientName || 'New Client',
    });
    setActivePackage(result);
  };

  const pkg = activePackage || existingPackages?.[0] || null;

  // Group documents by category
  const docsByCategory: Record<string, PrequalDocument[]> = {};
  if (pkg) {
    for (const doc of pkg.documents) {
      if (!docsByCategory[doc.category]) {
        docsByCategory[doc.category] = [];
      }
      docsByCategory[doc.category].push(doc);
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Prequalification Automation</h1>
        <p className="text-sm text-muted-foreground">
          Generate prequalification packages for ISNetworld, Avetta, BROWZ, and more
        </p>
      </div>

      {/* Top section: Platform selector + Generate */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 sm:grid-cols-4">
            <div className="space-y-2">
              <Label>Platform</Label>
              <Select value={platform} onValueChange={(v) => { if (v) setPlatform(v); }}>
                <SelectTrigger>
                  <SelectValue placeholder="Select platform" />
                </SelectTrigger>
                <SelectContent>
                  {PLATFORMS.map(p => (
                    <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label>Client Name</Label>
              <Input
                placeholder="e.g., Turner Construction"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button
                className="w-full bg-primary hover:bg-[var(--machine-dark)]"
                disabled={generatePackage.isPending}
                onClick={handleGenerate}
              >
                {generatePackage.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileCheck className="mr-2 h-4 w-4" />
                    Generate Package
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Package results */}
      {pkg && (
        <>
          {/* Readiness overview */}
          <div className="grid gap-4 sm:grid-cols-4">
            <Card className="sm:col-span-1">
              <CardContent className="flex flex-col items-center pt-6">
                <ComplianceRing score={pkg.overall_readiness} size="lg" />
                <p className="mt-2 text-sm font-semibold text-[var(--concrete-600)]">Overall Readiness</p>
                <p className="text-xs text-muted-foreground">
                  {pkg.platform === 'isnetworld' ? 'ISNetworld' :
                   pkg.platform === 'avetta' ? 'Avetta' :
                   pkg.platform === 'browz' ? 'BROWZ' : 'Generic GC'}
                  {pkg.client_name ? ` for ${pkg.client_name}` : ''}
                </p>
              </CardContent>
            </Card>
            <Card className="sm:col-span-3">
              <CardContent className="pt-6">
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-foreground">{pkg.total_documents}</p>
                    <p className="text-xs text-muted-foreground">Total Required</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-[var(--pass)]">{pkg.ready_documents}</p>
                    <p className="text-xs text-muted-foreground">Ready</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-[var(--warn)]">{pkg.outdated_documents}</p>
                    <p className="text-xs text-muted-foreground">Outdated</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-[var(--fail)]">{pkg.missing_documents}</p>
                    <p className="text-xs text-muted-foreground">Missing</p>
                  </div>
                </div>
                <Separator className="my-4" />
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="h-3 overflow-hidden rounded-full bg-muted">
                      <div className="flex h-full">
                        <div
                          className="bg-[var(--pass)] transition-all"
                          style={{ width: `${(pkg.ready_documents / pkg.total_documents) * 100}%` }}
                        />
                        <div
                          className="bg-[var(--warn)] transition-all"
                          style={{ width: `${(pkg.outdated_documents / pkg.total_documents) * 100}%` }}
                        />
                        <div
                          className="bg-[var(--fail)] transition-all"
                          style={{ width: `${(pkg.missing_documents / pkg.total_documents) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  {pkg.submission_deadline && (
                    <p className="text-xs text-muted-foreground">
                      Deadline: <span className="font-medium">{pkg.submission_deadline}</span>
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Document checklist by category */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Document Checklist</CardTitle>
              <CardDescription>Documents organized by category for {pkg.platform === 'isnetworld' ? 'ISNetworld' : pkg.platform} submission</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {Object.entries(docsByCategory).map(([category, docs]) => (
                <DocumentCategory key={category} category={category} documents={docs} />
              ))}
            </CardContent>
          </Card>

          {/* Pre-filled Questionnaire */}
          <QuestionnaireSection questionnaire={pkg.questionnaire} />
        </>
      )}
    </div>
  );
}
