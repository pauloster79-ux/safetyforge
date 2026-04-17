/**
 * SubPerformanceCard — rendered for get_sub_performance tool results.
 *
 * Shows performance score, pass rates, incident rate, response times.
 */

import { TrendingUp, Shield, AlertTriangle, CheckCircle } from 'lucide-react';

interface SubPerformanceCardProps {
  result: Record<string, unknown>;
}

export function SubPerformanceCard({ result }: SubPerformanceCardProps) {
  const subName = (result.sub_name || 'Sub-contractor') as string;
  const score = (result.performance_score ?? 0) as number;
  const passRate = result.inspection_pass_rate as number | null | undefined;
  const totalInspections = (result.total_inspections ?? 0) as number;
  const totalIncidents = (result.total_incidents ?? 0) as number;
  const criticalIncidents = (result.critical_incidents ?? 0) as number;
  const openIncidents = (result.open_incidents ?? 0) as number;
  const caClosureRate = result.corrective_action_closure_rate as number | null | undefined;

  const scoreColor =
    score >= 80 ? 'text-pass' :
    score >= 60 ? 'text-warn' : 'text-fail';

  const scoreBarColor =
    score >= 80 ? 'bg-pass' :
    score >= 60 ? 'bg-warn' : 'bg-fail';

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-machine-dark" />
          <div>
            <p className="text-[12px] font-semibold leading-tight">{subName}</p>
            <p className="text-[10px] text-muted-foreground">Performance</p>
          </div>
        </div>
        <span className={`text-[16px] font-bold tabular-nums ${scoreColor}`}>
          {score}
        </span>
      </div>

      <div className="mt-2">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div className={`h-full rounded-full ${scoreBarColor}`} style={{ width: `${score}%` }} />
        </div>
      </div>

      <div className="mt-2.5 grid grid-cols-2 gap-2">
        <div className="flex items-center gap-1.5">
          <Shield className="h-3 w-3 text-muted-foreground" />
          <div>
            <p className="font-mono text-[9px] text-muted-foreground">Pass rate</p>
            <p className="text-[11px] font-semibold tabular-nums">
              {passRate != null ? `${passRate}%` : '—'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <AlertTriangle className="h-3 w-3 text-muted-foreground" />
          <div>
            <p className="font-mono text-[9px] text-muted-foreground">Incidents</p>
            <p className="text-[11px] font-semibold tabular-nums">
              {totalIncidents}
              {criticalIncidents > 0 && (
                <span className="text-fail"> ({criticalIncidents} crit)</span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <CheckCircle className="h-3 w-3 text-muted-foreground" />
          <div>
            <p className="font-mono text-[9px] text-muted-foreground">CA closure</p>
            <p className="text-[11px] font-semibold tabular-nums">
              {caClosureRate != null ? `${caClosureRate}%` : '—'}
            </p>
          </div>
        </div>
        <div>
          <p className="font-mono text-[9px] text-muted-foreground">Inspections</p>
          <p className="text-[11px] font-semibold tabular-nums">{totalInspections}</p>
        </div>
      </div>

      {openIncidents > 0 && (
        <p className="mt-2 flex items-center gap-1 text-[10px] text-warn">
          <AlertTriangle className="h-3 w-3" />
          {openIncidents} open incidents
        </p>
      )}
    </div>
  );
}
