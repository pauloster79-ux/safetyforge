/**
 * ConversationTrace — turn-by-turn detail for one conversation.
 *
 * Renders, per message:
 *   - role + actor type (human / agent / synthetic tool result)
 *   - the text content
 *   - tool calls (collapsible) + their results
 *   - REFERENCES chips → entity_type:entity_id (clickable later)
 *   - provenance chips: model · in/out tokens · cost · latency
 *
 * Plus extracted decisions / insights at the bottom.
 *
 * Designed to be read top-to-bottom — exactly the shape Paul asked for in the
 * "see what's recorded against the KG" requirement.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronRight, ChevronDown, Loader2, Wrench, User, Bot, Cog,
  Lightbulb, GitBranch, Coins, Cpu, Timer,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { knowledgeApi, type KnowledgeMessage, type KnowledgeTrace } from '@/lib/knowledge-api';
import { cn } from '@/lib/utils';

function formatCost(cents: number | null | undefined): string {
  if (cents == null) return '—';
  if (cents < 1) return `${(cents * 100).toFixed(2)}\u00a2`;
  return `\u00a2${cents.toFixed(4)}`;
}

function formatTimestamp(ts: string | null | undefined): string {
  if (!ts) return '';
  try {
    return new Date(ts).toLocaleString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return ts;
  }
}

function actorIcon(m: KnowledgeMessage) {
  if (m.actor_type === 'human') return <User className="h-3.5 w-3.5" />;
  if (m.tool_results.length > 0) return <Cog className="h-3.5 w-3.5" />;
  return <Bot className="h-3.5 w-3.5" />;
}

function actorLabel(m: KnowledgeMessage): string {
  if (m.actor_type === 'human') return 'User';
  if (m.tool_results.length > 0) return 'Tool result';
  if (m.tool_calls.length > 0 && m.role === 'assistant') return 'Assistant + tool calls';
  return 'Assistant';
}

// ---------------------------------------------------------------------------
// Single message row
// ---------------------------------------------------------------------------

function MessageRow({ message }: { message: KnowledgeMessage }) {
  const [showTools, setShowTools] = useState(false);
  const isHuman = message.actor_type === 'human';
  const isToolResult = message.tool_results.length > 0;
  const hasTools = message.tool_calls.length > 0 || message.tool_results.length > 0;

  return (
    <Card
      className={cn(
        'p-3',
        isHuman && 'bg-accent/30 border-accent',
        isToolResult && 'bg-muted/40 border-muted',
      )}
    >
      <div className="mb-1.5 flex items-center gap-2 text-[11px] text-muted-foreground">
        <span className="flex items-center gap-1 font-medium text-foreground">
          {actorIcon(message)} {actorLabel(message)}
        </span>
        <span>·</span>
        <span>{formatTimestamp(message.timestamp)}</span>
        {message.scope_project_id && (
          <Badge variant="outline" className="text-[10px]">
            project: {message.scope_project_id.slice(0, 14)}
          </Badge>
        )}
      </div>

      {message.content && (
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {/* tool_result content is JSON; render compact */}
          {isToolResult ? (
            <pre className="overflow-x-auto rounded bg-background/60 p-2 text-[11px]">
              {message.content.length > 800 ? message.content.slice(0, 800) + '\u2026' : message.content}
            </pre>
          ) : (
            message.content
          )}
        </div>
      )}

      {/* Tool calls / results */}
      {hasTools && (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => setShowTools((v) => !v)}
            className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground"
          >
            {showTools ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            <Wrench className="h-3 w-3" />
            {message.tool_calls.length > 0 && (
              <span>{message.tool_calls.length} tool call{message.tool_calls.length === 1 ? '' : 's'}</span>
            )}
            {message.tool_results.length > 0 && (
              <span>{message.tool_results.length} result{message.tool_results.length === 1 ? '' : 's'}</span>
            )}
          </button>
          {showTools && (
            <div className="mt-2 space-y-1.5 pl-4">
              {message.tool_calls.map((tc) => (
                <div key={tc.id ?? tc.name} className="rounded border border-border bg-background/40 p-2 text-[11px]">
                  <div className="font-mono font-medium">{tc.name}(...)</div>
                  <pre className="mt-1 overflow-x-auto text-[10px] text-muted-foreground">
                    {JSON.stringify(tc.input, null, 2)}
                  </pre>
                </div>
              ))}
              {message.tool_results.map((tr, idx) => (
                <div key={tr.tool_use_id ?? idx} className="rounded border border-dashed border-border bg-background/40 p-2 text-[11px]">
                  <div className="text-muted-foreground">→ result for {tr.tool_use_id}</div>
                  <pre className="mt-1 overflow-x-auto text-[10px]">
                    {typeof tr.content === 'string' ? tr.content : JSON.stringify(tr.content, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* References (entities mentioned) */}
      {message.references.length > 0 && (
        <div className="mt-2 flex flex-wrap items-center gap-1 text-[11px] text-muted-foreground">
          <span>refs:</span>
          {message.references.map((r) => (
            <Badge key={r.entity_id} variant="secondary" className="text-[10px]">
              {r.entity_type}: {r.entity_name || r.entity_id}
            </Badge>
          ))}
        </div>
      )}

      {/* Provenance row — only meaningful for assistant turns */}
      {message.actor_type === 'agent' && message.model_id && (
        <div className="mt-2 flex flex-wrap items-center gap-3 border-t border-border/60 pt-2 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <Cpu className="h-3 w-3" />
            <span className="font-mono">{message.model_id}</span>
          </span>
          {message.input_tokens != null && message.output_tokens != null && (
            <span>{message.input_tokens} in / {message.output_tokens} out</span>
          )}
          {message.cost_cents != null && (
            <span className="flex items-center gap-1">
              <Coins className="h-3 w-3" /> {formatCost(message.cost_cents)}
            </span>
          )}
          {message.latency_ms != null && (
            <span className="flex items-center gap-1">
              <Timer className="h-3 w-3" /> {message.latency_ms}ms
            </span>
          )}
          {message.agent_id && (
            <span className="font-mono">{message.agent_id}@{message.agent_version}</span>
          )}
        </div>
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Trace header — totals + project link
// ---------------------------------------------------------------------------

function TraceHeader({ trace }: { trace: KnowledgeTrace }) {
  const c = trace.conversation;
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold">{c.title || c.id}</span>
        {c.project_name && (
          <Badge variant="secondary" className="text-[10px]">
            {c.project_name}
          </Badge>
        )}
        {c.mode && c.mode !== 'general' && (
          <Badge variant="outline" className="text-[10px]">
            {c.mode}
          </Badge>
        )}
      </div>
      <div className="mt-1 text-[11px] text-muted-foreground">
        Started {c.started_at ? new Date(c.started_at).toLocaleString() : '—'} · created by {c.created_by}
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
        <span>{trace.totals.turn_count} turns</span>
        <span className="flex items-center gap-1">
          <Coins className="h-3 w-3" /> {formatCost(trace.totals.cost_cents)}
        </span>
        <span>
          {trace.totals.input_tokens.toLocaleString()} in / {trace.totals.output_tokens.toLocaleString()} out tokens
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Decisions/Insights footer
// ---------------------------------------------------------------------------

function ExtractedSection({ trace }: { trace: KnowledgeTrace }) {
  if (trace.decisions.length === 0 && trace.insights.length === 0) return null;
  return (
    <div className="space-y-3 rounded-md border border-dashed border-border bg-background/60 p-3">
      <div className="text-xs font-medium text-muted-foreground">Extracted from this conversation</div>
      {trace.decisions.length > 0 && (
        <div>
          <div className="mb-1 flex items-center gap-1 text-[11px] font-medium">
            <Lightbulb className="h-3 w-3" /> Decisions ({trace.decisions.length})
          </div>
          <ul className="space-y-1">
            {trace.decisions.map((d) => (
              <li key={d.id} className="text-xs">
                <span>{d.description}</span>
                {d.affected_entity_id && (
                  <Badge variant="secondary" className="ml-2 text-[10px]">
                    {d.affected_entity_type}: {d.affected_entity_id}
                  </Badge>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      {trace.insights.length > 0 && (
        <div>
          <div className="mb-1 flex items-center gap-1 text-[11px] font-medium">
            <GitBranch className="h-3 w-3" /> Insights ({trace.insights.length})
          </div>
          <ul className="space-y-1">
            {trace.insights.map((i) => (
              <li key={i.id} className="text-xs">{i.content}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Top-level
// ---------------------------------------------------------------------------

export function ConversationTrace({ conversationId }: { conversationId: string }) {
  const { data: trace, isLoading, error } = useQuery({
    queryKey: ['knowledge', 'trace', conversationId],
    queryFn: () => knowledgeApi.getConversationTrace(conversationId),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-10 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
    );
  }
  if (error || !trace) {
    return <p className="py-6 text-sm text-destructive">Failed to load trace.</p>;
  }

  return (
    <div className="space-y-3">
      <TraceHeader trace={trace} />
      <div className="space-y-2">
        {trace.messages.map((m) => (
          <MessageRow key={m.id} message={m} />
        ))}
      </div>
      <ExtractedSection trace={trace} />
    </div>
  );
}
