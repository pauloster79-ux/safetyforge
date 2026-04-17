/**
 * ChatActionContext — provider that lets in-chat cards dispatch messages
 * back into chat.
 *
 * Most cards are pure displays of tool results. A small set (currently the
 * Insight confirmation card, possibly more later) need to emit a follow-up
 * user message so the agent can react. Threading ``sendMessage`` through
 * every card prop is noisy; a context is cheaper and stays out of the way of
 * cards that don't need it.
 *
 * The consumer hook lives in ``hooks/useChatActions.ts`` so this file
 * exports only the provider — keeps Vite's React Fast Refresh happy
 * (one component per file).
 */

import { useMemo, type ReactNode } from 'react';
import {
  ChatActionCtx,
  type ChatActions,
} from './ChatActionContextValue';

interface ChatActionProviderProps extends ChatActions {
  children: ReactNode;
}

/**
 * Wrap the chat surface so child cards can call ``useChatActions`` to
 * dispatch user messages back into the conversation.
 *
 * @param sendMessage Forwarded to consumers; called with the text to send.
 * @param prefillInput Forwarded to consumers; pre-fills the chat input so
 *   the user can refine before sending.
 * @param isStreaming Forwarded so consumers can disable buttons while the
 *   assistant is mid-reply.
 */
export function ChatActionProvider({
  sendMessage,
  prefillInput,
  isStreaming,
  children,
}: ChatActionProviderProps) {
  const value = useMemo<ChatActions>(
    () => ({ sendMessage, prefillInput, isStreaming }),
    [sendMessage, prefillInput, isStreaming],
  );
  return <ChatActionCtx.Provider value={value}>{children}</ChatActionCtx.Provider>;
}
