/**
 * Voice conversation hook — full-duplex conversation loop with proper state machine.
 *
 * State machine:
 *   IDLE ──start──> LISTENING ──speech──> PROCESSING ──response──> SPEAKING ──done──> LISTENING
 *                       ^                                              │
 *                       └──────────── interrupt (user speaks) ─────────┘
 *
 * Key design decisions:
 * - Uses continuous=true SpeechRecognition so the mic stays open (no flicker)
 * - Silence timer (1.5s) detects end-of-utterance instead of relying on onend
 * - TTS speaks sentence-by-sentence, queuing chunks as they stream in
 * - Interruption: if user speaks during TTS, cancel speech immediately and process
 * - All state transitions go through a single dispatch function to prevent races
 */

import { useCallback, useEffect, useRef, useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ConversationState = 'idle' | 'listening' | 'processing' | 'speaking';

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
}

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onspeechstart: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionInstance;
    webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
  }
}

interface UseVoiceConversationOptions {
  /** Called with final transcript when user finishes speaking */
  onTranscript: (text: string) => void;
  /** Language for speech recognition */
  lang?: string;
}

// How long to wait after last speech before sending (ms)
const SILENCE_TIMEOUT_MS = 1800;
// How long to wait before restarting recognition if it dies
const RESTART_DELAY_MS = 200;

export function useVoiceConversation({
  onTranscript,
  lang = 'en-US',
}: UseVoiceConversationOptions) {
  const [state, setState] = useState<ConversationState>('idle');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);

  // Refs for stable access in callbacks
  const stateRef = useRef<ConversationState>('idle');
  const activeRef = useRef(false); // Is the conversation loop active?
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const accumulatedTranscriptRef = useRef('');
  const ttsQueueRef = useRef<string[]>([]);
  const isSpeakingRef = useRef(false);
  const selectedVoiceRef = useRef<SpeechSynthesisVoice | null>(null);
  const onTranscriptRef = useRef(onTranscript);

  // Keep refs in sync
  useEffect(() => { stateRef.current = state; }, [state]);
  useEffect(() => { onTranscriptRef.current = onTranscript; }, [onTranscript]);

  // Check browser support
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SR && 'speechSynthesis' in window);
    // Pre-load voices (Chrome loads them async)
    if ('speechSynthesis' in window) {
      speechSynthesis.getVoices();
      speechSynthesis.onvoiceschanged = () => {
        selectedVoiceRef.current = pickVoice();
      };
      selectedVoiceRef.current = pickVoice();
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Voice selection
  // ---------------------------------------------------------------------------

  function pickVoice(): SpeechSynthesisVoice | null {
    const voices = speechSynthesis.getVoices();
    // Ranked preference: natural-sounding English voices
    const ranked = [
      (v: SpeechSynthesisVoice) => v.name.includes('Google UK English Male'),
      (v: SpeechSynthesisVoice) => v.name.includes('Google UK English Female'),
      (v: SpeechSynthesisVoice) => v.name.includes('Microsoft Mark') || v.name.includes('Microsoft David'),
      (v: SpeechSynthesisVoice) => v.name.includes('Samantha'),
      (v: SpeechSynthesisVoice) => v.lang.startsWith('en') && !v.name.includes('Google'),
      (v: SpeechSynthesisVoice) => v.lang.startsWith('en'),
    ];
    for (const test of ranked) {
      const match = voices.find(test);
      if (match) return match;
    }
    return voices[0] || null;
  }

  // ---------------------------------------------------------------------------
  // State transition — single point of control
  // ---------------------------------------------------------------------------

  const transition = useCallback((to: ConversationState) => {
    if (!activeRef.current && to !== 'idle') return; // Don't transition if stopped
    stateRef.current = to;
    setState(to);
  }, []);

  // ---------------------------------------------------------------------------
  // Speech Recognition (STT) — continuous mode
  // ---------------------------------------------------------------------------

  const destroyRecognition = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.onresult = null;
      recognitionRef.current.onerror = null;
      recognitionRef.current.onend = null;
      recognitionRef.current.onspeechstart = null;
      try { recognitionRef.current.abort(); } catch { /* */ }
      recognitionRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, []);

  const commitTranscript = useCallback(() => {
    const text = accumulatedTranscriptRef.current.trim();
    if (!text) return;
    accumulatedTranscriptRef.current = '';
    setInterimTranscript('');
    setFinalTranscript(text);
    transition('processing');
    onTranscriptRef.current(text);
  }, [transition]);

  const resetSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    silenceTimerRef.current = setTimeout(() => {
      // Silence detected — commit whatever we have
      if (accumulatedTranscriptRef.current.trim()) {
        commitTranscript();
      }
    }, SILENCE_TIMEOUT_MS);
  }, [commitTranscript]);

  const ensureRecognition = useCallback(() => {
    if (!activeRef.current) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;

    // If already running, just make sure state is right
    if (recognitionRef.current) return;

    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = lang;

    recognition.onspeechstart = () => {
      // User started speaking — if we're speaking TTS, interrupt
      if (stateRef.current === 'speaking') {
        cancelTTS();
        transition('listening');
      }
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      if (!activeRef.current) return;

      // If we were speaking and user talks, interrupt TTS
      if (stateRef.current === 'speaking') {
        cancelTTS();
        transition('listening');
      }

      // Make sure we're in listening state
      if (stateRef.current !== 'listening' && stateRef.current !== 'processing') {
        transition('listening');
      }

      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          final += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }

      if (final) {
        accumulatedTranscriptRef.current += final;
        setInterimTranscript('');
        setFinalTranscript(accumulatedTranscriptRef.current);
      }
      if (interim) {
        setInterimTranscript(interim);
      }

      // Reset silence timer on any speech
      resetSilenceTimer();
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error === 'no-speech' || event.error === 'aborted') {
        // Expected — don't change state, recognition will restart via onend
        return;
      }
      console.error('Speech recognition error:', event.error);
    };

    recognition.onend = () => {
      recognitionRef.current = null;
      // Recognition died — restart if we're still active and should be listening
      if (activeRef.current && (stateRef.current === 'listening' || stateRef.current === 'idle')) {
        setTimeout(() => ensureRecognition(), RESTART_DELAY_MS);
      }
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch {
      recognitionRef.current = null;
    }
  }, [lang, transition, resetSilenceTimer]);

  // ---------------------------------------------------------------------------
  // Speech Synthesis (TTS) — sentence queue
  // ---------------------------------------------------------------------------

  const cancelTTS = useCallback(() => {
    speechSynthesis.cancel();
    ttsQueueRef.current = [];
    isSpeakingRef.current = false;
  }, []);

  const speakNext = useCallback(() => {
    if (!activeRef.current) return;
    if (ttsQueueRef.current.length === 0) {
      isSpeakingRef.current = false;
      // Done speaking — go back to listening
      transition('listening');
      accumulatedTranscriptRef.current = '';
      setInterimTranscript('');
      setFinalTranscript('');
      ensureRecognition();
      return;
    }

    const text = ttsQueueRef.current.shift()!;
    isSpeakingRef.current = true;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    if (selectedVoiceRef.current) {
      utterance.voice = selectedVoiceRef.current;
    }

    utterance.onend = () => speakNext();
    utterance.onerror = () => speakNext();

    speechSynthesis.speak(utterance);
  }, [transition, ensureRecognition]);

  /** Queue a sentence for TTS. Call this as text streams in. */
  const enqueueSpeech = useCallback((text: string) => {
    if (!activeRef.current || !text.trim()) return;
    ttsQueueRef.current.push(text.trim());
    if (!isSpeakingRef.current) {
      transition('speaking');
      speakNext();
    }
  }, [transition, speakNext]);

  // Text buffer for accumulating streamed tokens into sentences
  const textBufferRef = useRef('');

  /** Feed streaming text deltas. Automatically splits into sentences and enqueues. */
  const feedStreamingText = useCallback((delta: string) => {
    if (!activeRef.current) return;
    textBufferRef.current += delta;

    // Split on sentence boundaries
    const sentencePattern = /([^.!?]*[.!?])\s*/g;
    let match: RegExpExecArray | null;
    let lastIndex = 0;

    while ((match = sentencePattern.exec(textBufferRef.current)) !== null) {
      const sentence = match[1].trim();
      if (sentence.length > 5) { // Skip very short fragments
        enqueueSpeech(sentence);
      }
      lastIndex = sentencePattern.lastIndex;
    }

    // Keep the remainder (incomplete sentence) in the buffer
    textBufferRef.current = textBufferRef.current.slice(lastIndex);
  }, [enqueueSpeech]);

  /** Flush any remaining buffered text as speech. Call when streaming is done. */
  const flushStreamingText = useCallback(() => {
    if (textBufferRef.current.trim()) {
      enqueueSpeech(textBufferRef.current.trim());
      textBufferRef.current = '';
    } else if (!isSpeakingRef.current && activeRef.current) {
      // Nothing to speak and nothing queued — go back to listening
      transition('listening');
      ensureRecognition();
    }
  }, [enqueueSpeech, transition, ensureRecognition]);

  // ---------------------------------------------------------------------------
  // Conversation lifecycle
  // ---------------------------------------------------------------------------

  const startConversation = useCallback(() => {
    activeRef.current = true;
    accumulatedTranscriptRef.current = '';
    textBufferRef.current = '';
    ttsQueueRef.current = [];
    setInterimTranscript('');
    setFinalTranscript('');
    transition('listening');
    ensureRecognition();
  }, [transition, ensureRecognition]);

  const stopConversation = useCallback(() => {
    activeRef.current = false;
    destroyRecognition();
    cancelTTS();
    accumulatedTranscriptRef.current = '';
    textBufferRef.current = '';
    setInterimTranscript('');
    setFinalTranscript('');
    transition('idle');
  }, [destroyRecognition, cancelTTS, transition]);

  /** Interrupt TTS and resume listening immediately */
  const interrupt = useCallback(() => {
    cancelTTS();
    textBufferRef.current = '';
    if (activeRef.current) {
      transition('listening');
      ensureRecognition();
    }
  }, [cancelTTS, transition, ensureRecognition]);

  /** Speak a complete text (not streamed). Used for initial messages. */
  const speakImmediate = useCallback((text: string) => {
    if (!activeRef.current || !text.trim()) return;
    cancelTTS(); // Clear any existing queue
    transition('speaking');
    // Stop recognition during TTS to avoid echo pickup
    destroyRecognition();
    ttsQueueRef.current = [];

    // Split into sentences and enqueue all
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    for (const s of sentences) {
      if (s.trim()) ttsQueueRef.current.push(s.trim());
    }
    speakNext();
  }, [cancelTTS, transition, destroyRecognition, speakNext]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      activeRef.current = false;
      speechSynthesis.cancel();
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch { /* */ }
      }
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    };
  }, []);

  return {
    /** Current state in the conversation loop */
    state,
    /** What the user is currently saying (interim, updates in real-time) */
    interimTranscript,
    /** The last committed user utterance */
    finalTranscript,
    /** Whether the browser supports speech APIs */
    isSupported,
    /** Start the voice conversation loop */
    startConversation,
    /** Stop everything and go idle */
    stopConversation,
    /** Interrupt TTS and go back to listening */
    interrupt,
    /** Feed a streaming text delta for sentence-buffered TTS */
    feedStreamingText,
    /** Flush remaining buffered text after streaming completes */
    flushStreamingText,
    /** Speak a complete text immediately (for initial messages) */
    speakImmediate,
  };
}
