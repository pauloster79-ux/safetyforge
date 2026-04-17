/**
 * ComplianceStatusCard — rendered for check_worker_compliance / check_project_compliance results.
 *
 * Shows compliance status, expired certifications, worker count.
 */

import { Shield, AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ComplianceStatusCardProps {
  result: Record<string, unknown>;
}

export function ComplianceStatusCard({ result }: ComplianceStatusCardProps) {
  // Tools return `compliant` (boolean), not `compliance_status` (string)
  const compliant = result.compliant;
  const status = compliant === true
    ? 'compliant'
    : compliant === false
      ? 'non-compliant'
      : (result.overall_status || result.status || 'unknown') as string;

  const isCompliant = status === 'compliant' || status === 'pass';
  const entityName = (result.worker_name || result.project_name || result.name || '') as string;

  // Tools return `expired_certifications` — array for worker, integer for project
  const expiredRaw = result.expired_certifications;
  const expiredCerts: Array<Record<string, unknown>> = Array.isArray(expiredRaw)
    ? expiredRaw
    : [];
  const expiredCount = typeof expiredRaw === 'number'
    ? expiredRaw
    : expiredCerts.length;

  // Worker compliance includes valid_certifications
  const validCount = typeof result.valid_certifications === 'number'
    ? result.valid_certifications
    : Array.isArray(result.valid_certifications)
      ? result.valid_certifications.length
      : null;

  // Project compliance includes workers_checked / compliant_workers
  const workersChecked = result.workers_checked as number | undefined;
  const compliantWorkers = result.compliant_workers as number | undefined;

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Shield className={`h-4 w-4 ${isCompliant ? 'text-pass' : 'text-fail'}`} />
          <div>
            <p className="text-[12px] font-semibold leading-tight">Compliance Check</p>
            {entityName && <p className="text-[10px] text-muted-foreground">{entityName}</p>}
          </div>
        </div>
        <Badge
          variant={isCompliant ? 'default' : 'destructive'}
          className="text-[9px] uppercase shrink-0"
        >
          {status.replace(/_/g, ' ')}
        </Badge>
      </div>

      {/* Worker/project stats */}
      {(workersChecked != null || validCount != null) && (
        <div className="mt-2 flex gap-3 text-[10px]">
          {workersChecked != null && (
            <span className="text-muted-foreground">
              {compliantWorkers ?? 0}/{workersChecked} workers compliant
            </span>
          )}
          {validCount != null && (
            <span className="text-muted-foreground">
              {validCount} valid certs
            </span>
          )}
        </div>
      )}

      {/* Expired certifications */}
      {expiredCount > 0 && (
        <div className="mt-2">
          <p className="flex items-center gap-1 text-[10px] font-medium text-fail">
            <AlertTriangle className="h-3 w-3" />
            Expired ({expiredCount})
          </p>
          {expiredCerts.length > 0 && (
            <ul className="mt-0.5 space-y-0.5">
              {expiredCerts.slice(0, 4).map((cert, i) => (
                <li key={i} className="text-[10px] text-muted-foreground">
                  &bull; {String(cert.certification_type || cert.name || cert.type || JSON.stringify(cert))}
                  {!!cert.expired_at && <span className="ml-1 font-mono text-[9px]">(exp {String(cert.expired_at).slice(0, 10)})</span>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
