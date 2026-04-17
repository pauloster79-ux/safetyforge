/**
 * QualityCard — rendered for quality observation tool results.
 *
 * Shows inspection date, category, pass/fail, score.
 */

import { Eye, CheckCircle, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface QualityCardProps {
  result: Record<string, unknown>;
}

export function QualityCard({ result }: QualityCardProps) {
  const status = (result.status || result.result || result.overall_status || 'unknown') as string;
  const description = (result.description || '') as string;
  const location = (result.location || '') as string;
  const score = result.score ?? result.compliance_score;
  const date = (result.date || result.created_at || '') as string;
  const category = (result.category || 'quality') as string;

  const passed = ['pass', 'passed', 'compliant'].includes(status.toLowerCase());

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          {passed ? (
            <CheckCircle className="h-4 w-4 text-pass" />
          ) : (
            <XCircle className="h-4 w-4 text-fail" />
          )}
          <div>
            <p className="text-[12px] font-semibold leading-tight">
              {category.replace(/_/g, ' ')} Observation
            </p>
            {date && <p className="font-mono text-[9px] text-muted-foreground">{date}</p>}
          </div>
        </div>
        <Badge
          variant={passed ? 'default' : 'destructive'}
          className="text-[9px] uppercase shrink-0"
        >
          {status.replace(/_/g, ' ')}
        </Badge>
      </div>

      {description && (
        <p className="mt-2 text-[10px] text-muted-foreground line-clamp-2">{description}</p>
      )}

      <div className="mt-2 flex items-center justify-between">
        {location && (
          <span className="text-[9px] text-muted-foreground">{location}</span>
        )}
        {score != null && (
          <div className="flex items-center gap-1">
            <Eye className="h-3 w-3 text-muted-foreground" />
            <span className="font-mono text-[12px] font-semibold">{String(score)}%</span>
          </div>
        )}
      </div>
    </div>
  );
}
