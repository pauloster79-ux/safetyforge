/**
 * InspectionCard — rendered for inspection-related tool results.
 *
 * Shows date, category, pass/fail, score.
 */

import { CheckCircle, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useShell } from '@/hooks/useShell';

interface InspectionCardProps {
  result: Record<string, unknown>;
}

export function InspectionCard({ result }: InspectionCardProps) {
  const shell = useShell();
  const status = (result.status || result.result || 'unknown') as string;
  const category = (result.category || result.inspection_type || result.type || '') as string;
  const date = (result.date || result.inspection_date || result.created_at || '') as string;
  const score = result.score ?? result.compliance_score;
  const projectId = result.project_id;
  const inspectionId = result.id || result.inspection_id;

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
              {category ? category.replace(/_/g, ' ') : 'Inspection'}
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

      {score != null && (
        <div className="mt-2 flex items-center justify-between">
          <span className="font-mono text-[10px] text-muted-foreground">Score</span>
          <span className="font-mono text-[12px] font-semibold">{String(score)}%</span>
        </div>
      )}

      {!!projectId && !!inspectionId && (
        <Button
          variant="ghost"
          size="sm"
          className="mt-2 h-7 w-full text-[10px] text-muted-foreground hover:text-foreground"
          onClick={() =>
            shell.openCanvasFromCard(
              'InspectionDetailPage',
              { projectId: String(projectId), inspectionId: String(inspectionId) },
              'Inspection',
            )
          }
        >
          Open in canvas
        </Button>
      )}
    </div>
  );
}
