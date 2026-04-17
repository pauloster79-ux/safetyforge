/**
 * SSE streaming client for the Kerf chat endpoint.
 *
 * Uses fetch + ReadableStream (not EventSource, which is GET-only).
 * Supports demo mode with simulated responses.
 */

import { BASE_URL, getAuthToken } from './api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ChatRequest {
  session_id?: string;
  message: string;
  company_id: string;
  project_id?: string;
  mode: 'general' | 'inspection';
  inspection_type?: string;
}

export interface ChatEvent {
  type: 'text_delta' | 'tool_call' | 'tool_result' | 'inspection_progress' | 'done' | 'error';
  data: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: Array<{ tool: string; result?: Record<string, unknown> }>;
  timestamp: string;
}

export interface InspectionProgress {
  current_index: number;
  total_items: number;
  completed_count: number;
  current_item: {
    item_id: string;
    category: string;
    description: string;
  } | null;
  completed: boolean;
  responses: Record<string, { status: string; notes: string }>;
}

// ---------------------------------------------------------------------------
// SSE streaming
// ---------------------------------------------------------------------------

export async function* streamChat(
  request: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  // Chat always hits the real backend (even in demo mode) so the user
  // gets real Claude + MCP tool responses against golden project data.
  // The demo-token is accepted by the backend in development mode.
  const token = await getAuthToken();

  const response = await fetch(`${BASE_URL}/me/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    yield {
      type: 'error',
      data: { message: `Chat request failed: ${response.status} ${response.statusText}` },
    };
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    yield { type: 'error', data: { message: 'No response body' } };
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE lines: "data: {...}\n\n"
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const chunk of lines) {
        const trimmed = chunk.trim();
        if (!trimmed) continue;

        for (const line of trimmed.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6)) as ChatEvent;
              yield event;
            } catch {
              // Skip malformed JSON
            }
          }
        }
      }
    }

    // Process remaining buffer
    if (buffer.trim()) {
      for (const line of buffer.trim().split('\n')) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6)) as ChatEvent;
            yield event;
          } catch {
            // Skip malformed JSON
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
