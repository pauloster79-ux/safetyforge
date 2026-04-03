import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Loader2,
  Printer,
  Download,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Circle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCertificationMatrix, useWorkers } from '@/hooks/useWorkers';
import { ROUTES, CERTIFICATION_TYPES, WORKER_ROLES, TRADE_TYPES } from '@/lib/constants';

// Subset of most common certs for the matrix view
const MATRIX_CERT_TYPES = [
  'osha_10',
  'osha_30',
  'fall_protection',
  'first_aid_cpr',
  'scaffold_competent',
  'confined_space',
  'excavation_competent',
  'forklift_operator',
  'crane_operator_nccco',
  'aerial_lift',
  'hazcom_ghs',
  'silica_competent',
  'electrical_safety',
  'respiratory_fit_test',
];

function CellIcon({ status }: { status: string }) {
  switch (status) {
    case 'valid':
      return <CheckCircle2 className="h-4 w-4 text-[var(--pass)]" />;
    case 'expiring_soon':
      return <AlertCircle className="h-4 w-4 text-[var(--warn)]" />;
    case 'expired':
      return <XCircle className="h-4 w-4 text-[var(--fail)]" />;
    default:
      return <Circle className="h-3.5 w-3.5 text-muted-foreground" />;
  }
}

export function CertificationMatrixPage() {
  const navigate = useNavigate();
  const { data: matrix, isLoading: matrixLoading } = useCertificationMatrix();
  const { data: workers } = useWorkers();
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [tradeFilter, setTradeFilter] = useState<string>('all');

  const filteredMatrix = matrix?.filter(row => {
    const worker = workers?.find(w => w.id === row.worker_id);
    if (!worker) return true;
    if (roleFilter !== 'all' && worker.role !== roleFilter) return false;
    if (tradeFilter !== 'all' && worker.trade !== tradeFilter) return false;
    return true;
  }) ?? [];

  const getCertShortName = (certId: string) => {
    const ct = CERTIFICATION_TYPES.find(c => c.id === certId);
    if (!ct) return certId;
    // Abbreviate names for column headers
    const shortNames: Record<string, string> = {
      osha_10: 'OSHA 10',
      osha_30: 'OSHA 30',
      fall_protection: 'Fall Prot.',
      first_aid_cpr: 'CPR/AED',
      scaffold_competent: 'Scaffold',
      confined_space: 'Conf. Space',
      excavation_competent: 'Excavation',
      forklift_operator: 'Forklift',
      crane_operator_nccco: 'Crane',
      aerial_lift: 'Aerial Lift',
      hazcom_ghs: 'HazCom',
      silica_competent: 'Silica',
      electrical_safety: 'Electrical',
      respiratory_fit_test: 'Resp. Fit',
    };
    return shortNames[certId] || ct.name;
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="mx-auto max-w-full space-y-6 px-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(ROUTES.WORKERS)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Certification Matrix</h1>
            <p className="text-sm text-muted-foreground">
              Training compliance overview for ISNetworld / GC prequalification
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handlePrint}>
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
          <Button variant="outline" disabled>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 print:hidden">
        <Select value={roleFilter} onValueChange={v => setRoleFilter(v || 'all')}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All Roles" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            {WORKER_ROLES.map(r => (
              <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={tradeFilter} onValueChange={v => setTradeFilter(v || 'all')}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All Trades" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Trades</SelectItem>
            {TRADE_TYPES.map(t => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <CheckCircle2 className="h-4 w-4 text-[var(--pass)]" />
          <span>Valid</span>
        </div>
        <div className="flex items-center gap-1">
          <AlertCircle className="h-4 w-4 text-[var(--warn)]" />
          <span>Expiring Soon</span>
        </div>
        <div className="flex items-center gap-1">
          <XCircle className="h-4 w-4 text-[var(--fail)]" />
          <span>Expired</span>
        </div>
        <div className="flex items-center gap-1">
          <Circle className="h-3.5 w-3.5 text-muted-foreground" />
          <span>Missing</span>
        </div>
      </div>

      {/* Matrix Table */}
      {matrixLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted">
                    <th className="sticky left-0 z-10 min-w-[180px] bg-muted px-4 py-3 text-left font-semibold text-[var(--concrete-600)]">
                      Worker
                    </th>
                    <th className="min-w-[60px] px-2 py-3 text-left font-medium text-muted-foreground">
                      Role
                    </th>
                    {MATRIX_CERT_TYPES.map(certId => (
                      <th
                        key={certId}
                        className="min-w-[70px] px-2 py-3 text-center text-xs font-medium text-muted-foreground"
                      >
                        <span className="block leading-tight">{getCertShortName(certId)}</span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredMatrix.map((row, index) => (
                    <tr
                      key={row.worker_id}
                      className={`cursor-pointer border-b transition-colors hover:bg-muted ${
                        index % 2 === 0 ? '' : 'bg-muted/30'
                      }`}
                      onClick={() => navigate(ROUTES.WORKER_DETAIL(row.worker_id))}
                    >
                      <td className="sticky left-0 z-10 bg-white px-4 py-2.5 font-medium text-foreground">
                        {row.worker_name}
                      </td>
                      <td className="px-2 py-2.5">
                        <Badge variant="secondary" className="text-[10px] capitalize">
                          {WORKER_ROLES.find(r => r.value === row.role)?.label || row.role}
                        </Badge>
                      </td>
                      {MATRIX_CERT_TYPES.map(certId => (
                        <td key={certId} className="px-2 py-2.5 text-center">
                          <div className="flex justify-center">
                            <CellIcon status={row[certId] || 'missing'} />
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filteredMatrix.length === 0 && (
              <div className="py-12 text-center text-sm text-muted-foreground">
                No workers match the current filters
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
