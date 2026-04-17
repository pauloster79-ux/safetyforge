/**
 * ChatPane — primary pane in the conversational-first layout.
 *
 * Reuses all logic from useChat and message rendering from ChatPanel.
 * Additions over the old overlay:
 * - Rich card rendering for tool_result events
 * - Context indicator (which project/entity the conversation is about)
 * - Quick action buttons in the input area
 */

import { useCallback, useEffect, useRef, useState, useMemo } from 'react';
import { DemoUserSwitcher } from '@/components/dev/DemoUserSwitcher';
import {
  MessageSquare,
  Send,
  Wrench,
  Sparkles,
  ClipboardList,
  Plus,
  Receipt,
  DollarSign,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useChat } from '@/hooks/useChat';
import { useShell } from '@/hooks/useShell';
import { CardRenderer } from '@/components/cards/CardRenderer';
import { ChatActionProvider } from '@/contexts/ChatActionContext';
import type { ChatMessage } from '@/lib/chat-stream';

// ---------------------------------------------------------------------------
// Lightweight markdown renderer (bold, italic, lists, line breaks)
// ---------------------------------------------------------------------------

function MarkdownText({ text }: { text: string }) {
  const html = useMemo(() => {
    let result = text
      // Fix missing spaces after punctuation (LLM artifact)
      .replace(/([.!?])([A-Z])/g, '$1 $2')
      .replace(/([a-z]):([A-Z])/g, '$1: $2')
      // Escape HTML
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      // Bold
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Italic
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-[12px] font-mono">$1</code>')
      // Bullet lists (- item)
      .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
      // Line breaks
      .replace(/\n/g, '<br/>');
    // Wrap consecutive <li> in <ul>
    result = result.replace(/((?:<li[^>]*>.*?<\/li><br\/>?)+)/g, (match) => {
      return '<ul class="space-y-0.5 my-1">' + match.replace(/<br\/>/g, '') + '</ul>';
    });
    return result;
  }, [text]);

  return (
    <div
      className="leading-relaxed [&_strong]:font-semibold [&_ul]:list-disc [&_ul]:ml-4"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

// ---------------------------------------------------------------------------
// Message bubble (enhanced with card rendering for tool results)
// ---------------------------------------------------------------------------

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  // Hide empty assistant bubble while waiting for first delta/tool call.
  if (!isUser && !message.content && (!message.toolCalls || message.toolCalls.length === 0)) {
    return null;
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[90%] text-sm ${
          isUser
            ? 'rounded-lg px-3 py-2 bg-machine-wash text-foreground'
            : 'text-foreground'
        }`}
      >
        {/* Tool call badges */}
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1">
            {message.toolCalls.map((tc, i) => (
              <Badge key={i} variant="secondary" className="text-[10px] gap-1 font-mono">
                <Wrench className="h-2.5 w-2.5" />
                {tc.tool.replace(/_/g, ' ')}
              </Badge>
            ))}
          </div>
        )}

        {/* Tool result cards (skip query_graph — Claude explains those in text) */}
        {!isUser && message.toolCalls && message.toolCalls.some((tc) => tc.result && tc.tool !== 'query_graph') && (
          <div className="mb-2 space-y-2">
            {message.toolCalls
              .filter((tc) => tc.result && tc.tool !== 'query_graph')
              .map((tc, i) => (
                <CardRenderer key={i} toolName={tc.tool} result={tc.result!} />
              ))}
          </div>
        )}

        {/* Message content */}
        {message.content && (
          isUser
            ? <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
            : <MarkdownText text={message.content} />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Thinking indicator — cycles through construction verbs, no box
// ---------------------------------------------------------------------------

const THINKING_VERBS = [
  'thinking',
  'surveying',
  'measuring',
  'framing',
  'levelling',
  'plumbing',
  'checking blueprints',
  'consulting the foreman',
  'calculating',
  'estimating',
];

function ThinkingIndicator() {
  const [verbIndex, setVerbIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setVerbIndex((i) => (i + 1) % THINKING_VERBS.length);
    }, 1400);
    return () => clearInterval(id);
  }, []);

  // Match the assistant MessageBubble wrapper exactly so text left-aligns
  // identically to every other thing Kerf says.
  return (
    <div className="flex justify-start">
      <div className="max-w-[90%] text-sm text-foreground">
        <div className="flex items-center gap-2 py-1">
          <span
            key={verbIndex}
            className="animate-[ti-fade_0.5s_ease-out] font-semibold text-machine-dark"
          >
            {THINKING_VERBS[verbIndex]}…
          </span>
          {/* Stacking blocks animation — 3 bars of increasing height, staggered pulse */}
          <div className="flex h-3 items-end gap-[2px]">
            <span className="block w-[3px] animate-[ti-build_1.2s_ease-in-out_infinite] rounded-[1px] bg-machine" style={{ animationDelay: '0s' }} />
            <span className="block w-[3px] animate-[ti-build_1.2s_ease-in-out_infinite] rounded-[1px] bg-machine" style={{ animationDelay: '0.2s' }} />
            <span className="block w-[3px] animate-[ti-build_1.2s_ease-in-out_infinite] rounded-[1px] bg-machine" style={{ animationDelay: '0.4s' }} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quick action chips
// ---------------------------------------------------------------------------

const QUICK_ACTIONS = [
  { label: 'New project', icon: Plus, prompt: 'Help me create a new project' },
  { label: 'New quote', icon: Receipt, prompt: 'Help me build a quote for a project' },
  { label: 'Daily log', icon: ClipboardList, prompt: 'Show me the daily log status for all projects' },
  { label: 'Money', icon: DollarSign, prompt: 'Show me a financial overview across all projects' },
];

// ---------------------------------------------------------------------------
// ChatPane
// ---------------------------------------------------------------------------

export function ChatPane() {
  const [textInput, setTextInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const companyId = sessionStorage.getItem('kerf_company_id') || 'demo_company_001';
  const shell = useShell();

  // Derive active context from the canvas view. If a project is open in the
  // right pane, the chat assumes subsequent messages relate to that project
  // unless the user names a different one.
  const contextProjectId = (() => {
    const v = shell.canvasView;
    if (!v) return undefined;
    // Any canvas view that receives a projectId prop is a project-scoped view.
    const pid = v.props?.projectId;
    return typeof pid === 'string' ? pid : undefined;
  })();
  const contextLabel = shell.canvasView?.label;

  // When a quoting tool returns data for a project, auto-open that
  // project's detail page in the canvas so the user sees it updating.
  const handleProjectAction = useCallback(
    (projectId: string, projectName: string) => {
      shell.openCanvas({
        component: 'ProjectDetailPage',
        props: { projectId },
        label: projectName,
      });
    },
    [shell],
  );

  const chat = useChat({ companyId, projectId: contextProjectId, onProjectAction: handleProjectAction });

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chat.messages]);

  const handleSend = useCallback(
    (text?: string) => {
      const msg = text || textInput;
      if (!msg.trim() || chat.isStreaming) return;
      chat.sendMessage(msg);
      if (!text) setTextInput('');
    },
    [textInput, chat],
  );

  /**
   * Pre-fill the chat input with text and place the caret at the end so the
   * user can refine before sending. Used by cards (e.g. InsightConfirmationCard)
   * whose Edit button means "I want to type, not commit yet."
   */
  const handlePrefillInput = useCallback((text: string) => {
    setTextInput(text);
    // Defer focus so the value lands before the caret jumps to the end.
    requestAnimationFrame(() => {
      const el = inputRef.current;
      if (!el) return;
      el.focus();
      const len = text.length;
      try {
        el.setSelectionRange(len, len);
      } catch {
        // Some input types don't support setSelectionRange — ignore.
      }
    });
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isEmpty = chat.messages.length === 0;

  return (
    <ChatActionProvider
      sendMessage={handleSend}
      prefillInput={handlePrefillInput}
      isStreaming={chat.isStreaming}
    >
    <div className="flex h-full flex-col bg-background">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border bg-card px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-sm bg-machine">
            <Sparkles className="h-3.5 w-3.5 text-white" />
          </div>
          <h2 className="text-sm font-semibold">Kerf</h2>
          {contextProjectId && contextLabel && (
            <Badge
              variant="secondary"
              className="ml-1 max-w-[180px] gap-1 truncate bg-machine-wash text-[10px] font-normal text-machine-dark hover:bg-machine-wash"
              title={`Chat is focused on: ${contextLabel}`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-machine" />
              <span className="truncate">{contextLabel}</span>
            </Badge>
          )}
          <DemoUserSwitcher />
        </div>
        {chat.messages.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={chat.clear}
            className="text-[11px] text-muted-foreground"
          >
            New chat
          </Button>
        )}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {isEmpty ? (
          /* Empty state */
          <div className="flex h-full flex-col items-center justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-machine-wash">
              <MessageSquare className="h-7 w-7 text-machine-dark" />
            </div>
            <h3 className="mt-4 text-base font-semibold">Ask Kerf anything</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Safety data, compliance checks, project summaries
            </p>
            <div className="mt-6 grid grid-cols-2 gap-2">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action.label}
                  onClick={() => handleSend(action.prompt)}
                  className="flex items-center gap-2 rounded-sm border border-border bg-card px-3 py-2 text-left text-[12px] font-medium text-foreground transition-colors hover:border-machine hover:bg-machine-wash"
                >
                  <action.icon className="h-3.5 w-3.5 text-muted-foreground" />
                  {action.label}
                </button>
              ))}
            </div>
            <div className="mt-6 space-y-1 text-center text-[11px] text-muted-foreground">
              <p>&ldquo;Which workers have expiring certs?&rdquo;</p>
              <p>&ldquo;Show me failed inspections this week&rdquo;</p>
              <p>&ldquo;Safety summary for Riverside Tower&rdquo;</p>
            </div>
          </div>
        ) : (
          /* Message list */
          <div className="space-y-3">
            {chat.messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Streaming indicator */}
            {chat.isStreaming && <ThinkingIndicator />}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-border bg-card px-4 py-3">
        <div className="flex items-center gap-2">
          <Input
            ref={inputRef}
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            className="flex-1 text-sm"
            disabled={chat.isStreaming}
          />
          <Button
            size="icon"
            onClick={() => handleSend()}
            disabled={!textInput.trim() || chat.isStreaming}
            className="h-9 w-9"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
    </ChatActionProvider>
  );
}
