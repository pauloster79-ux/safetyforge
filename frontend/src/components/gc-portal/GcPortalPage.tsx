import { useState } from 'react';
import {
  Building2,
  Users,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Send,
  ChevronRight,
  Eye,
  ClipboardCheck,
  MessageSquare,
  GraduationCap,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useGcDashboard, useMyGcs, useInviteSub } from '@/hooks/useGcPortal';
import { ComplianceRing } from '@/components/projects/ComplianceRing';
import type { SubComplianceSummary } from '@/lib/constants';

function OverallStatusBadge({ status }: { status: SubComplianceSummary['overall_status'] }) {
  const config = {
    compliant: { label: 'Compliant', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    at_risk: { label: 'At Risk', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
    non_compliant: { label: 'Non-Compliant', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
  };
  const { label, className } = config[status];
  return <Badge className={className}>{label}</Badge>;
}

function ComplianceIndicator({ label, current }: { label: string; current: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      {current ? (
        <CheckCircle2 className="h-4 w-4 text-[var(--pass)]" />
      ) : (
        <XCircle className="h-4 w-4 text-[var(--fail)]" />
      )}
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  );
}

function SubDetailView({ sub }: { sub: SubComplianceSummary }) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border p-4 text-center">
          <p className="text-xs text-muted-foreground">EMR</p>
          <p className={`text-2xl font-bold ${sub.emr && sub.emr <= 1.0 ? 'text-[var(--pass)]' : 'text-[var(--warn)]'}`}>
            {sub.emr?.toFixed(2) ?? '--'}
          </p>
        </div>
        <div className="rounded-lg border p-4 text-center">
          <p className="text-xs text-muted-foreground">TRIR</p>
          <p className={`text-2xl font-bold ${sub.trir && sub.trir <= 3.0 ? 'text-[var(--pass)]' : 'text-[var(--fail)]'}`}>
            {sub.trir?.toFixed(1) ?? '--'}
          </p>
        </div>
        <div className="rounded-lg border p-4 text-center">
          <p className="text-xs text-muted-foreground">Mock Inspection</p>
          <p className={`text-2xl font-bold ${
            sub.mock_inspection_score !== null
              ? sub.mock_inspection_score >= 75 ? 'text-[var(--pass)]' : sub.mock_inspection_score >= 60 ? 'text-[var(--warn)]' : 'text-[var(--fail)]'
              : 'text-muted-foreground'
          }`}>
            {sub.mock_inspection_score !== null ? `${sub.mock_inspection_score} (${sub.mock_inspection_grade})` : '--'}
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border p-4">
          <p className="text-sm font-medium text-[var(--concrete-600)]">Workforce</p>
          <div className="mt-2 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Active Workers</span>
              <span className="text-sm font-medium text-[var(--concrete-600)]">{sub.active_workers}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Expired Certifications</span>
              <span className={`text-sm font-medium ${sub.expired_certifications > 0 ? 'text-[var(--fail)]' : 'text-[var(--pass)]'}`}>
                {sub.expired_certifications}
              </span>
            </div>
          </div>
        </div>
        <div className="rounded-lg border p-4">
          <p className="text-sm font-medium text-[var(--concrete-600)]">Activity</p>
          <div className="mt-2 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Last Inspection</span>
              <span className="text-sm text-[var(--concrete-600)]">{sub.last_inspection_date ?? 'None'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Last Toolbox Talk</span>
              <span className="text-sm text-[var(--concrete-600)]">{sub.last_toolbox_talk_date ?? 'None'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function InviteSubDialog() {
  const [email, setEmail] = useState('');
  const [projectName, setProjectName] = useState('');
  const [open, setOpen] = useState(false);
  const inviteSub = useInviteSub();

  const handleInvite = async () => {
    await inviteSub.mutateAsync({ email, project_name: projectName });
    setEmail('');
    setProjectName('');
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button className="bg-primary hover:bg-[var(--machine-dark)]">
            <Send className="mr-2 h-4 w-4" />
            Invite Subcontractor
          </Button>
        }
      />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite Subcontractor</DialogTitle>
          <DialogDescription>
            Send an invitation to a subcontractor to connect their SafetyForge account.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Subcontractor Email</Label>
            <Input
              placeholder="sub@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Project Name</Label>
            <Input
              placeholder="e.g., Riverside Commercial Complex"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            disabled={!email || !projectName || inviteSub.isPending}
            onClick={handleInvite}
          >
            {inviteSub.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Send className="mr-2 h-4 w-4" />
            )}
            Send Invite
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function AsGcView() {
  const { data: dashboard, isLoading } = useGcDashboard();
  const [expandedSub, setExpandedSub] = useState<string | null>(null);

  if (isLoading || !dashboard) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const { relationships, compliance } = dashboard;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{relationships.length} subcontractor{relationships.length !== 1 ? 's' : ''} connected</p>
        <InviteSubDialog />
      </div>

      {relationships.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12 text-center">
            <Users className="h-12 w-12 text-muted-foreground" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">No subcontractors connected</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Invite subcontractors to monitor their safety compliance in real-time
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {relationships.map((rel) => {
            const sub = compliance.find(c => c.sub_company_id === rel.sub_company_id);
            const isExpanded = expandedSub === rel.sub_company_id;

            return (
              <Card key={rel.id}>
                <CardContent className="pt-6">
                  <button
                    className="flex w-full items-center gap-4 text-left"
                    onClick={() => setExpandedSub(isExpanded ? null : rel.sub_company_id)}
                  >
                    <ComplianceRing score={sub?.compliance_score ?? 0} size="md" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-foreground">
                          {rel.sub_company_name}
                        </p>
                        {sub && <OverallStatusBadge status={sub.overall_status} />}
                      </div>
                      <p className="text-xs text-muted-foreground">{rel.project_name}</p>
                      {sub && (
                        <div className="mt-2 flex flex-wrap gap-4">
                          <ComplianceIndicator label="Inspections" current={sub.inspection_current} />
                          <ComplianceIndicator label="Training" current={sub.training_current} />
                          <ComplianceIndicator label="Talks" current={sub.talks_current} />
                          {sub.expired_certifications > 0 && (
                            <div className="flex items-center gap-1.5">
                              <AlertTriangle className="h-4 w-4 text-[var(--fail)]" />
                              <span className="text-xs text-[var(--fail)]">{sub.expired_certifications} expired certs</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    <ChevronRight className={`h-5 w-5 text-muted-foreground transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                  </button>

                  {isExpanded && sub && (
                    <>
                      <Separator className="my-4" />
                      <SubDetailView sub={sub} />
                    </>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

function AsSubView() {
  const { data: gcs, isLoading } = useMyGcs();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="border-[var(--info)] bg-gradient-to-r from-[var(--info-bg)] to-[var(--info-bg)]">
        <CardContent className="py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--info-bg)]">
              <Eye className="h-5 w-5 text-[var(--info)]" />
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">This is what your GCs see</p>
              <p className="text-xs text-muted-foreground">
                Connected general contractors can view your compliance score, certifications, inspections, and toolbox talk history.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {(!gcs || gcs.length === 0) ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12 text-center">
            <Building2 className="h-12 w-12 text-muted-foreground" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">No GC connections</p>
            <p className="mt-1 text-xs text-muted-foreground">
              When a general contractor invites you, their connection will appear here.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {gcs.map((gc) => (
            <Card key={gc.id}>
              <CardContent className="flex items-center gap-4 pt-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                  <Building2 className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-[var(--concrete-600)]">{gc.gc_company_name}</p>
                  <p className="text-xs text-muted-foreground">{gc.project_name}</p>
                </div>
                <Badge className={
                  gc.status === 'active'
                    ? 'ml-auto bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]'
                    : gc.status === 'pending'
                      ? 'ml-auto bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]'
                      : 'ml-auto bg-muted text-muted-foreground hover:bg-muted'
                }>
                  {gc.status.charAt(0).toUpperCase() + gc.status.slice(1)}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* What GCs can see */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Shared Data</CardTitle>
          <CardDescription>Information visible to your connected GCs</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { icon: ClipboardCheck, label: 'Inspection History', desc: 'Recent inspections and pass rates' },
              { icon: MessageSquare, label: 'Toolbox Talk Records', desc: 'Frequency and attendance' },
              { icon: GraduationCap, label: 'Certification Status', desc: 'Worker certifications and expiration dates' },
              { icon: AlertTriangle, label: 'Safety Metrics', desc: 'TRIR, DART, EMR, compliance scores' },
            ].map(({ icon: Icon, label, desc }) => (
              <div key={label} className="flex items-start gap-3 rounded-lg border p-3">
                <Icon className="mt-0.5 h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium text-[var(--concrete-600)]">{label}</p>
                  <p className="text-xs text-muted-foreground">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function GcPortalPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">GC / Sub Portal</h1>
        <p className="text-sm text-muted-foreground">
          Monitor subcontractor safety compliance and manage GC relationships
        </p>
      </div>

      <Tabs defaultValue="gc">
        <TabsList>
          <TabsTrigger value="gc">As GC</TabsTrigger>
          <TabsTrigger value="sub">As Sub</TabsTrigger>
        </TabsList>
        <TabsContent value="gc" className="mt-4">
          <AsGcView />
        </TabsContent>
        <TabsContent value="sub" className="mt-4">
          <AsSubView />
        </TabsContent>
      </Tabs>
    </div>
  );
}
