/**
 * React hook for managing chat state and streaming responses from Kerf.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { streamChat, type ChatMessage, type InspectionProgress } from '../lib/chat-stream';

// Map of tool names → React Query keys to invalidate when the tool produces a result.
// Chat-driven mutations won't refetch on their own, so we invalidate here.
// Keep these in sync with query keys declared in hooks/use*.ts.
const estimateKeys = (pid: string): string[][] => [
  ['estimate-summary', pid],
  ['work-items', pid],
  ['labour', pid],
  ['items', pid],
];
const TOOL_INVALIDATIONS: Record<string, (projectId?: string) => string[][]> = {
  add_assumption: (pid) => (pid ? [['assumptions', pid]] : []),
  update_assumption: (pid) => (pid ? [['assumptions', pid]] : []),
  remove_assumption: (pid) => (pid ? [['assumptions', pid]] : []),
  add_exclusion: (pid) => (pid ? [['exclusions', pid]] : []),
  update_exclusion: (pid) => (pid ? [['exclusions', pid]] : []),
  remove_exclusion: (pid) => (pid ? [['exclusions', pid]] : []),
  create_work_item: (pid) => (pid ? estimateKeys(pid) : []),
  update_work_item: (pid) => (pid ? estimateKeys(pid) : []),
  remove_work_item: (pid) => (pid ? estimateKeys(pid) : []),
  create_labour: (pid) => (pid ? estimateKeys(pid) : []),
  create_item: (pid) => (pid ? estimateKeys(pid) : []),
  create_payment_milestone: (pid) =>
    pid ? [['payment-milestones', pid], ['contract-detail', pid]] : [],
  update_payment_milestone: (pid) =>
    pid ? [['payment-milestones', pid], ['contract-detail', pid]] : [],
  remove_payment_milestone: (pid) =>
    pid ? [['payment-milestones', pid], ['contract-detail', pid]] : [],
  create_condition: (pid) => (pid ? [['conditions', pid], ['contract-detail', pid]] : []),
  update_condition: (pid) => (pid ? [['conditions', pid], ['contract-detail', pid]] : []),
  remove_condition: (pid) => (pid ? [['conditions', pid], ['contract-detail', pid]] : []),
  set_warranty_terms: (pid) => (pid ? [['warranty', pid], ['contract-detail', pid]] : []),
  set_retention_terms: (pid) => (pid ? [['contract-detail', pid]] : []),
  update_project_state: (pid) => (pid ? [['project', pid], ['projects']] : [['projects']]),
  update_project_status: (pid) => (pid ? [['project', pid], ['projects']] : [['projects']]),
  set_contract_type: (pid) => (pid ? [['project', pid], ['projects']] : [['projects']]),
  capture_lead: (pid) => (pid ? [['project', pid], ['projects']] : [['projects']]),
  generate_proposal: (pid) => (pid ? [['project', pid], ['documents', pid]] : []),
};

/** Tools that produce project-scoped data worth navigating to. */
const AUTO_NAV_TOOLS = new Set([
  'create_work_item',
  'update_work_item',
  'remove_work_item',
  'create_labour',
  'create_item',
  'add_assumption',
  'update_assumption',
  'remove_assumption',
  'add_exclusion',
  'update_exclusion',
  'remove_exclusion',
  'create_payment_milestone',
  'update_payment_milestone',
  'remove_payment_milestone',
  'create_condition',
  'update_condition',
  'remove_condition',
  'set_warranty_terms',
  'set_retention_terms',
  'set_contract_type',
  'capture_lead',
  'generate_proposal',
  'get_estimate_summary',
  'get_project_summary',
  'get_contract_summary',
]);

interface UseChatOptions {
  companyId: string;
  projectId?: string;
  /** Called when a quoting tool returns a project_id + project_name so the
   *  shell can auto-open that project's detail page. */
  onProjectAction?: (projectId: string, projectName: string) => void;
}

export function useChat({ companyId, projectId, onProjectAction }: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [mode, setMode] = useState<'general' | 'inspection'>('general');
  const [inspectionProgress, setInspectionProgress] = useState<InspectionProgress | null>(null);
  const [sessionId, setSessionId] = useState(() => `chat_${crypto.randomUUID().slice(0, 16)}`);
  const abortRef = useRef<AbortController | null>(null);
  const queryClient = useQueryClient();

  // When the user switches projects, the previous backend session's
  // conversation context (including the old project's work items and
  // assumptions injected into the system prompt) is no longer relevant.
  // Reset the session id and clear local messages so the chat starts
  // fresh for the new project.
  useEffect(() => {
    abortRef.current?.abort();
    setSessionId(`chat_${crypto.randomUUID().slice(0, 16)}`);
    setMessages([]);
    setMode('general');
    setInspectionProgress(null);
  }, [projectId]);

  const sendMessage = useCallback(
    async (text: string, opts?: { inspectionType?: string; overrideMode?: 'general' | 'inspection' }) => {
      if (!text.trim() || isStreaming) return;
      const effectiveMode = opts?.overrideMode || mode;

      // Append user message
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: text,
        timestamp: new Date().toISOString(),
      };

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '',
        toolCalls: [],
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const stream = streamChat(
          {
            session_id: sessionId,
            message: text,
            company_id: companyId,
            project_id: projectId,
            mode: effectiveMode,
            inspection_type: opts?.inspectionType,
          },
          controller.signal,
        );

        for await (const event of stream) {
          if (controller.signal.aborted) break;

          switch (event.type) {
            case 'text_delta':
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    content: last.content + (event.data.text as string),
                  };
                }
                return updated;
              });
              break;

            case 'tool_call':
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    toolCalls: [
                      ...(last.toolCalls || []),
                      { tool: event.data.tool as string },
                    ],
                  };
                }
                return updated;
              });
              break;

            case 'tool_result': {
              const toolName = event.data.tool as string;
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.role === 'assistant' && last.toolCalls) {
                  const calls = [...last.toolCalls];
                  const idx = calls.findLastIndex(
                    (c) => c.tool === toolName && !c.result,
                  );
                  if (idx >= 0) {
                    calls[idx] = {
                      ...calls[idx],
                      result: event.data.result as Record<string, unknown>,
                    };
                  }
                  updated[updated.length - 1] = { ...last, toolCalls: calls };
                }
                return updated;
              });
              // Prefer project_id from the tool result (the agent may have
              // acted on a different project than the one open in the canvas)
              // and fall back to the current canvas project.
              const res = event.data.result as Record<string, unknown> | undefined;
              const resultPid = (res?.project_id as string | undefined) || projectId;
              // Invalidate affected query caches so panels refresh.
              const invalidate = TOOL_INVALIDATIONS[toolName];
              if (invalidate) {
                for (const key of invalidate(resultPid)) {
                  queryClient.invalidateQueries({ queryKey: key });
                }
              }
              // Auto-navigate to the project detail page when a quoting
              // tool creates or updates data so the user sees the result.
              if (onProjectAction && AUTO_NAV_TOOLS.has(toolName)) {
                const pname = res?.project_name as string | undefined;
                if (resultPid && pname) {
                  onProjectAction(resultPid, pname);
                }
              }
              break;
            }

            case 'inspection_progress':
              setInspectionProgress(event.data as unknown as InspectionProgress);
              break;

            case 'error':
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    content: last.content + `\n\n⚠️ Error: ${event.data.message}`,
                  };
                }
                return updated;
              });
              break;

            case 'done':
              break;
          }
        }
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === 'assistant') {
              updated[updated.length - 1] = {
                ...last,
                content: last.content + '\n\n⚠️ Connection lost. Please try again.',
              };
            }
            return updated;
          });
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [companyId, projectId, mode, sessionId, isStreaming, onProjectAction],
  );

  const startInspection = useCallback(
    (_inspectionProjectId: string, inspectionType: string) => {
      setMode('inspection');
      setInspectionProgress(null);
      setMessages([]);
      // Send initial message to start the inspection flow (pass overrideMode
      // because the mode state update hasn't been applied yet in this render)
      setTimeout(() => {
        sendMessage(`Start a ${inspectionType.replace(/_/g, ' ')} inspection.`, {
          inspectionType,
          overrideMode: 'inspection',
        });
      }, 100);
    },
    [sendMessage],
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  const clear = useCallback(() => {
    cancel();
    setMessages([]);
    setMode('general');
    setInspectionProgress(null);
    setSessionId(`chat_${crypto.randomUUID().slice(0, 16)}`);
  }, [cancel]);

  return {
    messages,
    isStreaming,
    mode,
    inspectionProgress,
    sessionId,
    sendMessage,
    startInspection,
    cancel,
    clear,
  };
}
