/**
 * Shared context value + types for the chat action context.
 *
 * Lives in its own file so the provider component file can keep React Fast
 * Refresh happy (one component export per file). The hook in
 * ``hooks/useChatActions.ts`` and the provider in ``ChatActionContext.tsx``
 * both import from here.
 */

import { createContext } from 'react';

export interface ChatActions {
  /** Dispatch a follow-up user message into the active chat session. */
  sendMessage: (text: string) => void;
  /**
   * Pre-fill the chat input with text and focus it (so the user can edit
   * before sending). Used by cards that want the user to refine wording
   * before the message is dispatched (e.g. the Insight confirmation card's
   * "Edit" action).
   */
  prefillInput: (text: string) => void;
  /** True while the chat is streaming a response (use to disable buttons). */
  isStreaming: boolean;
}

export const ChatActionCtx = createContext<ChatActions | null>(null);
