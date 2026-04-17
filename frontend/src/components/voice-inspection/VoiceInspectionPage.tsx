import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import { ArrowLeft, Mic, MicOff, Square, Send, Volume2, Loader2, CheckCircle, XCircle, MinusCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { useChat } from '../../hooks/useChat';
import { useVoiceConversation } from '../../hooks/useVoiceConversation';
import type { InspectionProgress } from '../../lib/chat-stream';

// ---------------------------------------------------------------------------
// Conversation Orb — large, unmistakable state indicator
// ---------------------------------------------------------------------------

function ConversationOrb({
  state,
  onTapToInterrupt,
}: {
  state: string;
  onTapToInterrupt: () => void;
}) {
  const config: Record<string, { label: string; sublabel: string; bg: string; ring: string; icon: React.ReactNode }> = {
    idle: {
      label: 'Tap to start',
      sublabel: 'Voice is off',
      bg: 'bg-zinc-200',
      ring: '',
      icon: <MicOff className="h-12 w-12 text-zinc-500" />,
    },
    listening: {
      label: 'Listening',
      sublabel: 'Speak now...',
      bg: 'bg-emerald-500',
      ring: 'ring-4 ring-emerald-200 animate-pulse',
      icon: <Mic className="h-12 w-12 text-white" />,
    },
    processing: {
      label: 'Thinking',
      sublabel: 'Processing your answer...',
      bg: 'bg-amber-500',
      ring: 'ring-4 ring-amber-200',
      icon: <Loader2 className="h-12 w-12 text-white animate-spin" />,
    },
    speaking: {
      label: 'Kerf speaking',
      sublabel: 'Tap to interrupt',
      bg: 'bg-blue-500',
      ring: 'ring-4 ring-blue-200 animate-pulse',
      icon: <Volume2 className="h-12 w-12 text-white" />,
    },
  };

  const c = config[state] || config.idle;

  return (
    <button
      onClick={state === 'speaking' ? onTapToInterrupt : undefined}
      className={`flex flex-col items-center gap-4 focus:outline-none ${state === 'speaking' ? 'cursor-pointer' : 'cursor-default'}`}
    >
      <div
        className={`flex h-32 w-32 items-center justify-center rounded-full ${c.bg} ${c.ring} shadow-lg transition-all duration-500`}
      >
        {c.icon}
      </div>
      <div className="text-center">
        <p className="text-lg font-semibold text-zinc-800">{c.label}</p>
        <p className="text-sm text-zinc-500">{c.sublabel}</p>
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Live transcript display
// ---------------------------------------------------------------------------

function TranscriptDisplay({
  interim,
  final,
  visible,
}: {
  interim: string;
  final: string;
  visible: boolean;
}) {
  if (!visible || (!interim && !final)) return null;

  return (
    <div className="w-full max-w-lg rounded-xl border-2 border-emerald-200 bg-emerald-50 px-5 py-3">
      <p className="text-sm font-medium text-emerald-700">You said:</p>
      <p className="mt-1 text-base text-emerald-900">
        {final}
        {interim && <span className="text-emerald-600 opacity-70"> {interim}</span>}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Kerf's response bubble
// ---------------------------------------------------------------------------

function KerfResponse({ text, isStreaming }: { text: string; isStreaming: boolean }) {
  if (!text) return null;

  return (
    <div className="w-full max-w-lg rounded-xl border border-zinc-200 bg-white px-5 py-4 shadow-sm">
      <p className="whitespace-pre-wrap text-base leading-relaxed text-zinc-800">{text}</p>
      {isStreaming && (
        <span className="mt-2 inline-flex items-center gap-1.5 text-xs text-zinc-400">
          <Loader2 className="h-3 w-3 animate-spin" />
          responding...
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Progress bar
// ---------------------------------------------------------------------------

function InspectionProgressBar({ progress }: { progress: InspectionProgress | null }) {
  if (!progress) return null;

  const pct = progress.total_items > 0
    ? Math.round((progress.completed_count / progress.total_items) * 100)
    : 0;

  return (
    <div className="w-full max-w-lg">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-zinc-700">
          {progress.completed ? 'Inspection Complete' : `Item ${Math.min(progress.current_index + 1, progress.total_items)} of ${progress.total_items}`}
        </span>
        <span className="tabular-nums text-zinc-500">{pct}%</span>
      </div>
      <div className="mt-2 h-3 w-full overflow-hidden rounded-full bg-zinc-100">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${progress.completed ? 'bg-emerald-500' : 'bg-amber-500'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {progress.current_item && !progress.completed && (
        <p className="mt-2 text-sm text-zinc-500">
          <span className="font-medium text-zinc-700">{progress.current_item.category}</span>
          {' — '}
          {progress.current_item.description}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Completed items
// ---------------------------------------------------------------------------

function CompletedItems({ progress }: { progress: InspectionProgress | null }) {
  if (!progress || Object.keys(progress.responses).length === 0) return null;

  const statusIcon: Record<string, React.ReactNode> = {
    pass: <CheckCircle className="h-4 w-4 text-emerald-500" />,
    fail: <XCircle className="h-4 w-4 text-red-500" />,
    na: <MinusCircle className="h-4 w-4 text-zinc-400" />,
  };

  const statusLabel: Record<string, { text: string; variant: 'default' | 'destructive' | 'secondary' }> = {
    pass: { text: 'PASS', variant: 'default' },
    fail: { text: 'FAIL', variant: 'destructive' },
    na: { text: 'N/A', variant: 'secondary' },
  };

  return (
    <div className="w-full max-w-lg">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">
        Results so far
      </p>
      <div className="max-h-40 space-y-1 overflow-y-auto rounded-lg border border-zinc-100 bg-white">
        {Object.entries(progress.responses).map(([itemId, resp]) => {
          const s = statusLabel[resp.status] || statusLabel.na;
          return (
            <div key={itemId} className="flex items-center gap-2 px-3 py-2 text-sm">
              {statusIcon[resp.status]}
              <span className="flex-1 truncate text-zinc-700">{itemId.replace(/_/g, ' ')}</span>
              <Badge variant={s.variant} className="text-[10px]">{s.text}</Badge>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function VoiceInspectionPage({ projectId: propProjectId, type: propType }: { projectId?: string; type?: string } = {}) {
  const params = useParams<{ projectId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useCanvasNavigate();
  const projectId = propProjectId || params.projectId;
  const inspectionType = propType || searchParams.get('type') || 'daily_site';

  const [voiceActive, setVoiceActive] = useState(false);
  const [textInput, setTextInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const startedRef = useRef(false);

  const companyId = sessionStorage.getItem('kerf_company_id') || 'demo_company_001';

  const chat = useChat({ companyId, projectId });

  // Voice conversation — wired to chat.sendMessage
  const voice = useVoiceConversation({
    onTranscript: useCallback((text: string) => {
      chat.sendMessage(text, { inspectionType, overrideMode: 'inspection' });
    }, [chat, inspectionType]),
  });

  // Wire streaming text to voice TTS
  const lastContentLenRef = useRef(0);
  useEffect(() => {
    if (!voiceActive || !chat.messages.length) return;
    const lastMsg = chat.messages[chat.messages.length - 1];
    if (lastMsg?.role !== 'assistant') return;

    const content = lastMsg.content;
    if (content.length > lastContentLenRef.current) {
      const delta = content.slice(lastContentLenRef.current);
      voice.feedStreamingText(delta);
      lastContentLenRef.current = content.length;
    }

    // When streaming finishes, flush remaining buffer
    if (!chat.isStreaming && content.length > 0) {
      voice.flushStreamingText();
      lastContentLenRef.current = 0; // Reset for next message
    }
  }, [chat.messages, chat.isStreaming, voiceActive, voice]);

  // Start inspection on mount
  useEffect(() => {
    if (projectId && !startedRef.current) {
      startedRef.current = true;
      chat.startInspection(projectId, inspectionType);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chat.messages, chat.inspectionProgress]);

  // Voice toggle
  const toggleVoice = useCallback(() => {
    if (voiceActive) {
      voice.stopConversation();
      setVoiceActive(false);
    } else {
      setVoiceActive(true);
      voice.startConversation();
    }
  }, [voiceActive, voice]);

  // Text input send
  const handleSendText = useCallback(() => {
    if (!textInput.trim()) return;
    chat.sendMessage(textInput, { inspectionType, overrideMode: 'inspection' });
    setTextInput('');
  }, [textInput, chat, inspectionType]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  // Get the latest assistant message
  const lastAssistantMsg = chat.messages
    .filter((m) => m.role === 'assistant')
    .slice(-1)[0];

  return (
    <div className="flex h-screen flex-col bg-gradient-to-b from-zinc-50 to-zinc-100">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-5 py-3 shadow-sm">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="gap-1.5">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <h1 className="text-sm font-semibold text-zinc-800">
          {inspectionType.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} Inspection
        </h1>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            voice.stopConversation();
            chat.cancel();
            navigate(-1);
          }}
        >
          End
        </Button>
      </header>

      {/* Scrollable content */}
      <div className="flex flex-1 flex-col items-center gap-6 overflow-y-auto px-4 py-8">
        {/* Conversation orb */}
        <ConversationOrb
          state={voiceActive ? voice.state : 'idle'}
          onTapToInterrupt={voice.interrupt}
        />

        {/* Live transcript (what the user is saying) */}
        <TranscriptDisplay
          interim={voice.interimTranscript}
          final={voice.finalTranscript}
          visible={voiceActive && (voice.state === 'listening' || voice.state === 'processing')}
        />

        {/* Kerf's latest response */}
        <KerfResponse
          text={lastAssistantMsg?.content || ''}
          isStreaming={chat.isStreaming}
        />

        {/* Progress */}
        <InspectionProgressBar progress={chat.inspectionProgress} />

        {/* Completed items */}
        <CompletedItems progress={chat.inspectionProgress} />

        <div ref={scrollRef} />
      </div>

      {/* Bottom controls */}
      <footer className="border-t border-zinc-200 bg-white px-4 py-4 shadow-inner">
        <div className="mx-auto flex max-w-lg items-center gap-3">
          {/* Voice toggle — big and obvious */}
          <Button
            size="lg"
            className={`h-12 w-12 rounded-full p-0 transition-all duration-300 ${
              voiceActive
                ? voice.state === 'listening'
                  ? 'bg-emerald-500 hover:bg-emerald-600 shadow-emerald-200 shadow-lg'
                  : voice.state === 'speaking'
                    ? 'bg-blue-500 hover:bg-blue-600 shadow-blue-200 shadow-lg'
                    : 'bg-amber-500 hover:bg-amber-600'
                : 'bg-zinc-200 hover:bg-zinc-300 text-zinc-600'
            }`}
            onClick={toggleVoice}
            disabled={!voice.isSupported}
            title={
              !voice.isSupported
                ? 'Voice not supported in this browser'
                : voiceActive
                  ? 'Stop voice'
                  : 'Start voice conversation'
            }
          >
            {voiceActive ? (
              voice.state === 'speaking' ? <Volume2 className="h-5 w-5 text-white" /> :
              voice.state === 'processing' ? <Loader2 className="h-5 w-5 text-white animate-spin" /> :
              <Mic className="h-5 w-5 text-white" />
            ) : (
              <MicOff className="h-5 w-5" />
            )}
          </Button>

          {/* Interrupt button — only when Kerf is speaking */}
          {voiceActive && voice.state === 'speaking' && (
            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10 rounded-full border-red-200 text-red-500 hover:bg-red-50"
              onClick={voice.interrupt}
              title="Interrupt Kerf"
            >
              <Square className="h-4 w-4" />
            </Button>
          )}

          {/* Text input */}
          <Input
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={voiceActive ? 'Or type here...' : 'Type your answer...'}
            className="flex-1"
            disabled={chat.isStreaming}
          />
          <Button
            size="icon"
            className="h-10 w-10 rounded-full"
            onClick={handleSendText}
            disabled={!textInput.trim() || chat.isStreaming}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </footer>
    </div>
  );
}
