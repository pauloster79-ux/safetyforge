/**
 * SubComplianceCard — rendered for check_sub_compliance / list_subs results.
 *
 * Shows sub name, insurance status, cert status, and performance score.
 */

import { Building2, AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface SubComplianceCardProps {
  result: Record<string, unknown>;
}

export function SubComplianceCard({ result }: SubComplianceCardProps) {
  const subName = (result.sub_name || result.name || 'Sub-contractor') as string;
  const status = (result.compliance_status || result.overall_status || 'unknown') as string;
  const activeWorkers = (result.active_workers ?? '—') as number | string;
  const expiredCerts = (result.expired_certifications ?? 0) as number;
  const insuranceCerts = (result.insurance_certificates ?? 0) as number;
  const passRate = result.inspection_pass_rate as number | null | undefined;
  const issues = (result.issues || []) as string[];

  // For list_subs results which contain an array of subs
  const subs = result.subs as Array<Record<string, unknown>> | undefined;

  const statusColor =
    status === 'compliant' ? 'default' :
    status === 'at_risk' ? 'secondary' :
    status === 'non_compliant' ? 'destructive' : 'outline';

  // If this is a list result, render a summary
  if (subs && Array.isArray(subs)) {
    const total = (result.total ?? subs.length) as number;
    const compliant = (result.compliant_count ?? 0) as number;
    const atRisk = (result.at_risk_count ?? 0) as number;
    const nonCompliant = (result.non_compliant_count ?? 0) as number;

    return (
      <div className="rounded-sm border border-border bg-card p-3">
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-machine-dark" />
          <p className="text-[12px] font-semibold leading-tight">
            Sub-contractors ({total})
          </p>
        </div>

        <div className="mt-2 flex gap-3 text-[10px]">
          <span className="text-pass font-medium">{compliant} compliant</span>
          <span className="text-warn font-medium">{atRisk} at risk</span>
          <span className="text-fail font-medium">{nonCompliant} non-compliant</span>
        </div>

        <div className="mt-2 space-y-1">
          {subs.slice(0, 6).map((sub, i) => {
            const s = sub.compliance_status as string;
            return (
              <div key={i} className="flex items-center justify-between rounded bg-muted/50 px-2 py-1">
                <p className="text-[10px] font-medium">{sub.sub_name as string}</p>
                <Badge
                  variant={s === 'compliant' ? 'default' : s === 'at_risk' ? 'secondary' : 'destructive'}
                  className="text-[8px]"
                >
                  {s.replace(/_/g, ' ')}
                </Badge>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Single sub compliance view
  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-machine-dark" />
          <div>
            <p className="text-[12px] font-semibold leading-tight">{subName}</p>
            <p className="text-[10px] text-muted-foreground">Sub-contractor</p>
          </div>
        </div>
        <Badge variant={statusColor} className="text-[9px] uppercase shrink-0">
          {status.replace(/_/g, ' ')}
        </Badge>
      </div>

      <div className="mt-2.5 grid grid-cols-3 gap-3">
        <div>
          <p className="font-mono text-[9px] text-muted-foreground">Workers</p>
          <p className="text-[12px] font-semibold tabular-nums">{activeWorkers}</p>
        </div>
        <div>
          <p className="font-mono text-[9px] text-muted-foreground">Insurance</p>
          <p className={`text-[12px] font-semibold tabular-nums ${insuranceCerts > 0 ? 'text-pass' : 'text-fail'}`}>
            {insuranceCerts > 0 ? 'On file' : 'Missing'}
          </p>
        </div>
        <div>
          <p className="font-mono text-[9px] text-muted-foreground">Pass rate</p>
          <p className="text-[12px] font-semibold tabular-nums">
            {passRate != null ? `${passRate}%` : '—'}
          </p>
        </div>
      </div>

      {expiredCerts > 0 && (
        <p className="mt-2 flex items-center gap-1 text-[10px] text-fail">
          <AlertTriangle className="h-3 w-3" />
          {expiredCerts} expired certifications
        </p>
      )}

      {issues.length > 0 && (
        <div className="mt-1.5">
          <ul className="space-y-0.5">
            {issues.map((issue, i) => (
              <li key={i} className="text-[10px] text-muted-foreground">&bull; {issue}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
