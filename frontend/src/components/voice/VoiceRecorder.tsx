import { useState } from 'react';
import { Mic, MicOff, Loader2, Square, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
import { useTranscribe } from '@/hooks/useVoiceTranscription';

interface VoiceRecorderProps {
  onTranscript: (transcript: string) => void;
  className?: string;
  compact?: boolean;
  placeholder?: string;
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function VoiceRecorder({
  onTranscript,
  className,
  compact = false,
  placeholder = 'Tap to record',
}: VoiceRecorderProps) {
  const { state, duration, error, startRecording, stopRecording, cancelRecording } =
    useVoiceRecorder();
  const transcribe = useTranscribe();
  const [transcript, setTranscript] = useState('');

  const handleToggle = async () => {
    if (state === 'idle') {
      setTranscript('');
      await startRecording();
    } else if (state === 'recording') {
      const result = await stopRecording();
      if (result) {
        try {
          const response = await transcribe.mutateAsync({
            audio_base64: result.base64,
            media_type: result.mediaType,
          });
          setTranscript(response.transcript);
          onTranscript(response.transcript);
        } catch {
          // Error handled by React Query
        }
      }
    }
  };

  const isProcessing = state === 'processing' || transcribe.isPending;

  if (compact) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <Button
          type="button"
          variant={state === 'recording' ? 'destructive' : 'outline'}
          size="icon"
          className={cn(
            'h-9 w-9 shrink-0',
            state === 'recording' && 'animate-pulse',
          )}
          onClick={handleToggle}
          disabled={isProcessing}
        >
          {isProcessing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : state === 'recording' ? (
            <Square className="h-3.5 w-3.5" />
          ) : (
            <Mic className="h-4 w-4" />
          )}
        </Button>
        {state === 'recording' && (
          <span className="text-xs font-mono text-destructive">
            {formatDuration(duration)}
          </span>
        )}
        {isProcessing && (
          <span className="text-xs text-muted-foreground">Transcribing...</span>
        )}
        {error && (
          <span className="text-xs text-destructive">{error}</span>
        )}
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center gap-3">
        <Button
          type="button"
          variant={state === 'recording' ? 'destructive' : 'outline'}
          size="sm"
          className={cn(state === 'recording' && 'animate-pulse')}
          onClick={handleToggle}
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Transcribing...
            </>
          ) : state === 'recording' ? (
            <>
              <Square className="mr-2 h-3.5 w-3.5" />
              Stop Recording ({formatDuration(duration)})
            </>
          ) : (
            <>
              <Mic className="mr-2 h-4 w-4" />
              {placeholder}
            </>
          )}
        </Button>

        {state === 'recording' && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={cancelRecording}
          >
            <MicOff className="mr-2 h-4 w-4" />
            Cancel
          </Button>
        )}
      </div>

      {state === 'recording' && (
        <div className="flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-2">
          <div className="h-2 w-2 rounded-full bg-destructive animate-pulse" />
          <span className="text-sm text-destructive font-medium">
            Recording... speak clearly
          </span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-2">
          <AlertCircle className="h-4 w-4 text-destructive" />
          <span className="text-sm text-destructive">{error}</span>
        </div>
      )}

      {transcribe.isError && (
        <div className="flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-2">
          <AlertCircle className="h-4 w-4 text-destructive" />
          <span className="text-sm text-destructive">
            Transcription failed. Please try again.
          </span>
        </div>
      )}

      {transcript && (
        <div className="rounded-md border border-border bg-muted/50 p-3">
          <p className="text-xs font-medium text-muted-foreground mb-1">Transcript</p>
          <p className="text-sm text-foreground">{transcript}</p>
        </div>
      )}
    </div>
  );
}
