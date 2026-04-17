/**
 * LeadCard — rendered for capture_lead / qualify_project tool results.
 *
 * Shows project name, type, client, address, and qualification status.
 */

import { Target, MapPin, User } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface LeadCardProps {
  result: Record<string, unknown>;
}

export function LeadCard({ result }: LeadCardProps) {
  const name = (result.project_name || result.name || 'Untitled Lead') as string;
  const status = (result.qualification_status || result.status || 'lead') as string;
  const projectType = result.project_type as string | undefined;
  const clientName = (result.client_name || result.client) as string | undefined;
  const address = result.address as string | undefined;
  const issues = (result.issues || []) as string[];
  const strengths = (result.strengths || []) as string[];

  const statusColor =
    status === 'qualified' ? 'default' :
    status === 'at_risk' ? 'secondary' :
    status === 'not_qualified' ? 'destructive' : 'outline';

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-machine-dark" />
          <div>
            <p className="text-[12px] font-semibold leading-tight">{name}</p>
            {projectType && (
              <p className="text-[10px] text-muted-foreground">{projectType}</p>
            )}
          </div>
        </div>
        <Badge variant={statusColor} className="text-[9px] uppercase shrink-0">
          {status.replace(/_/g, ' ')}
        </Badge>
      </div>

      <div className="mt-2 space-y-1">
        {clientName && (
          <div className="flex items-center gap-1.5">
            <User className="h-3 w-3 text-muted-foreground" />
            <p className="text-[10px] text-muted-foreground">{clientName}</p>
          </div>
        )}
        {address && (
          <div className="flex items-center gap-1.5">
            <MapPin className="h-3 w-3 text-muted-foreground" />
            <p className="text-[10px] text-muted-foreground">{address}</p>
          </div>
        )}
      </div>

      {issues.length > 0 && (
        <div className="mt-2">
          <p className="text-[10px] font-medium text-fail">Issues ({issues.length})</p>
          <ul className="mt-0.5 space-y-0.5">
            {issues.slice(0, 3).map((issue, i) => (
              <li key={i} className="text-[10px] text-muted-foreground">&bull; {issue}</li>
            ))}
          </ul>
        </div>
      )}

      {strengths.length > 0 && (
        <div className="mt-2">
          <p className="text-[10px] font-medium text-pass">Strengths ({strengths.length})</p>
          <ul className="mt-0.5 space-y-0.5">
            {strengths.slice(0, 3).map((s, i) => (
              <li key={i} className="text-[10px] text-muted-foreground">&bull; {s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
