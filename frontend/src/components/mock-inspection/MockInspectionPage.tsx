import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Shield,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Loader2,
  Zap,
  FileText,
  Users,
  ClipboardCheck,
  ArrowRight,
  Clock,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useRunMockInspection, useMockInspectionResults, useMockInspectionResult } from '@/hooks/useMockInspection';
import { useProjects } from '@/hooks/useProjects';
import type { MockInspectionResult, MockInspectionFinding } from '@/lib/constants';
import { format } from 'date-fns';

const PROGRESS_STEPS = [
  'Reviewing documents...',
  'Checking training records...',
  'Analyzing inspection logs...',
  'Evaluating OSHA recordkeeping...',
  'Generating report...',
];

function getScoreColor(score: number): { ring: string; text: string; bg: string; grade: string } {
  if (score < 40) return { ring: 'stroke-[var(--fail)]', text: 'text-[var(--fail)]', bg: 'bg-[var(--fail-bg)]', grade: 'text-[var(--fail)]' };
  if (score < 60) return { ring: 'stroke-[var(--warn)]', text: 'text-[var(--warn)]', bg: 'bg-[var(--warn-bg)]', grade: 'text-[var(--warn)]' };
  if (score < 75) return { ring: 'stroke-[var(--warn)]', text: 'text-[var(--warn)]', bg: 'bg-[var(--warn-bg)]', grade: 'text-[var(--warn)]' };
  if (score < 90) return { ring: 'stroke-[var(--pass)]', text: 'text-[var(--pass)]', bg: 'bg-[var(--pass-bg)]', grade: 'text-[var(--pass)]' };
  return { ring: 'stroke-emerald-600', text: 'text-emerald-700', bg: 'bg-emerald-50', grade: 'text-emerald-700' };
}

function getSeverityConfig(severity: MockInspectionFinding['severity']) {
  switch (severity) {
    case 'critical':
      return { label: 'Critical', badge: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]', border: 'border-l-4 border-l-[var(--fail)]', icon: 'text-[var(--fail)]' };
    case 'high':
      return { label: 'High', badge: 'bg-[var(--machine-wash)] text-primary hover:bg-[var(--machine-wash)]', border: 'border-l-4 border-l-primary', icon: 'text-primary' };
    case 'medium':
      return { label: 'Medium', badge: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]', border: 'border-l-4 border-l-[var(--warn)]', icon: 'text-[var(--warn)]' };
    case 'low':
      return { label: 'Low', badge: 'bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)]', border: 'border-l-4 border-l-[var(--info)]', icon: 'text-[var(--info)]' };
    case 'info':
      return { label: 'Info', badge: 'bg-muted text-[var(--concrete-600)] hover:bg-muted', border: 'border-l-4 border-l-muted-foreground', icon: 'text-muted-foreground' };
  }
}

function ScoreRing({ score, grade }: { score: number; grade: string }) {
  const colors = getScoreColor(score);
  const radius = 54;
  const strokeWidth = 8;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score / 100) * circumference;
  const viewBoxSize = (radius + strokeWidth) * 2;
  const center = viewBoxSize / 2;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative inline-flex h-36 w-36 items-center justify-center">
        <svg
          className="rotate-[-90deg]"
          width="100%"
          height="100%"
          viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
        >
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            className="stroke-muted"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            className={colors.ring}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className={`text-4xl font-bold ${colors.text}`}>{score}</span>
          <span className={`text-lg font-semibold ${colors.grade}`}>{grade}</span>
        </div>
      </div>
    </div>
  );
}

function FindingCard({ finding }: { finding: MockInspectionFinding }) {
  const [expanded, setExpanded] = useState(false);
  const config = getSeverityConfig(finding.severity);

  return (
    <Card className={`${config.border} overflow-hidden`}>
      <button
        className="flex w-full items-center gap-3 p-4 text-left transition-colors hover:bg-muted"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        )}
        <Badge className={config.badge}>{config.label}</Badge>
        <span className="min-w-0 flex-1 text-sm font-medium text-foreground">{finding.title}</span>
        <Badge variant="outline" className="shrink-0 font-mono text-xs">
          {finding.osha_standard}
        </Badge>
      </button>

      {expanded && (
        <div className="border-t bg-muted/50 px-4 pb-4 pt-3 space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">What an inspector would find</p>
            <p className="mt-1 text-sm text-[var(--concrete-600)]">{finding.description}</p>
          </div>

          <div className="rounded-lg border border-border bg-white p-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">OSHA Citation</p>
            <p className="mt-1 text-sm italic text-[var(--concrete-600)] leading-relaxed">{finding.citation_language}</p>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Corrective Action</p>
            <p className="mt-1 text-sm text-[var(--concrete-600)]">{finding.corrective_action}</p>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Estimated Penalty</p>
              <p className="mt-1 text-sm font-semibold text-[var(--fail)]">{finding.estimated_penalty}</p>
            </div>

            {finding.can_auto_fix && (
              <Button
                className="bg-[var(--pass)] hover:bg-[var(--pass)] text-white"
                onClick={(e) => {
                  e.stopPropagation();
                }}
              >
                <Zap className="mr-2 h-4 w-4" />
                Fix This Now
              </Button>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}

function InspectionResults({ result }: { result: MockInspectionResult }) {
  const colors = getScoreColor(result.overall_score);

  const severityOrder: MockInspectionFinding['severity'][] = ['critical', 'high', 'medium', 'low', 'info'];
  const groupedFindings = severityOrder
    .map((sev) => ({
      severity: sev,
      findings: result.findings.filter((f) => f.severity === sev),
    }))
    .filter((g) => g.findings.length > 0);

  return (
    <div className="space-y-6">
      {/* Score Card */}
      <Card className={`${colors.bg} border-0`}>
        <CardContent className="py-6">
          <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
            <ScoreRing score={result.overall_score} grade={result.grade} />

            <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
              {result.critical_findings > 0 && (
                <div className="flex items-center gap-1.5 rounded-lg bg-[var(--fail-bg)] px-3 py-2">
                  <span className="text-lg font-bold text-[var(--fail)]">{result.critical_findings}</span>
                  <span className="text-xs font-medium text-[var(--fail)]">Critical</span>
                </div>
              )}
              {result.high_findings > 0 && (
                <div className="flex items-center gap-1.5 rounded-lg bg-[var(--machine-wash)] px-3 py-2">
                  <span className="text-lg font-bold text-primary">{result.high_findings}</span>
                  <span className="text-xs font-medium text-[var(--machine-dark)]">High</span>
                </div>
              )}
              {result.medium_findings > 0 && (
                <div className="flex items-center gap-1.5 rounded-lg bg-[var(--warn-bg)] px-3 py-2">
                  <span className="text-lg font-bold text-[var(--warn)]">{result.medium_findings}</span>
                  <span className="text-xs font-medium text-[var(--warn)]">Medium</span>
                </div>
              )}
              {result.low_findings > 0 && (
                <div className="flex items-center gap-1.5 rounded-lg bg-[var(--info-bg)] px-3 py-2">
                  <span className="text-lg font-bold text-[var(--info)]">{result.low_findings}</span>
                  <span className="text-xs font-medium text-[var(--info)]">Low</span>
                </div>
              )}
            </div>

            <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span>{result.documents_reviewed} docs</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Users className="h-4 w-4 text-muted-foreground" />
                <span>{result.training_records_reviewed} training</span>
              </div>
              <div className="flex items-center gap-1.5">
                <ClipboardCheck className="h-4 w-4 text-muted-foreground" />
                <span>{result.inspections_reviewed} inspections</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executive Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Executive Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-[var(--concrete-600)]">{result.executive_summary}</p>
        </CardContent>
      </Card>

      {/* Findings */}
      <div>
        <h3 className="mb-3 text-lg font-semibold text-foreground">
          Findings ({result.total_findings})
        </h3>
        <div className="space-y-3">
          {groupedFindings.map((group) => (
            <div key={group.severity} className="space-y-2">
              {group.findings.map((finding) => (
                <FindingCard key={finding.finding_id} finding={finding} />
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Areas Checked */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Areas Checked</CardTitle>
          <CardDescription>{result.areas_checked.length} compliance areas reviewed</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {result.areas_checked.map((area) => (
              <Badge
                key={area}
                variant="outline"
                className="border-[var(--pass)] bg-[var(--pass-bg)] text-[var(--pass)]"
              >
                <CheckCircle2 className="mr-1 h-3 w-3" />
                {area}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function MockInspectionPage() {
  const { id: resultId } = useParams<{ id: string }>();
  const { data: projects } = useProjects();
  const { data: results } = useMockInspectionResults();
  const { data: specificResult } = useMockInspectionResult(resultId);
  const runInspection = useRunMockInspection();

  const [selectedProjectId, setSelectedProjectId] = useState<string>('company-wide');
  const [isRunning, setIsRunning] = useState(false);
  const [progressStep, setProgressStep] = useState(0);
  const [currentResult, setCurrentResult] = useState<MockInspectionResult | null>(null);

  const activeProjects = projects?.filter((p) => p.status === 'active') ?? [];

  // If viewing a specific result via URL
  useEffect(() => {
    if (specificResult) {
      setCurrentResult(specificResult);
    }
  }, [specificResult]);

  const handleRunInspection = async () => {
    setIsRunning(true);
    setProgressStep(0);
    setCurrentResult(null);

    // Simulate progress steps
    for (let i = 0; i < PROGRESS_STEPS.length; i++) {
      setProgressStep(i);
      await new Promise((r) => setTimeout(r, 800));
    }

    try {
      const result = await runInspection.mutateAsync(
        selectedProjectId !== 'company-wide' ? { project_id: selectedProjectId } : undefined
      );
      setCurrentResult(result);
    } finally {
      setIsRunning(false);
    }
  };

  const pastResults = results?.filter((r) => r.id !== currentResult?.id) ?? [];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Mock OSHA Inspection</h1>
        <p className="text-sm text-muted-foreground">
          Find out what OSHA would find if they walked in today.
        </p>
      </div>

      {/* Run Inspection Hero */}
      {!currentResult && !isRunning && (
        <Card className="border-2 border-primary bg-gradient-to-br from-[var(--machine-wash)] to-[var(--warn-bg)]">
          <CardContent className="py-8">
            <div className="flex flex-col items-center text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--machine-wash)]">
                <Shield className="h-8 w-8 text-[var(--machine-dark)]" />
              </div>
              <h2 className="mt-4 text-xl font-bold text-foreground">
                Run a Mock OSHA Inspection
              </h2>
              <p className="mt-2 max-w-lg text-sm text-muted-foreground">
                Kerf will review all your documents, training records, inspection logs, and
                OSHA recordkeeping — then return findings formatted exactly like real OSHA citations.
              </p>

              <div className="mt-6 w-full max-w-xs">
                <Select value={selectedProjectId} onValueChange={(v) => { if (v) setSelectedProjectId(v); }}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select scope" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="company-wide">Company-Wide Inspection</SelectItem>
                    {activeProjects.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button
                size="lg"
                className="mt-6 bg-primary px-8 text-lg hover:bg-[var(--machine-dark)]"
                onClick={handleRunInspection}
              >
                <Shield className="mr-2 h-5 w-5" />
                Run Mock Inspection
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Running Progress */}
      {isRunning && (
        <Card className="border-2 border-primary">
          <CardContent className="py-12">
            <div className="flex flex-col items-center text-center">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <h2 className="mt-4 text-lg font-bold text-foreground">Inspection in Progress</h2>
              <div className="mt-6 w-full max-w-sm space-y-3">
                {PROGRESS_STEPS.map((step, i) => (
                  <div
                    key={step}
                    className={`flex items-center gap-3 text-sm transition-all ${
                      i < progressStep
                        ? 'text-[var(--pass)]'
                        : i === progressStep
                          ? 'font-medium text-[var(--machine-dark)]'
                          : 'text-muted-foreground'
                    }`}
                  >
                    {i < progressStep ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-[var(--pass)]" />
                    ) : i === progressStep ? (
                      <Loader2 className="h-4 w-4 shrink-0 animate-spin text-primary" />
                    ) : (
                      <div className="h-4 w-4 shrink-0 rounded-full border border-border" />
                    )}
                    {step}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {currentResult && !isRunning && (
        <>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">
                Inspection completed {format(new Date(currentResult.inspection_date), 'MMM d, yyyy h:mm a')}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => {
                setCurrentResult(null);
              }}
            >
              Run New Inspection
            </Button>
          </div>
          <InspectionResults result={currentResult} />
        </>
      )}

      {/* Past Inspections */}
      {!isRunning && pastResults.length > 0 && (
        <>
          <Separator />
          <div>
            <h3 className="mb-3 text-lg font-semibold text-foreground">Past Inspections</h3>
            <div className="space-y-2">
              {pastResults.map((result) => {
                const scoreColors = getScoreColor(result.overall_score);
                return (
                  <Card
                    key={result.id}
                    className="cursor-pointer transition-shadow hover:shadow-md"
                    onClick={() => {
                      setCurrentResult(result);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                  >
                    <CardContent className="flex items-center gap-4 py-4">
                      <div className={`flex h-12 w-12 items-center justify-center rounded-full ${scoreColors.bg}`}>
                        <span className={`text-lg font-bold ${scoreColors.text}`}>{result.overall_score}</span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-bold ${scoreColors.grade}`}>Grade: {result.grade}</span>
                          <span className="text-sm text-muted-foreground">
                            {result.total_findings} findings
                          </span>
                          {result.critical_findings > 0 && (
                            <Badge className="bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]">
                              {result.critical_findings} critical
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {result.documents_reviewed} documents, {result.training_records_reviewed} training records, {result.inspections_reviewed} inspections reviewed
                        </p>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        {format(new Date(result.inspection_date), 'MMM d, yyyy')}
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* Empty state for no results at all */}
      {!isRunning && !currentResult && (!results || results.length === 0) && (
        <Card>
          <CardContent className="py-8 text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-muted-foreground" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">No inspection history</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Run your first mock inspection to see how you measure up against OSHA standards.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
