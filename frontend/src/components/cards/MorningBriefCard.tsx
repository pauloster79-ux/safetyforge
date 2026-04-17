/**
 * MorningBriefCard — rendered for generate_morning_brief tool results.
 *
 * Shows alerts with severity, summary text, project context.
 */

import { Sun, AlertTriangle, Info, AlertCircle } from 'lucide-react';

interface MorningBriefCardProps {
  result: Record<string, unknown>;
}

export function MorningBriefCard({ result }: MorningBriefCardProps) {
  const alerts = (result.alerts || result.critical_alerts || []) as Array<Record<string, unknown>>;
  const projectName = (result.project_name || '') as string;
  const summary = (result.summary || '') as string;
  const riskScore = result.risk_score ?? result.risk_level;

  // Group alerts by severity
  const highAlerts = alerts.filter(a => a.severity === 'high' || a.severity === 'critical');
  const mediumAlerts = alerts.filter(a => a.severity === 'medium');
  const lowAlerts = alerts.filter(a => a.severity === 'low' || a.severity === 'info');

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Sun className="h-4 w-4 text-machine-dark" />
          <div>
            <p className="text-[12px] font-semibold leading-tight">Morning Brief</p>
            {projectName && <p className="text-[10px] text-muted-foreground">{projectName}</p>}
          </div>
        </div>
        {riskScore != null && (
          <span className="font-mono text-[10px] font-semibold text-muted-foreground">
            Risk: {String(riskScore)}
          </span>
        )}
      </div>

      {summary && (
        <p className="mt-2 text-[10px] text-muted-foreground leading-relaxed">{summary}</p>
      )}

      {/* High-severity alerts */}
      {highAlerts.length > 0 && (
        <div className="mt-2">
          <p className="flex items-center gap-1 text-[10px] font-semibold text-fail">
            <AlertTriangle className="h-3 w-3" />
            Critical ({highAlerts.length})
          </p>
          <ul className="mt-0.5 space-y-0.5">
            {highAlerts.slice(0, 3).map((a, i) => (
              <li key={i} className="text-[10px] text-muted-foreground">
                &bull; {String(a.message || a.description || JSON.stringify(a))}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Medium-severity alerts */}
      {mediumAlerts.length > 0 && (
        <div className="mt-2">
          <p className="flex items-center gap-1 text-[10px] font-semibold text-warn">
            <AlertCircle className="h-3 w-3" />
            Warnings ({mediumAlerts.length})
          </p>
          <ul className="mt-0.5 space-y-0.5">
            {mediumAlerts.slice(0, 3).map((a, i) => (
              <li key={i} className="text-[10px] text-muted-foreground">
                &bull; {String(a.message || a.description || JSON.stringify(a))}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Info alerts */}
      {lowAlerts.length > 0 && (
        <div className="mt-2">
          <p className="flex items-center gap-1 text-[10px] font-semibold text-foreground">
            <Info className="h-3 w-3 text-muted-foreground" />
            Info ({lowAlerts.length})
          </p>
          <ul className="mt-0.5 space-y-0.5">
            {lowAlerts.slice(0, 3).map((a, i) => (
              <li key={i} className="text-[10px] text-muted-foreground">
                &bull; {String(a.message || a.description || JSON.stringify(a))}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
