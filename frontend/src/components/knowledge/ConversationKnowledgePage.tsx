/**
 * ConversationKnowledgePage — surfaces what Kerf has recorded about chat activity.
 *
 * Three tabs (no "Mentions" tab — that lives on entity detail pages):
 *   - Conversations  list with provenance summary; click → trace view
 *   - Decisions      cross-conversation Decision nodes extracted by memory_extraction
 *   - Insights       cross-conversation Insight nodes
 *
 * Selecting a conversation switches the panel into the trace view (no canvas
 * push — the page owns its own internal navigation so the breadcrumb stays put).
 *
 * Note: this is NOT the Layer 4 "My Knowledge" page. That one lives in
 * ``KnowledgePage.tsx`` and shows rates / productivity / lessons learned.
 * This component is kept for conversational-memory inspection — route it in
 * explicitly if you want to open it again.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Brain, Loader2, MessageSquare, Lightbulb, GitBranch, ArrowLeft } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { knowledgeApi } from '@/lib/knowledge-api';
import { ConversationTrace } from './ConversationTrace';

function formatCost(cents: number | null | undefined): string {
  if (cents == null) return '—';
  if (cents < 1) return `${(cents * 100).toFixed(2)}\u00a2`;
  return `\u00a2${cents.toFixed(2)}`;
}

function formatTimestamp(ts: string | null | undefined): string {
  if (!ts) return '';
  try {
    return new Date(ts).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch {
    return ts;
  }
}

// ---------------------------------------------------------------------------
// Conversations tab
// ---------------------------------------------------------------------------

interface ConversationsTabProps {
  onSelect: (conversationId: string) => void;
}

function ConversationsTab({ onSelect }: ConversationsTabProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge', 'conversations'],
    queryFn: () => knowledgeApi.listConversations({ limit: 50 }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-10 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
    );
  }
  if (error) {
    return <p className="py-6 text-sm text-destructive">Failed to load conversations.</p>;
  }
  if (!data || data.conversations.length === 0) {
    return (
      <div className="py-10 text-center text-sm text-muted-foreground">
        No conversations recorded yet for this company.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        {data.total} conversation{data.total === 1 ? '' : 's'} recorded
      </p>
      {data.conversations.map((c) => (
        <Card
          key={c.id}
          className="cursor-pointer p-3 transition-colors hover:bg-accent/40"
          onClick={() => onSelect(c.id)}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-medium">
                  {c.title || c.id}
                </span>
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
                {formatTimestamp(c.last_activity)} · {c.created_by}
              </div>
            </div>
            <div className="text-right text-[11px] text-muted-foreground">
              <div>{c.turn_count} turn{c.turn_count === 1 ? '' : 's'}</div>
              <div>{formatCost(c.total_cost_cents)}</div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Decisions tab
// ---------------------------------------------------------------------------

interface DecisionsTabProps {
  onOpenConversation: (conversationId: string) => void;
}

function DecisionsTab({ onOpenConversation }: DecisionsTabProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge', 'decisions'],
    queryFn: () => knowledgeApi.listDecisions({ limit: 100 }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-10 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
    );
  }
  if (error) {
    return <p className="py-6 text-sm text-destructive">Failed to load decisions.</p>;
  }
  if (!data || data.decisions.length === 0) {
    return (
      <div className="py-10 text-center text-sm text-muted-foreground">
        <Lightbulb className="mx-auto mb-2 h-6 w-6 opacity-30" />
        No decisions extracted yet. They appear here when Kerf recognises a commitment in chat (e.g. "assign Mike to roofing").
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        {data.total} decision{data.total === 1 ? '' : 's'} extracted
      </p>
      {data.decisions.map((d) => (
        <Card key={d.id} className="p-3">
          <p className="text-sm">{d.description}</p>
          {d.reasoning && (
            <p className="mt-1 text-[11px] italic text-muted-foreground">{d.reasoning}</p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
            {d.affected_entity_type && d.affected_entity_id && (
              <Badge variant="secondary" className="text-[10px]">
                {d.affected_entity_type}: {d.affected_entity_id}
              </Badge>
            )}
            {d.project_name && (
              <Badge variant="outline" className="text-[10px]">
                {d.project_name}
              </Badge>
            )}
            <span>·</span>
            <span>{formatTimestamp(d.created_at)}</span>
            <button
              onClick={() => onOpenConversation(d.conversation_id)}
              className="ml-auto text-[11px] text-primary hover:underline"
            >
              source →
            </button>
          </div>
        </Card>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Insights tab
// ---------------------------------------------------------------------------

interface InsightsTabProps {
  onOpenConversation: (conversationId: string) => void;
}

function InsightsTab({ onOpenConversation }: InsightsTabProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge', 'insights'],
    queryFn: () => knowledgeApi.listInsights({ limit: 100 }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-10 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
    );
  }
  if (error) {
    return <p className="py-6 text-sm text-destructive">Failed to load insights.</p>;
  }
  if (!data || data.insights.length === 0) {
    return (
      <div className="py-10 text-center text-sm text-muted-foreground">
        <GitBranch className="mx-auto mb-2 h-6 w-6 opacity-30" />
        No insights extracted yet. They appear here when Kerf identifies a generalisable pattern in chat (e.g. "kitchen rewires average 16 hours").
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        {data.total} insight{data.total === 1 ? '' : 's'} extracted
      </p>
      {data.insights.map((i) => (
        <Card key={i.id} className="p-3">
          <p className="text-sm">{i.content}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
            {i.tags?.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-[10px]">
                {tag}
              </Badge>
            ))}
            {i.project_name && (
              <Badge variant="outline" className="text-[10px]">
                {i.project_name}
              </Badge>
            )}
            <span>·</span>
            <span>{formatTimestamp(i.created_at)}</span>
            <button
              onClick={() => onOpenConversation(i.conversation_id)}
              className="ml-auto text-[11px] text-primary hover:underline"
            >
              source →
            </button>
          </div>
        </Card>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// KnowledgePage (top-level)
// ---------------------------------------------------------------------------

export function ConversationKnowledgePage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'conversations' | 'decisions' | 'insights'>('conversations');

  if (selectedConversationId) {
    return (
      <div className="space-y-3">
        <Button
          variant="ghost"
          size="sm"
          className="h-7 gap-1.5 px-2 text-xs"
          onClick={() => setSelectedConversationId(null)}
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Knowledge
        </Button>
        <ConversationTrace conversationId={selectedConversationId} />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 pb-1">
        <Brain className="h-4 w-4 text-muted-foreground" />
        <h2 className="text-sm font-semibold">Knowledge</h2>
        <span className="text-xs text-muted-foreground">
          What Kerf has recorded about your work
        </span>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="conversations" className="gap-1.5">
            <MessageSquare className="h-3.5 w-3.5" /> Conversations
          </TabsTrigger>
          <TabsTrigger value="decisions" className="gap-1.5">
            <Lightbulb className="h-3.5 w-3.5" /> Decisions
          </TabsTrigger>
          <TabsTrigger value="insights" className="gap-1.5">
            <GitBranch className="h-3.5 w-3.5" /> Insights
          </TabsTrigger>
        </TabsList>

        <TabsContent value="conversations" className="mt-3">
          <ConversationsTab onSelect={setSelectedConversationId} />
        </TabsContent>
        <TabsContent value="decisions" className="mt-3">
          <DecisionsTab onOpenConversation={(id) => { setSelectedConversationId(id); setActiveTab('conversations'); }} />
        </TabsContent>
        <TabsContent value="insights" className="mt-3">
          <InsightsTab onOpenConversation={(id) => { setSelectedConversationId(id); setActiveTab('conversations'); }} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
