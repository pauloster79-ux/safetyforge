/**
 * ApplyInsightCard — rendered when the ``apply_insight`` tool returns.
 *
 * Small inline chat card. Kerf has already bumped confidence on the insight;
 * this card just tells the contractor what happened and offers one escape
 * hatch: "This wasn't right." When clicked, we prompt for a reason and call
 * ``useCorrectInsight`` which dials confidence back down (and annotates the
 * source_context so the rationale survives in the graph).
 *
 * The adjustment + before/after numbers are rendered if the tool result
 * carries them; if not, we fall back to whatever ``message`` the tool
 * produced. Don't assume optional fields exist.
 */

import { useState } from 'react';
import { Lightbulb, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useCorrectInsight } from '@/hooks/useKnowledge';

interface ApplyInsightCardProps {
  result: Record<string, unknown>;
}

function extractAdjustmentLabel(result: Record<string, unknown>): string | null {
  // Chat service occasionally forwards original adjustment_value; use it if
  // present, otherwise emit nothing (the statement alone is fine).
  const adj = result.adjustment_value;
  const adjType = result.adjustment_type;
  if (typeof adj === 'number' && (adjType === 'productivity_multiplier' || adjType === 'rate_adjustment')) {
    const pct = Math.round((adj - 1) * 100);
    return pct > 0 ? `+${pct}%` : `${pct}%`;
  }
  return null;
}

export function ApplyInsightCard({ result }: ApplyInsightCardProps) {
  const insightId = (result.insight_id || '') as string;
  const statement = (result.statement || 'Applied a pattern from your knowledge.') as string;
  const confidence = (result.confidence ?? null) as number | null;
  const message = (result.message || '') as string;
  const adjustmentLabel = extractAdjustmentLabel(result);

  // Optional before/after — if the tool passes them through, we show the swap.
  const baselineRate = result.baseline_rate as string | number | undefined;
  const adjustedRate = result.adjusted_rate as string | number | undefined;

  const [correcting, setCorrecting] = useState(false);
  const [correctionNote, setCorrectionNote] = useState('');
  const [corrected, setCorrected] = useState(false);
  const correct = useCorrectInsight();

  if (corrected) {
    return (
      <div className="rounded-sm border border-amber-200 bg-amber-50 p-2">
        <div className="flex items-center gap-2 text-[11px] text-amber-800">
          <AlertTriangle className="h-3.5 w-3.5" />
          <span className="font-medium">Thanks — recorded the correction.</span>
          <span className="text-amber-700/80 truncate">
            Kerf will be more cautious with this pattern.
          </span>
        </div>
      </div>
    );
  }

  const submitCorrection = () => {
    const trimmed = correctionNote.trim();
    if (!insightId || !trimmed || confidence == null) {
      setCorrecting(false);
      return;
    }
    correct.mutate(
      { id: insightId, note: trimmed, currentConfidence: confidence },
      {
        onSuccess: () => {
          setCorrected(true);
          setCorrecting(false);
        },
      },
    );
  };

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start gap-2">
        <div className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center">
          <Lightbulb className="h-4 w-4 text-amber-500" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start gap-2">
            <p className="min-w-0 flex-1 text-[12px] font-medium leading-tight">
              Applied your pattern{adjustmentLabel ? ` (${adjustmentLabel})` : ''}:
              {' '}
              <span className="font-normal text-muted-foreground">
                {statement}
              </span>
            </p>
            <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" />
          </div>
          {(baselineRate != null || adjustedRate != null) && (
            <div className="mt-1 font-mono text-[10px] text-muted-foreground">
              {baselineRate != null && <span>baseline {String(baselineRate)}</span>}
              {baselineRate != null && adjustedRate != null && <span> → </span>}
              {adjustedRate != null && (
                <span className="font-semibold text-foreground">
                  applied {String(adjustedRate)}
                </span>
              )}
            </div>
          )}
          {!baselineRate && !adjustedRate && message && (
            <div className="mt-1 text-[10px] text-muted-foreground">{message}</div>
          )}
          {confidence != null && (
            <div className="mt-0.5 text-[10px] text-muted-foreground">
              confidence now {Math.round(confidence * 100)}%
            </div>
          )}
        </div>
      </div>

      {correcting ? (
        <div className="mt-2 flex items-center gap-1">
          <Input
            value={correctionNote}
            onChange={(e) => setCorrectionNote(e.target.value)}
            autoFocus
            placeholder="What was wrong? (one sentence)"
            className="h-7 text-[11px]"
            onKeyDown={(e) => {
              if (e.key === 'Enter') submitCorrection();
              if (e.key === 'Escape') {
                setCorrecting(false);
                setCorrectionNote('');
              }
            }}
          />
          <Button
            size="sm"
            className="h-7 px-2 text-[11px]"
            onClick={submitCorrection}
            disabled={!correctionNote.trim() || correct.isPending}
          >
            Submit
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-[11px]"
            onClick={() => {
              setCorrecting(false);
              setCorrectionNote('');
            }}
          >
            Cancel
          </Button>
        </div>
      ) : (
        <div className="mt-2 flex items-center justify-end">
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-[11px] text-muted-foreground"
            onClick={() => setCorrecting(true)}
            disabled={!insightId || confidence == null}
            title="Tell Kerf this pattern shouldn't apply here"
          >
            This wasn&apos;t right
          </Button>
        </div>
      )}
    </div>
  );
}
