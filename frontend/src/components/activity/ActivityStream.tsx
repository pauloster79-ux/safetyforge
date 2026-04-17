import { formatDistanceToNow } from 'date-fns';
import {
  Activity,
  ArrowRight,
  Bot,
  FileEdit,
  Plus,
  Trash2,
  User,
  Link2,
  Loader2,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { AuditEvent, ActivityStreamResponse } from '@/hooks/useActivityStream';

const EVENT_ICONS: Record<string, typeof Plus> = {
  'entity.created': Plus,
  'entity.updated': FileEdit,
  'entity.archived': Trash2,
  'state.transitioned': ArrowRight,
  'relationship.added': Link2,
  'relationship.removed': Link2,
  'field.changed': FileEdit,
};

const EVENT_COLORS: Record<string, string> = {
  'entity.created': 'text-emerald-600 bg-emerald-50',
  'entity.updated': 'text-blue-600 bg-blue-50',
  'entity.archived': 'text-red-600 bg-red-50',
  'state.transitioned': 'text-purple-600 bg-purple-50',
  'relationship.added': 'text-amber-600 bg-amber-50',
  'relationship.removed': 'text-amber-600 bg-amber-50',
  'field.changed': 'text-blue-600 bg-blue-50',
};

function ProvenanceBadge({ event }: { event: AuditEvent }) {
  if (event.actor_type === 'agent') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
        <Bot className="h-3 w-3" />
        <span>{event.model_id || 'Agent'}</span>
        {event.confidence != null && (
          <span className="text-[10px] opacity-70">({Math.round(event.confidence * 100)}%)</span>
        )}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
      <User className="h-3 w-3" />
      <span>{event.actor_id === 'backfill' ? 'System' : event.actor_id}</span>
    </span>
  );
}

function StateTransitionBadge({ from, to }: { from: string | null; to: string | null }) {
  if (!from && !to) return null;
  return (
    <span className="inline-flex items-center gap-1 text-xs">
      {from && <Badge variant="outline" className="text-[10px] px-1 py-0">{from}</Badge>}
      {from && to && <ArrowRight className="h-3 w-3 text-muted-foreground" />}
      {to && <Badge variant="outline" className="text-[10px] px-1 py-0 border-purple-300 text-purple-700">{to}</Badge>}
    </span>
  );
}

function EventRow({ event }: { event: AuditEvent }) {
  const IconComponent = EVENT_ICONS[event.event_type] || Activity;
  const colorClass = EVENT_COLORS[event.event_type] || 'text-gray-600 bg-gray-50';

  let timeAgo: string;
  try {
    timeAgo = formatDistanceToNow(new Date(event.occurred_at), { addSuffix: true });
  } catch {
    timeAgo = event.occurred_at;
  }

  return (
    <div className="flex items-start gap-3 py-3 border-b last:border-b-0">
      <div className={`flex-shrink-0 rounded-full p-1.5 ${colorClass}`}>
        <IconComponent className="h-3.5 w-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm leading-snug">{event.summary}</p>
        <div className="flex flex-wrap items-center gap-2 mt-1">
          <ProvenanceBadge event={event} />
          <span className="text-[11px] text-muted-foreground">{timeAgo}</span>
          {event.event_type === 'state.transitioned' && (
            <StateTransitionBadge from={event.prev_state} to={event.new_state} />
          )}
          <Badge variant="outline" className="text-[10px] px-1 py-0 font-normal">
            {event.entity_type}
          </Badge>
        </div>
      </div>
    </div>
  );
}

interface ActivityStreamProps {
  data: ActivityStreamResponse | undefined;
  isLoading: boolean;
  error: Error | null;
  emptyMessage?: string;
}

export function ActivityStream({
  data,
  isLoading,
  error,
  emptyMessage = 'No activity yet',
}: ActivityStreamProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading activity...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-sm">Unable to load activity stream</p>
        <p className="text-xs mt-1">{error.message}</p>
      </div>
    );
  }

  if (!data?.events.length) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Activity className="h-8 w-8 mx-auto mb-2 opacity-40" />
        <p className="text-sm">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="divide-y-0">
      {data.events.map((event) => (
        <EventRow key={event.id} event={event} />
      ))}
      {data.has_more && (
        <p className="text-xs text-center text-muted-foreground py-2">
          Showing {data.events.length} of {data.total}+ events
        </p>
      )}
    </div>
  );
}
