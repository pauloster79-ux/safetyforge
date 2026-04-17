/**
 * InsightConfirmationCard — rendered when the agent calls
 * ``offer_insight_capture``.
 *
 * This is the proposal-before-save flow: the agent has detected a pattern
 * worth remembering ("low ceilings in renovations add 15% to rough-in") and
 * surfaces it for confirmation rather than silently saving. Three quick
 * actions:
 *
 *   Save it   → "Yes, save that pattern."
 *   Edit      → "Let me edit it first — [user types]"
 *   Don't save → "No, don't save that one."
 *
 * Each button dispatches a chat message via ``useChatActions`` so the agent
 * processes the response naturally — it'll then call ``create_insight``,
 * acknowledge, or do nothing. We deliberately keep the cards' state minimal:
 * the agent owns the conversation thread, not the card.
 *
 * Distinct from ``InsightCard``: that one renders ``create_insight`` results
 * (already saved). This one renders ``offer_insight_capture`` proposals
 * (not yet saved). The agent's system prompt instructs it to propose before
 * committing for any pattern worth confirming with the user.
 *
 * Note: as of this writing the backend doesn't yet expose
 * ``offer_insight_capture`` as a tool. Wiring it in CardRenderer with the
 * correct name means the card lights up automatically when the tool ships.
 */

import { useState } from 'react';
import { Lightbulb, Check, Pencil, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useChatActions } from '@/hooks/useChatActions';

interface InsightConfirmationCardProps {
  result: Record<string, unknown>;
}

function describeAdjustment(
  type: string | undefined,
  value: number | undefined,
): string | null {
  if (!type) return null;
  if (
    (type === 'productivity_multiplier' || type === 'rate_adjustment')
    && typeof value === 'number'
  ) {
    const pct = Math.round((value - 1) * 100);
    return pct > 0 ? `+${pct}%` : `${pct}%`;
  }
  if (type === 'qualitative') return 'qualitative';
  return type.replace(/_/g, ' ');
}

/** Friendly noun for the adjustment_type so the agent's response sounds natural. */
function describeAdjustmentSummary(
  type: string | undefined,
  value: number | undefined,
): string | null {
  if (!type) return null;
  if (type === 'productivity_multiplier' && typeof value === 'number') {
    const pct = Math.round((value - 1) * 100);
    const dir = value > 1 ? 'add' : 'remove';
    return `${dir} ${Math.abs(pct)}% to productivity hours`;
  }
  if (type === 'rate_adjustment' && typeof value === 'number') {
    const pct = Math.round((value - 1) * 100);
    const dir = value > 1 ? '+' : '−';
    return `rate ${dir}${Math.abs(pct)}%`;
  }
  if (type === 'qualitative') return 'qualitative pattern';
  return type.replace(/_/g, ' ');
}

export function InsightConfirmationCard({ result }: InsightConfirmationCardProps) {
  const statement = (result.statement || result.proposed_statement || '') as string;
  const scope = (result.scope || '') as string;
  const scopeValue = (result.scope_value || '') as string;
  const adjustmentType = result.adjustment_type as string | undefined;
  const adjustmentValue = result.adjustment_value as number | undefined;
  const reasoning = (result.reasoning || result.context || '') as string;

  const adjustmentBadge = describeAdjustment(adjustmentType, adjustmentValue);
  const adjustmentSummary = describeAdjustmentSummary(adjustmentType, adjustmentValue);

  const { sendMessage, prefillInput, isStreaming } = useChatActions();
  const [decided, setDecided] = useState<'save' | 'edit' | 'reject' | null>(null);

  // Once the user clicks an action, collapse the card into a single-line
  // acknowledgement so the chat history stays scannable.
  if (decided === 'save') {
    return (
      <div className="rounded-sm border border-emerald-200 bg-emerald-50 p-2">
        <div className="flex items-center gap-2 text-[11px] text-emerald-800">
          <Check className="h-3.5 w-3.5" />
          <span className="font-medium">Saving the pattern…</span>
          <span className="truncate text-emerald-700/80">{statement}</span>
        </div>
      </div>
    );
  }
  if (decided === 'edit') {
    return (
      <div className="rounded-sm border border-border bg-muted/40 p-2">
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
          <Pencil className="h-3.5 w-3.5" />
          <span className="font-medium">Editing — type your version below.</span>
        </div>
      </div>
    );
  }
  if (decided === 'reject') {
    return (
      <div className="rounded-sm border border-border bg-muted/40 p-2">
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
          <X className="h-3.5 w-3.5" />
          <span className="font-medium">Skipped — not saved.</span>
        </div>
      </div>
    );
  }

  const handleSave = () => {
    setDecided('save');
    sendMessage('Yes, save that pattern.');
  };

  const handleEdit = () => {
    setDecided('edit');
    // Pre-fill the chat input rather than dispatching immediately — the user
    // wants to type their refinement before sending.
    prefillInput(`Let me edit it first — change "${statement}" to: `);
  };

  const handleReject = () => {
    setDecided('reject');
    sendMessage("No, don't save that one.");
  };

  return (
    <div className="rounded-sm border border-amber-200 bg-amber-50/50 p-3">
      <div className="flex items-start gap-2">
        <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-900">
            Save this as a pattern?
          </p>
          <div className="mt-1 flex items-start gap-2">
            <p className="min-w-0 flex-1 text-[13px] font-medium leading-snug text-foreground">
              &ldquo;{statement || 'New pattern'}&rdquo;
            </p>
            {adjustmentBadge && (
              <Badge
                variant="outline"
                className="shrink-0 border-amber-300 bg-white font-mono text-[10px]"
              >
                {adjustmentBadge}
              </Badge>
            )}
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground">
            {(scope || scopeValue) && (
              <span>
                <span className="uppercase tracking-wider">Applies to:</span>{' '}
                {scope.replace(/_/g, ' ')}
                {scope && scopeValue && ' / '}
                <span className="font-mono">{scopeValue}</span>
              </span>
            )}
            {adjustmentSummary && (
              <>
                <span>·</span>
                <span>
                  <span className="uppercase tracking-wider">Adjustment:</span>{' '}
                  {adjustmentSummary}
                </span>
              </>
            )}
          </div>
          {reasoning && (
            <p className="mt-1.5 text-[11px] italic text-muted-foreground">{reasoning}</p>
          )}
        </div>
      </div>

      <div className="mt-3 flex items-center justify-end gap-1">
        <Button
          size="sm"
          variant="ghost"
          className="h-7 gap-1 px-2 text-[11px] text-muted-foreground"
          onClick={handleReject}
          disabled={isStreaming}
          title="Don't save this pattern"
        >
          <X className="h-3 w-3" />
          Don&apos;t save
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 gap-1 px-2 text-[11px]"
          onClick={handleEdit}
          disabled={isStreaming}
          title="Edit before saving"
        >
          <Pencil className="h-3 w-3" />
          Edit
        </Button>
        <Button
          size="sm"
          className="h-7 gap-1 px-2 text-[11px]"
          onClick={handleSave}
          disabled={isStreaming || !statement}
          title="Save this pattern to your knowledge"
        >
          <Check className="h-3 w-3" />
          Save it
        </Button>
      </div>
    </div>
  );
}
