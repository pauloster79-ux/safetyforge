import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface TranscribeResponse {
  transcript: string;
}

interface ParseInspectionResponse {
  items: {
    item_id: string;
    category: string;
    description: string;
    status: 'pass' | 'fail' | 'na';
    notes: string;
  }[];
  notes: string;
  corrective_actions: string;
}

interface ParseIncidentResponse {
  location: string;
  severity: string;
  description: string;
  persons_involved: string;
  witnesses: string;
  immediate_actions_taken: string;
}

export function useTranscribe() {
  return useMutation({
    mutationFn: (data: { audio_base64: string; media_type: string }) =>
      api.post<TranscribeResponse>('/me/voice/transcribe', data),
  });
}

export function useParseInspection() {
  return useMutation({
    mutationFn: (data: {
      transcript: string;
      inspection_type: string;
      checklist_template?: { item_id: string; category: string; description: string }[];
    }) => api.post<ParseInspectionResponse>('/me/voice/parse-inspection', data),
  });
}

export function useParseIncident() {
  return useMutation({
    mutationFn: (data: { transcript: string }) =>
      api.post<ParseIncidentResponse>('/me/voice/parse-incident', data),
  });
}
