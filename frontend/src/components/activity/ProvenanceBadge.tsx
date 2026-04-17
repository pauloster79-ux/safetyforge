/**
 * ProvenanceBadge — displays who created or modified an entity.
 *
 * Three display variants:
 * - inline:  tiny, fits in a table row. Icon + name.
 * - card:    medium, fits in a card header. Icon + name + timestamp. Agent: model + confidence.
 * - full:    large, fits in a detail page header. All provenance fields.
 */

import { Bot, User, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow, format } from 'date-fns';

export interface ProvenanceBadgeProps {
  actorType: 'human' | 'agent';
  actorId: string;
  agentId?: string | null;
  agentVersion?: string | null;
  modelId?: string | null;
  confidence?: number | null;
  costCents?: number | null;
  timestamp?: string;
  variant?: 'inline' | 'card' | 'full';
}

function formatActorName(actorId: string): string {
  if (actorId === 'backfill' || actorId === 'system') return 'System';
  // Strip prefixes like "demo_user_001" -> "demo_user_001"
  // If the ID looks like a user ID, show it abbreviated
  if (actorId.startsWith('user_') || actorId.startsWith('demo_')) {
    return actorId.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }
  return actorId;
}

function formatTimestamp(ts: string): string {
  try {
    return formatDistanceToNow(new Date(ts), { addSuffix: true });
  } catch {
    return ts;
  }
}

function formatFullTimestamp(ts: string): string {
  try {
    return format(new Date(ts), 'MMM d, yyyy h:mm a');
  } catch {
    return ts;
  }
}

/**
 * Inline variant: tiny badge for table rows. Shows icon + actor name.
 */
function InlineVariant({ actorType, actorId }: ProvenanceBadgeProps) {
  const Icon = actorType === 'agent' ? Bot : User;
  return (
    <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground leading-none">
      <Icon className="h-3 w-3 shrink-0" />
      <span className="truncate max-w-[100px]">
        {actorType === 'agent' ? (actorId || 'Agent') : formatActorName(actorId)}
      </span>
    </span>
  );
}

/**
 * Card variant: medium badge for card headers.
 * Shows icon + name + timestamp. Agent: also model + confidence.
 */
function CardVariant({
  actorType,
  actorId,
  modelId,
  confidence,
  timestamp,
}: ProvenanceBadgeProps) {
  const Icon = actorType === 'agent' ? Bot : User;
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <div
        className={`flex h-6 w-6 items-center justify-center rounded-full ${
          actorType === 'agent'
            ? 'bg-purple-50 text-purple-600'
            : 'bg-blue-50 text-blue-600'
        }`}
      >
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div className="flex flex-col gap-0.5">
        <span className="font-medium text-foreground text-xs">
          {actorType === 'agent' ? (actorId || 'Agent') : formatActorName(actorId)}
        </span>
        <span className="flex items-center gap-2 text-[11px]">
          {timestamp && (
            <span className="flex items-center gap-0.5">
              <Clock className="h-3 w-3" />
              {formatTimestamp(timestamp)}
            </span>
          )}
          {actorType === 'agent' && modelId && (
            <Badge variant="secondary" className="text-[10px] px-1 py-0 h-4">
              {modelId}
            </Badge>
          )}
          {actorType === 'agent' && confidence != null && (
            <span className="text-[10px] opacity-70">
              {Math.round(confidence * 100)}% conf
            </span>
          )}
        </span>
      </div>
    </div>
  );
}

/**
 * Full variant: large badge for detail page headers.
 * Shows all provenance fields including agent_version, model_id, confidence, cost.
 */
function FullVariant({
  actorType,
  actorId,
  agentId,
  agentVersion,
  modelId,
  confidence,
  costCents,
  timestamp,
}: ProvenanceBadgeProps) {
  const Icon = actorType === 'agent' ? Bot : User;
  return (
    <div
      className={`flex items-start gap-3 rounded-lg border p-3 ${
        actorType === 'agent'
          ? 'border-purple-200 bg-purple-50/50'
          : 'border-border bg-muted/30'
      }`}
    >
      <div
        className={`flex h-8 w-8 items-center justify-center rounded-full shrink-0 ${
          actorType === 'agent'
            ? 'bg-purple-100 text-purple-600'
            : 'bg-blue-100 text-blue-600'
        }`}
      >
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex flex-col gap-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-foreground">
            {actorType === 'agent' ? (agentId || actorId || 'Agent') : formatActorName(actorId)}
          </span>
          <Badge
            variant="outline"
            className={`text-[10px] px-1.5 py-0 ${
              actorType === 'agent'
                ? 'border-purple-300 text-purple-700'
                : 'border-blue-300 text-blue-700'
            }`}
          >
            {actorType === 'agent' ? 'AI Agent' : 'Human'}
          </Badge>
        </div>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          {timestamp && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatFullTimestamp(timestamp)}
            </span>
          )}
          {actorType === 'agent' && agentVersion && (
            <span>v{agentVersion}</span>
          )}
          {actorType === 'agent' && modelId && (
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4">
              {modelId}
            </Badge>
          )}
          {actorType === 'agent' && confidence != null && (
            <span>Confidence: {Math.round(confidence * 100)}%</span>
          )}
          {actorType === 'agent' && costCents != null && (
            <span>Cost: ${(costCents / 100).toFixed(2)}</span>
          )}
        </div>
      </div>
    </div>
  );
}

export function ProvenanceBadge(props: ProvenanceBadgeProps) {
  const { variant = 'inline' } = props;

  switch (variant) {
    case 'inline':
      return <InlineVariant {...props} />;
    case 'card':
      return <CardVariant {...props} />;
    case 'full':
      return <FullVariant {...props} />;
    default:
      return <InlineVariant {...props} />;
  }
}
