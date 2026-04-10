import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Users,
  Search,
  Loader2,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Shield,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useWorkers, useExpiringCertifications } from '@/hooks/useWorkers';
import { ROUTES, WORKER_ROLES, TRADE_TYPES, CERTIFICATION_TYPES } from '@/lib/constants';
import type { Worker } from '@/lib/constants';

function WorkerStatusBadge({ status }: { status: Worker['status'] }) {
  const config = {
    active: { label: 'Active', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    inactive: { label: 'Inactive', className: 'bg-muted text-muted-foreground hover:bg-muted' },
    terminated: { label: 'Terminated', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
  };
  const { label, className } = config[status];
  return <Badge className={className}>{label}</Badge>;
}

function RoleBadge({ role }: { role: string }) {
  const roleLabel = WORKER_ROLES.find(r => r.value === role)?.label || role;
  return <Badge variant="secondary" className="text-xs capitalize">{roleLabel}</Badge>;
}

function LanguageFlag({ pref }: { pref: 'en' | 'es' | 'both' }) {
  if (pref === 'en') return <span className="text-xs" title="English">EN</span>;
  if (pref === 'es') return <span className="text-xs" title="Spanish">ES</span>;
  return <span className="text-xs" title="Bilingual">EN/ES</span>;
}

function CertHealthIndicator({ worker }: { worker: Worker }) {
  if (worker.expired > 0) {
    return (
      <div className="flex items-center gap-1.5 text-xs">
        <span className="text-[var(--pass)]">{worker.total_certifications - worker.expired - worker.expiring_soon}</span>
        {worker.expiring_soon > 0 && <span className="text-[var(--warn)]">{worker.expiring_soon} exp. soon</span>}
        <span className="font-medium text-[var(--fail)]">{worker.expired} expired</span>
        <div className="h-2.5 w-2.5 rounded-full bg-[var(--fail)]" />
      </div>
    );
  }
  if (worker.expiring_soon > 0) {
    return (
      <div className="flex items-center gap-1.5 text-xs">
        <span className="text-[var(--pass)]">{worker.total_certifications - worker.expiring_soon} valid</span>
        <span className="font-medium text-[var(--warn)]">{worker.expiring_soon} exp. soon</span>
        <div className="h-2.5 w-2.5 rounded-full bg-[var(--warn)]" />
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span className="text-[var(--pass)]">{worker.total_certifications} certs</span>
      <div className="h-2.5 w-2.5 rounded-full bg-[var(--pass)]" />
    </div>
  );
}

export function WorkerListPage() {
  const navigate = useNavigate();
  const [roleFilter, setRoleFilter] = useState<string>('All Roles');
  const [tradeFilter, setTradeFilter] = useState<string>('All Trades');
  const [statusFilter, setStatusFilter] = useState<string>('All Status');
  const [searchQuery, setSearchQuery] = useState('');
  const [alertsExpanded, setAlertsExpanded] = useState(false);

  const params: Record<string, string> = {};
  if (!statusFilter.startsWith('All')) params.status = statusFilter;
  if (!roleFilter.startsWith('All')) params.role = roleFilter;
  if (!tradeFilter.startsWith('All')) params.trade = tradeFilter;
  if (searchQuery) params.search = searchQuery;

  const { data: workers, isLoading } = useWorkers(
    Object.keys(params).length > 0 ? params : undefined
  );

  const { data: expiringCerts } = useExpiringCertifications(30);

  const expiringSoon = expiringCerts?.filter(c => c.certification.status === 'expiring_soon') ?? [];
  const expired = expiringCerts?.filter(c => c.certification.status === 'expired') ?? [];

  const getCertTypeName = (typeId: string) =>
    CERTIFICATION_TYPES.find(ct => ct.id === typeId)?.name || typeId;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Workers</h1>
          <p className="text-sm text-muted-foreground">
            Manage your crew and track certifications
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => navigate(ROUTES.CERTIFICATION_MATRIX)}
          >
            <Shield className="mr-2 h-4 w-4" />
            Cert Matrix
          </Button>
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => navigate(ROUTES.WORKER_NEW)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Worker
          </Button>
        </div>
      </div>

      {/* Certification Alerts */}
      {(expired.length > 0 || expiringSoon.length > 0) && (
        <div className="space-y-2">
          {expired.length > 0 && (
            <div className="rounded-lg border border-[var(--fail)] bg-[var(--fail-bg)] p-4">
              <button
                className="flex w-full items-center justify-between text-left"
                onClick={() => setAlertsExpanded(prev => !prev)}
              >
                <div className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-[var(--fail)]" />
                  <span className="font-medium text-[var(--fail)]">
                    {expired.length} expired certification{expired.length !== 1 ? 's' : ''}
                  </span>
                </div>
                {alertsExpanded ? (
                  <ChevronUp className="h-4 w-4 text-[var(--fail)]" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-[var(--fail)]" />
                )}
              </button>
              {alertsExpanded && (
                <div className="mt-3 space-y-1">
                  {expired.map((item, i) => (
                    <button
                      key={i}
                      className="flex w-full items-center gap-2 rounded p-1.5 text-left text-sm text-[var(--fail)] hover:bg-[var(--fail-bg)]"
                      onClick={() => navigate(ROUTES.WORKER_DETAIL(item.worker_id))}
                    >
                      <span className="font-medium">{item.worker_name}</span>
                      <span className="text-[var(--fail)]">-</span>
                      <span>{getCertTypeName(item.certification.certification_type)}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          {expiringSoon.length > 0 && (
            <div className="rounded-lg border border-[var(--warn)] bg-[var(--warn-bg)] p-4">
              <button
                className="flex w-full items-center justify-between text-left"
                onClick={() => setAlertsExpanded(prev => !prev)}
              >
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-[var(--warn)]" />
                  <span className="font-medium text-[var(--warn)]">
                    {expiringSoon.length} certification{expiringSoon.length !== 1 ? 's' : ''} expiring in the next 30 days
                  </span>
                </div>
                {alertsExpanded ? (
                  <ChevronUp className="h-4 w-4 text-[var(--warn)]" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-[var(--warn)]" />
                )}
              </button>
              {alertsExpanded && (
                <div className="mt-3 space-y-1">
                  {expiringSoon.map((item, i) => (
                    <button
                      key={i}
                      className="flex w-full items-center gap-2 rounded p-1.5 text-left text-sm text-[var(--warn)] hover:bg-[var(--warn-bg)]"
                      onClick={() => navigate(ROUTES.WORKER_DETAIL(item.worker_id))}
                    >
                      <span className="font-medium">{item.worker_name}</span>
                      <span className="text-[var(--warn)]">-</span>
                      <span>{getCertTypeName(item.certification.certification_type)}</span>
                      {item.certification.expiry_date && (
                        <span className="text-xs text-[var(--warn)]">
                          (exp. {item.certification.expiry_date})
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 sm:max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search workers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Select value={roleFilter} onValueChange={(v) => setRoleFilter(v || 'All')}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All Roles" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="All Roles">All Roles</SelectItem>
            {WORKER_ROLES.map(r => (
              <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={tradeFilter} onValueChange={(v) => setTradeFilter(v || 'All')}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All Trades" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="All Trades">All Trades</SelectItem>
            {TRADE_TYPES.map(t => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v || 'All')}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="All Status">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="terminated">Terminated</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Workers List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : workers && workers.length > 0 ? (
        <div className="space-y-3">
          {workers.map((worker) => (
            <Card
              key={worker.id}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => navigate(ROUTES.WORKER_DETAIL(worker.id))}
            >
              <CardContent className="flex items-center gap-4 py-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted text-sm font-semibold text-muted-foreground">
                  {worker.first_name[0]}{worker.last_name[0]}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-foreground">
                      {worker.first_name} {worker.last_name}
                    </p>
                    <RoleBadge role={worker.role} />
                    <WorkerStatusBadge status={worker.status} />
                  </div>
                  <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="capitalize">{worker.trade.replace('_', ' ')}</span>
                    <LanguageFlag pref={worker.language_preference} />
                  </div>
                </div>
                <CertHealthIndicator worker={worker} />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <Users className="h-16 w-16 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium text-muted-foreground">No workers yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Add your first crew member to start tracking certifications
          </p>
          <Button
            className="mt-4 bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => navigate(ROUTES.WORKER_NEW)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Worker
          </Button>
        </div>
      )}
    </div>
  );
}
