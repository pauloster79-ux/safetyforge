/**
 * InsightCard — rendered when the ``create_insight`` tool returns.
 *
 * By the time this card appears, the Insight is already in the knowledge
 * graph. The card therefore serves as a *confirmation surface*: the
 * contractor can either let it stand (the default — silence is consent),
 * nudge the wording (inline edit via ``useUpdateInsight``), or remove it
 * entirely (``useDeleteInsight``) if it wasn't what they meant.
 *
 * The "Keep it" button is deliberately a no-op visual affordance. It
 * collapses the card into a tick so Marco/Sarah/Jake can acknowledge on a
 * phone without wondering "did it save?" — the answer is yes, it already did.
 */

import { useState } from 'react';
import { Lightbulb, Check, Pencil, Trash2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { useUpdateInsight, useDeleteInsight } from '@/hooks/useKnowledge';

interface InsightCardProps {
  result: Record<string, unknown>;
}

function describeAdjustment(
  type: string | undefined,
  value: number | undefined,
): string | null {
  if (!type) return null;
  if (type === 'productivity_multiplier' && typeof value === 'number') {
    const pct = Math.round((value - 1) * 100);
    return pct > 0 ? `+${pct}%` : `${pct}%`;
  }
  if (type === 'rate_adjustment' && typeof value === 'number') {
    const pct = Math.round((value - 1) * 100);
    return pct > 0 ? `+${pct}%` : `${pct}%`;
  }
  if (type === 'qualitative') return 'qualitative';
  return type.replace(/_/g, ' ');
}

export function InsightCard({ result }: InsightCardProps) {
  const insightId = (result.insight_id || '') as string;
  const initialStatement = (result.statement || '') as string;
  const scope = (result.scope || '') as string;
  const scopeValue = (result.scope_value || '') as string;
  const confidence = (result.confidence ?? null) as number | null;
  // adjustment_type/value are params not returned — read them if chat forwarded
  const adjustmentType = (result.adjustment_type as string | undefined);
  const adjustmentValue = (result.adjustment_value as number | undefined);
  const adjustmentLabel = describeAdjustment(adjustmentType, adjustmentValue);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(initialStatement);
  const [statement, setStatement] = useState(initialStatement);
  const [removed, setRemoved] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);

  const update = useUpdateInsight();
  const remove = useDeleteInsight();

  if (removed) {
    return (
      <div className="rounded-sm border border-border bg-muted/30 p-2 text-[11px] text-muted-foreground">
        Insight removed. Kerf won&apos;t apply this pattern to future quotes.
      </div>
    );
  }

  if (acknowledged) {
    return (
      <div className="rounded-sm border border-emerald-200 bg-emerald-50 p-2">
        <div className="flex items-center gap-2 text-[11px] text-emerald-800">
          <Check className="h-3.5 w-3.5" />
          <span className="font-medium">Saved to your knowledge.</span>
          <span className="text-emerald-700/80 truncate">{statement}</span>
        </div>
      </div>
    );
  }

  const save = () => {
    const trimmed = draft.trim();
    if (!insightId || !trimmed || trimmed === statement) {
      setEditing(false);
      setDraft(statement);
      return;
    }
    update.mutate(
      { id: insightId, patch: { statement: trimmed } },
      {
        onSuccess: () => {
          setStatement(trimmed);
          setEditing(false);
        },
        onError: () => {
          setEditing(false);
          setDraft(statement);
        },
      },
    );
  };

  const handleRemove = () => {
    if (!insightId) {
      setRemoved(true);
      return;
    }
    if (!window.confirm('Remove this insight? Kerf will stop applying it.')) return;
    remove.mutate(insightId, {
      onSuccess: () => setRemoved(true),
    });
  };

  return (
    <div className="rounded-sm border border-border bg-card p-3">
      <div className="flex items-start gap-2">
        <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
        <div className="min-w-0 flex-1">
          {editing ? (
            <div className="flex items-center gap-1">
              <Input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                autoFocus
                className="h-7 text-sm"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') save();
                  if (e.key === 'Escape') {
                    setEditing(false);
                    setDraft(statement);
                  }
                }}
              />
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                onClick={save}
                disabled={update.isPending}
                title="Save"
              >
                <Check className="h-3.5 w-3.5" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                onClick={() => {
                  setEditing(false);
                  setDraft(statement);
                }}
                title="Cancel"
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          ) : (
            <div className="flex items-start gap-2">
              <p className="min-w-0 flex-1 text-[12px] font-semibold leading-tight">
                {statement}
              </p>
              {adjustmentLabel && (
                <Badge variant="outline" className="shrink-0 font-mono text-[10px]">
                  {adjustmentLabel}
                </Badge>
              )}
            </div>
          )}
          <div className="mt-1 flex flex-wrap items-center gap-1 text-[10px] text-muted-foreground">
            <span className="uppercase tracking-wider">SOURCE:</span>
            {scope && <span>{scope.replace(/_/g, ' ')}</span>}
            {scope && scopeValue && <span>·</span>}
            {scopeValue && <span>{scopeValue}</span>}
            {confidence != null && (
              <>
                <span>·</span>
                <span>confidence {Math.round(confidence * 100)}%</span>
              </>
            )}
          </div>
        </div>
      </div>

      {!editing && (
        <div className="mt-2 flex items-center justify-end gap-1">
          <Button
            size="sm"
            variant="ghost"
            className="h-7 gap-1 px-2 text-[11px]"
            onClick={() => setEditing(true)}
            title="Edit statement"
          >
            <Pencil className="h-3 w-3" />
            Edit
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 gap-1 px-2 text-[11px] text-muted-foreground hover:text-destructive"
            onClick={handleRemove}
            disabled={remove.isPending}
            title="Remove insight"
          >
            <Trash2 className="h-3 w-3" />
            Remove
          </Button>
          <Button
            size="sm"
            className="h-7 gap-1 px-2 text-[11px]"
            onClick={() => setAcknowledged(true)}
            title="Keep it — already saved to your knowledge"
          >
            <Check className="h-3 w-3" />
            Keep it
          </Button>
        </div>
      )}
    </div>
  );
}
