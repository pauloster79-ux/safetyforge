import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import {
  Building2,
  ClipboardCheck,
  MessageSquare,
  AlertTriangle,
  AlertCircle,
  Users,
  Shield,
  TrendingDown,
  TrendingUp,
  DollarSign,
  Calculator,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { useAnalyticsDashboard, useEmrEstimate } from '@/hooks/useAnalytics';
import { ROUTES } from '@/lib/constants';
import type { EmrEstimate } from '@/lib/constants';

function ComplianceRingLarge({ score }: { score: number }) {
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? 'text-[var(--pass)]' : score >= 60 ? 'text-[var(--warn)]' : 'text-[var(--fail)]';
  const strokeColor = score >= 80 ? 'stroke-[var(--pass)]' : score >= 60 ? 'stroke-[var(--warn)]' : 'stroke-[var(--fail)]';

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="8" className="text-muted" />
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={strokeColor}
        />
      </svg>
      <span className={`absolute text-xl font-bold ${color}`}>{score}%</span>
    </div>
  );
}

export function AnalyticsPage() {
  const navigate = useCanvasNavigate();
  const { data: metrics, isLoading } = useAnalyticsDashboard();
  const emrEstimate = useEmrEstimate();

  const [emrForm, setEmrForm] = useState({
    current_emr: '1.15',
    annual_payroll: '500000',
    wc_rate: '15',
  });
  const [emrResult, setEmrResult] = useState<EmrEstimate | null>(null);

  const handleCalculateEmr = async () => {
    const result = await emrEstimate.mutateAsync({
      current_emr: parseFloat(emrForm.current_emr) || 1.0,
      annual_payroll: parseFloat(emrForm.annual_payroll) || 500000,
      wc_rate: parseFloat(emrForm.wc_rate) || 15,
    });
    setEmrResult(result);
  };

  if (isLoading || !metrics) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const INDUSTRY_TRIR = 3.0;
  const INDUSTRY_DART = 1.7;
  const trirBelowAvg = metrics.trir <= INDUSTRY_TRIR;
  const dartBelowAvg = metrics.dart <= INDUSTRY_DART;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Safety Analytics</h1>
        <p className="text-sm text-muted-foreground">Comprehensive safety performance overview</p>
      </div>

      {/* Section 1: Key Metrics Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="cursor-pointer transition-shadow hover:shadow-md" onClick={() => navigate(ROUTES.PROJECTS)}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--info-bg)]">
                <Building2 className="h-5 w-5 text-[var(--info)]" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{metrics.active_projects}</p>
                <p className="text-xs text-muted-foreground">Active Projects</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--machine-wash)]">
                <ClipboardCheck className="h-5 w-5 text-[var(--machine-dark)]" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{metrics.inspections_this_month}</p>
                <p className="text-xs text-muted-foreground">Inspections This Month</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--pass-bg)]">
                <MessageSquare className="h-5 w-5 text-[var(--pass)]" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{metrics.talks_this_month}</p>
                <p className="text-xs text-muted-foreground">Toolbox Talks This Month</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${metrics.open_hazard_reports > 0 ? 'bg-[var(--fail-bg)]' : 'bg-[var(--pass-bg)]'}`}>
                <AlertTriangle className={`h-5 w-5 ${metrics.open_hazard_reports > 0 ? 'text-[var(--fail)]' : 'text-[var(--pass)]'}`} />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{metrics.open_hazard_reports}</p>
                <p className="text-xs text-muted-foreground">Open Hazard Reports</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${metrics.incidents_this_month > 0 ? 'bg-[var(--fail-bg)]' : 'bg-[var(--pass-bg)]'}`}>
                <AlertCircle className={`h-5 w-5 ${metrics.incidents_this_month > 0 ? 'text-[var(--fail)]' : 'text-[var(--pass)]'}`} />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{metrics.incidents_this_month}</p>
                <p className="text-xs text-muted-foreground">Incidents This Month</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <ComplianceRingLarge score={metrics.avg_compliance_score} />
              <div>
                <p className="text-xs text-muted-foreground">Avg Compliance Score</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer transition-shadow hover:shadow-md" onClick={() => navigate(ROUTES.OSHA_LOG)}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${trirBelowAvg ? 'bg-[var(--pass-bg)]' : 'bg-[var(--fail-bg)]'}`}>
                {trirBelowAvg ? <TrendingDown className="h-5 w-5 text-[var(--pass)]" /> : <TrendingUp className="h-5 w-5 text-[var(--fail)]" />}
              </div>
              <div>
                <p className={`text-2xl font-bold ${trirBelowAvg ? 'text-[var(--pass)]' : 'text-[var(--fail)]'}`}>
                  {metrics.trir.toFixed(1)}
                </p>
                <p className="text-xs text-muted-foreground">TRIR</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer transition-shadow hover:shadow-md" onClick={() => navigate(ROUTES.OSHA_LOG)}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${dartBelowAvg ? 'bg-[var(--pass-bg)]' : 'bg-[var(--fail-bg)]'}`}>
                {dartBelowAvg ? <TrendingDown className="h-5 w-5 text-[var(--pass)]" /> : <TrendingUp className="h-5 w-5 text-[var(--fail)]" />}
              </div>
              <div>
                <p className={`text-2xl font-bold ${dartBelowAvg ? 'text-[var(--pass)]' : 'text-[var(--fail)]'}`}>
                  {metrics.dart.toFixed(1)}
                </p>
                <p className="text-xs text-muted-foreground">DART</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Section 2: Safety Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Safety Performance</CardTitle>
          <CardDescription>Your rates compared to construction industry averages</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 sm:grid-cols-2">
            <div className="rounded-lg border p-4">
              <p className="text-sm font-medium text-muted-foreground">Total Recordable Incident Rate (TRIR)</p>
              <div className="mt-2 flex items-end gap-2">
                <span className={`text-3xl font-bold ${trirBelowAvg ? 'text-[var(--pass)]' : 'text-[var(--fail)]'}`}>
                  {metrics.trir.toFixed(1)}
                </span>
                <span className="mb-1 text-sm text-muted-foreground">vs Industry Avg: {INDUSTRY_TRIR.toFixed(1)}</span>
              </div>
              <div className="mt-3 flex items-center gap-2">
                {trirBelowAvg ? (
                  <Badge className="bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]">Below Average</Badge>
                ) : (
                  <Badge className="bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]">Above Average</Badge>
                )}
                {trirBelowAvg ? (
                  <TrendingDown className="h-4 w-4 text-[var(--pass)]" />
                ) : (
                  <TrendingUp className="h-4 w-4 text-[var(--fail)]" />
                )}
              </div>
            </div>

            <div className="rounded-lg border p-4">
              <p className="text-sm font-medium text-muted-foreground">Days Away, Restricted, or Transferred (DART)</p>
              <div className="mt-2 flex items-end gap-2">
                <span className={`text-3xl font-bold ${dartBelowAvg ? 'text-[var(--pass)]' : 'text-[var(--fail)]'}`}>
                  {metrics.dart.toFixed(1)}
                </span>
                <span className="mb-1 text-sm text-muted-foreground">vs Industry Avg: {INDUSTRY_DART.toFixed(1)}</span>
              </div>
              <div className="mt-3 flex items-center gap-2">
                {dartBelowAvg ? (
                  <Badge className="bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]">Below Average</Badge>
                ) : (
                  <Badge className="bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]">Above Average</Badge>
                )}
                {dartBelowAvg ? (
                  <TrendingDown className="h-4 w-4 text-[var(--pass)]" />
                ) : (
                  <TrendingUp className="h-4 w-4 text-[var(--fail)]" />
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section 3: EMR Calculator */}
      <Card className="border-primary bg-gradient-to-r from-[var(--machine-wash)] to-[var(--warn-bg)]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <DollarSign className="h-5 w-5 text-[var(--machine-dark)]" />
            EMR Impact Calculator
          </CardTitle>
          <CardDescription>
            See how improving your safety record can lower your workers' comp premium
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="current_emr">Current EMR</Label>
              <Input
                id="current_emr"
                type="number"
                step="0.01"
                value={emrForm.current_emr}
                onChange={(e) => setEmrForm((p) => ({ ...p, current_emr: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="annual_payroll">Annual Payroll ($)</Label>
              <Input
                id="annual_payroll"
                type="number"
                step="1000"
                value={emrForm.annual_payroll}
                onChange={(e) => setEmrForm((p) => ({ ...p, annual_payroll: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="wc_rate">Workers' Comp Rate ($/100)</Label>
              <Input
                id="wc_rate"
                type="number"
                step="0.5"
                value={emrForm.wc_rate}
                onChange={(e) => setEmrForm((p) => ({ ...p, wc_rate: e.target.value }))}
              />
            </div>
          </div>

          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            disabled={emrEstimate.isPending}
            onClick={handleCalculateEmr}
          >
            {emrEstimate.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Calculating...
              </>
            ) : (
              <>
                <Calculator className="mr-2 h-4 w-4" />
                Calculate Impact
              </>
            )}
          </Button>

          {emrResult && (
            <>
              <Separator />
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-lg border border-primary bg-white p-4 text-center">
                  <p className="text-xs font-medium text-muted-foreground">Current Annual Premium</p>
                  <p className="mt-1 text-2xl font-bold text-foreground">
                    ${emrResult.current_premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </p>
                  <p className="text-xs text-muted-foreground">EMR: {emrResult.current_emr.toFixed(2)}</p>
                </div>
                <div className="rounded-lg border border-[var(--pass)] bg-white p-4 text-center">
                  <p className="text-xs font-medium text-muted-foreground">Projected Premium</p>
                  <p className="mt-1 text-2xl font-bold text-[var(--pass)]">
                    ${emrResult.projected_premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </p>
                  <p className="text-xs text-muted-foreground">EMR: {emrResult.projected_emr.toFixed(2)}</p>
                </div>
                <div className="rounded-lg border border-[var(--pass)] bg-[var(--pass-bg)] p-4 text-center">
                  <p className="text-xs font-medium text-[var(--pass)]">Potential Annual Savings</p>
                  <p className="mt-1 text-2xl font-bold text-[var(--pass)]">
                    ${emrResult.potential_savings.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </p>
                  <p className="text-xs text-[var(--pass)]">By improving safety metrics</p>
                </div>
              </div>

              {(emrResult.recommendations || []).length > 0 && (
                <div className="rounded-lg border border-primary bg-white p-4">
                  <p className="font-medium text-[var(--concrete-600)]">Recommendations to Lower Your EMR</p>
                  <ul className="mt-2 space-y-2">
                    {(emrResult.recommendations || []).map((rec, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                        <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Section 4: Compliance Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Compliance Overview</CardTitle>
          <CardDescription>Workforce certifications and inspection readiness</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="cursor-pointer transition-shadow hover:shadow-md" onClick={() => navigate(ROUTES.WORKERS)}>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${metrics.workers_with_expired_certs > 0 ? 'bg-[var(--fail-bg)]' : 'bg-[var(--pass-bg)]'}`}>
                    <Users className={`h-5 w-5 ${metrics.workers_with_expired_certs > 0 ? 'text-[var(--fail)]' : 'text-[var(--pass)]'}`} />
                  </div>
                  <div>
                    <p className={`text-2xl font-bold ${metrics.workers_with_expired_certs > 0 ? 'text-[var(--fail)]' : 'text-[var(--pass)]'}`}>
                      {metrics.workers_with_expired_certs}
                    </p>
                    <p className="text-xs text-muted-foreground">Expired Certs</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="cursor-pointer transition-shadow hover:shadow-md" onClick={() => navigate(ROUTES.WORKERS)}>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${metrics.workers_with_expiring_certs > 0 ? 'bg-[var(--warn-bg)]' : 'bg-[var(--pass-bg)]'}`}>
                    <AlertTriangle className={`h-5 w-5 ${metrics.workers_with_expiring_certs > 0 ? 'text-[var(--warn)]' : 'text-[var(--pass)]'}`} />
                  </div>
                  <div>
                    <p className={`text-2xl font-bold ${metrics.workers_with_expiring_certs > 0 ? 'text-[var(--warn)]' : 'text-[var(--pass)]'}`}>
                      {metrics.workers_with_expiring_certs}
                    </p>
                    <p className="text-xs text-muted-foreground">Expiring Soon</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="cursor-pointer transition-shadow hover:shadow-md" onClick={() => navigate(ROUTES.MOCK_INSPECTION)}>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                    metrics.last_mock_score === null
                      ? 'bg-muted'
                      : metrics.last_mock_score >= 75
                        ? 'bg-[var(--pass-bg)]'
                        : metrics.last_mock_score >= 60
                          ? 'bg-[var(--warn-bg)]'
                          : 'bg-[var(--fail-bg)]'
                  }`}>
                    <Shield className={`h-5 w-5 ${
                      metrics.last_mock_score === null
                        ? 'text-muted-foreground'
                        : metrics.last_mock_score >= 75
                          ? 'text-[var(--pass)]'
                          : metrics.last_mock_score >= 60
                            ? 'text-[var(--warn)]'
                            : 'text-[var(--fail)]'
                    }`} />
                  </div>
                  <div>
                    {metrics.last_mock_score !== null ? (
                      <>
                        <p className={`text-2xl font-bold ${
                          metrics.last_mock_score >= 75
                            ? 'text-[var(--pass)]'
                            : metrics.last_mock_score >= 60
                              ? 'text-[var(--warn)]'
                              : 'text-[var(--fail)]'
                        }`}>
                          {metrics.last_mock_score}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Mock Score (Grade: {metrics.last_mock_grade})
                        </p>
                      </>
                    ) : (
                      <>
                        <p className="text-2xl font-bold text-muted-foreground">--</p>
                        <p className="text-xs text-muted-foreground">No Mock Inspection</p>
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <ComplianceRingLarge score={metrics.avg_compliance_score} />
                  <div>
                    <p className="text-xs text-muted-foreground">Avg Compliance</p>
                    <p className="text-xs text-muted-foreground">Across all projects</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="mt-4 flex gap-3">
            <Button
              variant="outline"
              className="border-primary text-[var(--machine-dark)] hover:bg-[var(--machine-wash)]"
              onClick={() => navigate(ROUTES.MOCK_INSPECTION)}
            >
              <Shield className="mr-2 h-4 w-4" />
              Run Mock Inspection
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(ROUTES.CERTIFICATION_MATRIX)}
            >
              <Users className="mr-2 h-4 w-4" />
              View Certification Matrix
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
