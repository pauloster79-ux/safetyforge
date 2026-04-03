import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Plus,
  ClipboardCheck,
  Building2,
  Users,
  Activity,
  Shield,
  CheckCircle2,
  Circle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import { useRecentDocuments, useDocumentStats } from '@/hooks/useDocuments';
import { useCompany } from '@/hooks/useCompany';
import { useProjects } from '@/hooks/useProjects';
import { useWorkers, useExpiringCertifications } from '@/hooks/useWorkers';
import { useOsha300Summary } from '@/hooks/useOshaLog';
import { useMorningBrief } from '@/hooks/useMorningBrief';
import { ROUTES, DOCUMENT_TYPES } from '@/lib/constants';
import { format } from 'date-fns';

export function DashboardPage() {
  const navigate = useNavigate();
  useAuth();
  const { data: recentDocs, isLoading: docsLoading } = useRecentDocuments(5);
  const { data: stats } = useDocumentStats();
  const { data: company } = useCompany();
  const { data: projects } = useProjects();
  const { data: allWorkers } = useWorkers();
  const { data: expiringCerts } = useExpiringCertifications(30);
  const { data: oshaSummary } = useOsha300Summary();

  const activeProjects = projects?.filter((p) => p.status === 'active') ?? [];
  const firstProjectId = activeProjects.length > 0 ? activeProjects[0].id : undefined;
  useMorningBrief(firstProjectId);

  const docsThisMonth = stats?.documents_this_month ?? 0;
  const totalDocs = stats?.total_documents ?? 0;
  const maxDocsPerMonth = company?.subscription_status === 'active' ? 50 : 5;
  const usagePercent = Math.min((docsThisMonth / maxDocsPerMonth) * 100, 100);
  const companyName = company?.name || 'Your Company';

  const getDocTypeName = (typeId: string) =>
    DOCUMENT_TYPES.find((t) => t.id === typeId)?.name || typeId;

  const trirColor = (v: number) =>
    v <= 3.0 ? 'text-[var(--pass)]' : v <= 5.0 ? 'text-[var(--warn)]' : 'text-[var(--fail)]';
  const certColor = () => {
    if (expiringCerts?.some(c => c.certification.status === 'expired')) return 'text-[var(--fail)]';
    if ((expiringCerts?.length ?? 0) > 0) return 'text-[var(--warn)]';
    return 'text-foreground';
  };

  return (
    <div className="space-y-4">
      {/* ── Status Strip: scrollable on mobile, flex row on desktop ── */}
      <div className="overflow-x-auto -mx-4 px-4 lg:mx-0 lg:px-0">
        <div className="flex bg-white border border-[var(--border)] min-w-[600px] lg:min-w-0">
          <div className="flex-1 px-3 py-3 border-r border-[var(--border)] lg:px-[18px] lg:py-[14px]">
            <div className="font-mono text-[10px] font-medium uppercase tracking-[1px] text-muted-foreground mb-1">Active Projects</div>
            <div className="text-xl font-bold tracking-tight text-[var(--info)] lg:text-[26px]">{activeProjects.length}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5 truncate">{companyName}</div>
          </div>
          <div className="flex-1 px-3 py-3 border-r border-[var(--border)] lg:px-[18px] lg:py-[14px]">
            <div className="font-mono text-[10px] font-medium uppercase tracking-[1px] text-muted-foreground mb-1">Inspections</div>
            <div className="text-xl font-bold tracking-tight text-foreground lg:text-[26px]">{totalDocs}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">{docsThisMonth} this month</div>
          </div>
          <div className="flex-1 px-3 py-3 border-r border-[var(--border)] cursor-pointer hover:bg-[var(--concrete-50)] lg:px-[18px] lg:py-[14px]" onClick={() => navigate(ROUTES.WORKERS)}>
            <div className="font-mono text-[10px] font-medium uppercase tracking-[1px] text-muted-foreground mb-1">Workers</div>
            <div className="text-xl font-bold tracking-tight text-foreground lg:text-[26px]">{allWorkers?.length ?? 0}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">{expiringCerts?.length ?? 0} alerts</div>
          </div>
          <div className="flex-1 px-3 py-3 border-r border-[var(--border)] cursor-pointer hover:bg-[var(--concrete-50)] lg:px-[18px] lg:py-[14px]" onClick={() => navigate(ROUTES.WORKERS)}>
            <div className="font-mono text-[10px] font-medium uppercase tracking-[1px] text-muted-foreground mb-1">Cert Alerts</div>
            <div className={`text-xl font-bold tracking-tight lg:text-[26px] ${certColor()}`}>{expiringCerts?.length ?? 0}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              {expiringCerts?.filter(c => c.certification.status === 'expired').length ?? 0} expired
            </div>
          </div>
          <div className="flex-1 px-3 py-3 cursor-pointer hover:bg-[var(--concrete-50)] lg:px-[18px] lg:py-[14px]" onClick={() => navigate(ROUTES.OSHA_LOG)}>
            <div className="font-mono text-[10px] font-medium uppercase tracking-[1px] text-muted-foreground mb-1">TRIR</div>
            <div className={`text-xl font-bold tracking-tight lg:text-[26px] ${trirColor(oshaSummary?.trir ?? 0)}`}>
              {oshaSummary?.trir?.toFixed(1) ?? '0.0'}
            </div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              {(oshaSummary?.trir ?? 0) <= 3.0 ? 'Good' : (oshaSummary?.trir ?? 0) <= 5.0 ? 'Caution' : 'High'}
            </div>
          </div>
        </div>
      </div>

      {/* ── Usage bar ── */}
      <div className="flex items-center gap-3 bg-white border border-[var(--border)] px-3 py-2.5 lg:gap-4 lg:px-[18px] lg:py-3">
        <div className="text-[12px] font-medium text-muted-foreground whitespace-nowrap">
          {docsThisMonth}/{maxDocsPerMonth} docs
        </div>
        <div className="flex-1 h-1.5 bg-[var(--border)] overflow-hidden">
          <div
            className={`h-full transition-all ${
              usagePercent >= 90 ? 'bg-[var(--fail)]' : usagePercent >= 70 ? 'bg-[var(--warn)]' : 'bg-[var(--machine)]'
            }`}
            style={{ width: `${usagePercent}%` }}
          />
        </div>
        <div className="font-mono text-[11px] text-muted-foreground">
          {company?.subscription_status === 'active' ? 'Active' : 'Free'}
        </div>
        {company?.subscription_status !== 'active' && (
          <button
            onClick={() => navigate(ROUTES.BILLING)}
            className="text-[11px] font-semibold text-[var(--machine-dark)] hover:underline"
          >
            Upgrade
          </button>
        )}
      </div>

      {/* ── Two column grid: stacks on mobile ── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">

        {/* Left: Recent Documents (checklist style) */}
        <div className="bg-white border border-[var(--border)]">
          <div className="flex items-center justify-between px-3 py-2.5 border-b border-[var(--border)] bg-[var(--concrete-50)] lg:px-[18px]">
            <span className="text-[12px] font-bold uppercase tracking-[0.5px] text-[var(--concrete-700)]">Recent Documents</span>
            <button
              onClick={() => navigate(ROUTES.DOCUMENTS)}
              className="text-[11px] font-semibold text-[var(--machine-dark)] hover:underline"
            >
              View All
            </button>
          </div>

          {docsLoading ? (
            <div className="px-3 py-8 text-center text-[12px] text-muted-foreground lg:px-[18px]">Loading...</div>
          ) : recentDocs && recentDocs.length > 0 ? (
            recentDocs.map((doc) => (
              <button
                key={doc.id}
                onClick={() => navigate(ROUTES.DOCUMENT_EDIT(doc.id))}
                className="flex items-center gap-3 w-full px-3 py-2.5 border-b border-[var(--concrete-50)] hover:bg-[var(--concrete-50)] text-left transition-colors last:border-b-0 lg:px-[18px]"
              >
                <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                  {doc.status === 'final' ? (
                    <CheckCircle2 className="w-[18px] h-[18px] text-[var(--pass)]" />
                  ) : (
                    <Circle className="w-[18px] h-[18px] text-[var(--concrete-300)]" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] font-medium text-[var(--concrete-800)] truncate">{doc.title}</div>
                  <div className="text-[11px] text-muted-foreground truncate">{getDocTypeName(doc.document_type)}</div>
                </div>
                <span className={`font-mono text-[10px] font-semibold uppercase px-1.5 py-0.5 flex-shrink-0 ${
                  doc.status === 'final'
                    ? 'text-[var(--pass)] bg-[var(--pass-bg)]'
                    : 'text-muted-foreground bg-[var(--concrete-50)]'
                }`}>
                  {doc.status === 'final' ? 'Final' : 'Draft'}
                </span>
              </button>
            ))
          ) : (
            <div className="px-3 py-8 text-center lg:px-[18px]">
              <FileText className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-[12px] text-muted-foreground">No documents yet</p>
              <Button className="mt-3" size="sm" onClick={() => navigate(ROUTES.TEMPLATES)}>
                <Plus className="mr-1.5 h-3.5 w-3.5" />
                Create Document
              </Button>
            </div>
          )}
        </div>

        {/* Right: Worker Certifications — simplified columns on mobile */}
        <div className="bg-white border border-[var(--border)]">
          <div className="flex items-center justify-between px-3 py-2.5 border-b border-[var(--border)] bg-[var(--concrete-50)] lg:px-[18px]">
            <span className="text-[12px] font-bold uppercase tracking-[0.5px] text-[var(--concrete-700)]">Certification Status</span>
            <button
              onClick={() => navigate(ROUTES.WORKERS)}
              className="text-[11px] font-semibold text-[var(--machine-dark)] hover:underline"
            >
              Full Matrix
            </button>
          </div>

          {/* Table header — hide Role on mobile */}
          <div className="grid grid-cols-[1fr_70px_60px] px-3 py-1.5 border-b border-[var(--border)] bg-[var(--concrete-50)] lg:grid-cols-[1fr_80px_80px_60px] lg:px-[18px]">
            <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.5px] text-muted-foreground">Worker</span>
            <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.5px] text-muted-foreground hidden lg:block">Role</span>
            <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.5px] text-muted-foreground">Expires</span>
            <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.5px] text-muted-foreground">Status</span>
          </div>

          {expiringCerts && expiringCerts.length > 0 ? (
            expiringCerts.slice(0, 5).map((item) => (
              <div
                key={`${item.worker_id}-${item.certification.certification_type}`}
                className="grid grid-cols-[1fr_70px_60px] items-center px-3 py-2 border-b border-[var(--concrete-50)] last:border-b-0 lg:grid-cols-[1fr_80px_80px_60px] lg:px-[18px]"
              >
                <span className="text-[13px] font-semibold text-[var(--concrete-800)] truncate">{item.worker_name}</span>
                <span className="text-[12px] text-muted-foreground truncate hidden lg:block">{'—'}</span>
                <span className="font-mono text-[11px] text-[var(--concrete-500)]">
                  {item.certification.expiry_date
                    ? format(new Date(item.certification.expiry_date), 'MMM d')
                    : '—'}
                </span>
                <span className={`font-mono text-[10px] font-semibold uppercase px-1.5 py-0.5 ${
                  item.certification.status === 'expired'
                    ? 'text-[var(--fail)] bg-[var(--fail-bg)]'
                    : item.certification.status === 'expiring_soon'
                      ? 'text-[var(--warn)] bg-[var(--warn-bg)]'
                      : 'text-[var(--pass)] bg-[var(--pass-bg)]'
                }`}>
                  {item.certification.status === 'expired'
                    ? 'Expired'
                    : item.certification.status === 'expiring_soon'
                      ? 'Soon'
                      : 'Valid'}
                </span>
              </div>
            ))
          ) : allWorkers && allWorkers.length > 0 ? (
            allWorkers.slice(0, 5).map((worker) => (
              <div
                key={worker.id}
                className="grid grid-cols-[1fr_70px_60px] items-center px-3 py-2 border-b border-[var(--concrete-50)] last:border-b-0 lg:grid-cols-[1fr_80px_80px_60px] lg:px-[18px]"
              >
                <span className="text-[13px] font-semibold text-[var(--concrete-800)] truncate">
                  {worker.first_name} {worker.last_name}
                </span>
                <span className="text-[12px] text-muted-foreground truncate hidden lg:block">{worker.role || '—'}</span>
                <span className="font-mono text-[11px] text-[var(--concrete-500)]">—</span>
                <span className="font-mono text-[10px] font-semibold uppercase text-[var(--pass)] bg-[var(--pass-bg)] px-1.5 py-0.5">Valid</span>
              </div>
            ))
          ) : (
            <div className="px-3 py-8 text-center lg:px-[18px]">
              <Users className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-[12px] text-muted-foreground">No workers added</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Active Projects ── */}
      {activeProjects.length > 0 && (
        <div className="bg-white border border-[var(--border)]">
          <div className="flex items-center justify-between px-3 py-2.5 border-b border-[var(--border)] bg-[var(--concrete-50)] lg:px-[18px]">
            <span className="text-[12px] font-bold uppercase tracking-[0.5px] text-[var(--concrete-700)]">Active Projects</span>
            <button
              onClick={() => navigate(ROUTES.PROJECTS)}
              className="text-[11px] font-semibold text-[var(--machine-dark)] hover:underline"
            >
              View All
            </button>
          </div>
          {activeProjects.slice(0, 5).map((project) => (
            <button
              key={project.id}
              onClick={() => navigate(ROUTES.PROJECT_DETAIL(project.id))}
              className="flex items-center gap-3 w-full px-3 py-2.5 border-b border-[var(--concrete-50)] hover:bg-[var(--concrete-50)] text-left transition-colors last:border-b-0 lg:px-[18px]"
            >
              <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                project.compliance_score >= 80 ? 'bg-[var(--pass)]' :
                project.compliance_score >= 60 ? 'bg-[var(--warn)]' : 'bg-[var(--fail)]'
              }`} />
              <div className="flex-1 min-w-0">
                <div className="text-[13px] font-medium text-[var(--concrete-800)] truncate">{project.name}</div>
                <div className="text-[11px] text-muted-foreground truncate">{project.address}</div>
              </div>
              <span className="font-mono text-[11px] font-semibold text-[var(--concrete-500)] flex-shrink-0">
                {project.compliance_score}%
              </span>
              <span className={`font-mono text-[10px] font-semibold uppercase px-1.5 py-0.5 flex-shrink-0 ${
                project.compliance_score >= 80
                  ? 'text-[var(--pass)] bg-[var(--pass-bg)]'
                  : project.compliance_score >= 60
                    ? 'text-[var(--warn)] bg-[var(--warn-bg)]'
                    : 'text-[var(--fail)] bg-[var(--fail-bg)]'
              }`}>
                {project.status === 'active' ? 'Active' : project.status === 'on_hold' ? 'Hold' : 'Done'}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* ── Quick Actions: wrap on mobile ── */}
      <div className="flex flex-wrap gap-2 lg:gap-3">
        <Button size="sm" onClick={() => {
          if (activeProjects.length > 0) navigate(ROUTES.INSPECTION_NEW(activeProjects[0].id));
          else navigate(ROUTES.PROJECT_NEW);
        }}>
          <ClipboardCheck className="mr-1.5 h-3.5 w-3.5" />
          New Inspection
        </Button>
        <Button variant="outline" size="sm" onClick={() => navigate(ROUTES.DOCUMENT_NEW)}>
          <FileText className="mr-1.5 h-3.5 w-3.5" />
          New Document
        </Button>
        <Button variant="outline" size="sm" onClick={() => navigate(ROUTES.PROJECT_NEW)}>
          <Building2 className="mr-1.5 h-3.5 w-3.5" />
          New Project
        </Button>
        <Button variant="outline" size="sm" className="hidden sm:flex" onClick={() => navigate(ROUTES.MOCK_INSPECTION)}>
          <Shield className="mr-1.5 h-3.5 w-3.5" />
          Mock Inspection
        </Button>
        <Button variant="outline" size="sm" className="hidden sm:flex" onClick={() => navigate(ROUTES.ANALYTICS)}>
          <Activity className="mr-1.5 h-3.5 w-3.5" />
          Analytics
        </Button>
      </div>
    </div>
  );
}
