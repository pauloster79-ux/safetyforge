/**
 * Knowledge API — thin typed wrappers over /me/knowledge/* endpoints.
 *
 * Powers the Knowledge canvas (conversations / decisions / insights / mentions).
 * Designed so the UI can display:
 *   - per-message provenance (model, tokens, cost, latency)
 *   - tool calls & results extracted from assistant turns
 *   - REFERENCES edges as clickable entity chips
 *   - extracted Decision / Insight nodes inline with the source conversation
 */

import { api } from './api';

// ---------------------------------------------------------------------------
// Types — match backend/app/routers/knowledge.py response shapes
// ---------------------------------------------------------------------------

export interface KnowledgeConversation {
  id: string;
  title: string | null;
  mode: string | null;
  started_at: string | null;
  created_by: string | null;
  last_activity: string | null;
  turn_count: number;
  total_cost_cents: number | null;
  project_id: string | null;
  project_name: string | null;
}

export interface KnowledgeConversationsResponse {
  conversations: KnowledgeConversation[];
  total: number;
  limit: number;
  offset: number;
}

export interface ToolCall {
  id: string | null;
  name: string | null;
  input: unknown;
}

export interface ToolResult {
  tool_use_id: string | null;
  content: unknown;
}

export interface EntityReference {
  entity_id: string;
  entity_type: string | null;
  entity_name: string | null;
}

export interface KnowledgeMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  actor_type: 'human' | 'agent' | null;
  agent_id: string | null;
  agent_version: string | null;
  model_id: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_cents: number | null;
  latency_ms: number | null;
  confidence: number | null;
  scope_project_id: string | null;
  timestamp: string;
  content: string | null;
  sender_id: string | null;
  sender_labels: string[] | null;
  references: EntityReference[];
  tool_calls: ToolCall[];
  tool_results: ToolResult[];
}

export interface KnowledgeDecision {
  id: string;
  description: string | null;
  reasoning: string | null;
  affected_entity_type: string | null;
  affected_entity_id: string | null;
  created_at: string | null;
  conversation_id: string;
  conversation_title: string | null;
  project_id: string | null;
  project_name: string | null;
}

export interface KnowledgeInsight {
  id: string;
  content: string | null;
  tags: string[] | null;
  created_at: string | null;
  conversation_id: string;
  conversation_title: string | null;
  project_id: string | null;
  project_name: string | null;
}

export interface KnowledgeTraceTotals {
  turn_count: number;
  cost_cents: number;
  input_tokens: number;
  output_tokens: number;
}

export interface KnowledgeTrace {
  conversation: {
    id: string;
    title: string | null;
    mode: string | null;
    started_at: string | null;
    created_by: string | null;
    company_id: string;
    project_id: string | null;
    project_name: string | null;
  };
  messages: KnowledgeMessage[];
  decisions: Pick<
    KnowledgeDecision,
    'id' | 'description' | 'reasoning' | 'affected_entity_type' | 'affected_entity_id' | 'created_at'
  >[];
  insights: Pick<KnowledgeInsight, 'id' | 'content' | 'tags' | 'created_at'>[];
  totals: KnowledgeTraceTotals;
}

export interface KnowledgeMention {
  message_id: string;
  role: string;
  actor_type: string | null;
  timestamp: string;
  preview: string | null;
  conversation_id: string;
  conversation_title: string | null;
}

// ---------------------------------------------------------------------------
// API wrappers
// ---------------------------------------------------------------------------

function qs(params: Record<string, string | number | undefined | null>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '');
  if (entries.length === 0) return '';
  const sp = new URLSearchParams();
  for (const [k, v] of entries) sp.set(k, String(v));
  return `?${sp.toString()}`;
}

export const knowledgeApi = {
  listConversations: (opts: { project_id?: string; limit?: number; offset?: number } = {}) =>
    api.get<KnowledgeConversationsResponse>(`/me/knowledge/conversations${qs(opts)}`),

  getConversationTrace: (conversationId: string) =>
    api.get<KnowledgeTrace>(
      `/me/knowledge/conversations/${encodeURIComponent(conversationId)}/trace`,
    ),

  listDecisions: (opts: { project_id?: string; limit?: number; offset?: number } = {}) =>
    api.get<{ decisions: KnowledgeDecision[]; total: number; limit: number; offset: number }>(
      `/me/knowledge/decisions${qs(opts)}`,
    ),

  listInsights: (opts: { project_id?: string; limit?: number; offset?: number } = {}) =>
    api.get<{ insights: KnowledgeInsight[]; total: number; limit: number; offset: number }>(
      `/me/knowledge/insights${qs(opts)}`,
    ),

  listEntityMentions: (entityType: string, entityId: string, opts: { limit?: number; offset?: number } = {}) =>
    api.get<{
      entity_type: string;
      entity_id: string;
      mentions: KnowledgeMention[];
      total: number;
      limit: number;
      offset: number;
    }>(
      `/me/knowledge/entities/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/mentions${qs(opts)}`,
    ),
};
