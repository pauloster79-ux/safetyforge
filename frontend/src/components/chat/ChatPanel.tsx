import { useCallback, useEffect, useRef, useState } from 'react';
import { MessageSquare, X, Send, Loader2, Wrench } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { useChat } from '../../hooks/useChat';
import type { ChatMessage } from '../../lib/chat-stream';

// ---------------------------------------------------------------------------
// Message bubble
// ---------------------------------------------------------------------------

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? 'bg-zinc-900 text-white'
            : 'bg-white text-zinc-800 shadow-sm border border-zinc-100'
        }`}
      >
        {/* Tool calls indicator */}
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mb-1.5 flex flex-wrap gap-1">
            {message.toolCalls.map((tc, i) => (
              <Badge key={i} variant="secondary" className="text-xs gap-1">
                <Wrench className="h-3 w-3" />
                {tc.tool.replace(/_/g, ' ')}
              </Badge>
            ))}
          </div>
        )}

        {/* Message content */}
        <div className="whitespace-pre-wrap">{message.content || '\u00A0'}</div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chat Panel
// ---------------------------------------------------------------------------

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatPanel({ isOpen, onClose }: ChatPanelProps) {
  const [textInput, setTextInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const companyId = sessionStorage.getItem('kerf_company_id') || 'demo_company_001';

  const chat = useChat({ companyId });

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chat.messages]);

  const handleSend = useCallback(() => {
    if (!textInput.trim() || chat.isStreaming) return;
    chat.sendMessage(textInput);
    setTextInput('');
  }, [textInput, chat]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 z-50 flex h-full w-[400px] flex-col border-l border-zinc-200 bg-zinc-50 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-200 bg-white px-4 py-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-zinc-600" />
          <h2 className="text-sm font-semibold">Ask Kerf</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        {chat.messages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <MessageSquare className="mb-3 h-8 w-8 text-zinc-300" />
            <p className="text-sm text-zinc-500">Ask me anything about your projects</p>
            <div className="mt-4 space-y-1.5 text-xs text-zinc-400">
              <p>"Which workers have expiring certs?"</p>
              <p>"Show me failed inspections this week"</p>
              <p>"Daily log status for all projects"</p>
              <p>"Safety summary for Riverside Tower"</p>
            </div>
          </div>
        )}

        <div className="space-y-3">
          {chat.messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Streaming indicator */}
          {chat.isStreaming && (
            <div className="flex justify-start">
              <div className="flex items-center gap-1.5 rounded-lg bg-white px-3 py-2 text-sm shadow-sm border border-zinc-100">
                <Loader2 className="h-3 w-3 animate-spin text-zinc-400" />
                <span className="text-zinc-400">thinking...</span>
              </div>
            </div>
          )}
        </div>

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-zinc-200 bg-white px-3 py-3">
        <div className="flex items-center gap-2">
          <Input
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            className="flex-1 text-sm"
            disabled={chat.isStreaming}
          />
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!textInput.trim() || chat.isStreaming}
            className="h-9 w-9"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Floating toggle button (exported separately for layout)
// ---------------------------------------------------------------------------

export function ChatToggleButton({ onClick, isOpen }: { onClick: () => void; isOpen: boolean }) {
  if (isOpen) return null;

  return (
    <Button
      onClick={onClick}
      className="fixed bottom-6 right-6 z-40 h-12 w-12 rounded-full bg-zinc-900 shadow-lg hover:bg-zinc-800"
      size="icon"
    >
      <MessageSquare className="h-5 w-5 text-white" />
    </Button>
  );
}
