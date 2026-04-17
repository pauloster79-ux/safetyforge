/**
 * useChatActions — read the chat action context from inside a card.
 *
 * Returns ``sendMessage`` and ``isStreaming`` from the nearest
 * ``ChatActionProvider``. Used by cards (e.g. ``InsightConfirmationCard``)
 * that need to dispatch follow-up user messages so the agent can react.
 *
 * If a consumer mounts outside the provider (e.g. an entity detail page
 * that happens to embed an InsightCard), this returns no-op functions so
 * the card stays operable but the buttons silently do nothing — preferable
 * to throwing inside a tool-result render.
 */

import { useContext } from 'react';
import {
  ChatActionCtx,
  type ChatActions,
} from '@/contexts/ChatActionContextValue';

const NOOP_ACTIONS: ChatActions = {
  sendMessage: () => {},
  prefillInput: () => {},
  isStreaming: false,
};

/**
 * Read the chat action context. Returns no-op handlers if used outside
 * a ``ChatActionProvider`` so cards still mount cleanly outside chat.
 */
export function useChatActions(): ChatActions {
  return useContext(ChatActionCtx) ?? NOOP_ACTIONS;
}
