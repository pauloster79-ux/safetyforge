import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface AuditEvent {
  id: string;
  event_type: string;
  entity_id: string;
  entity_type: string;
  company_id: string;
  occurred_at: string;
  actor_type: 'human' | 'agent';
  actor_id: string;
  agent_id: string | null;
  agent_version: string | null;
  model_id: string | null;
  confidence: number | null;
  cost_cents: number | null;
  summary: string;
  changes: Record<string, { from: unknown; to: unknown }> | null;
  prev_state: string | null;
  new_state: string | null;
  caused_by_event_id: string | null;
  related_entity_ids: string[] | null;
}

export interface ActivityStreamResponse {
  events: AuditEvent[];
  total: number;
  has_more: boolean;
}

export function useProjectActivity(projectId: string | undefined, limit = 50) {
  return useQuery<ActivityStreamResponse>({
    queryKey: ['activity', 'project', projectId, limit],
    queryFn: () => api.get(`/me/projects/${projectId}/activity?limit=${limit}`),
    enabled: !!projectId,
  });
}

export function useWorkerActivity(workerId: string | undefined, limit = 50) {
  return useQuery<ActivityStreamResponse>({
    queryKey: ['activity', 'worker', workerId, limit],
    queryFn: () => api.get(`/me/workers/${workerId}/activity?limit=${limit}`),
    enabled: !!workerId,
  });
}

export function useWorkItemActivity(workItemId: string | undefined, limit = 50) {
  return useQuery<ActivityStreamResponse>({
    queryKey: ['activity', 'work-item', workItemId, limit],
    queryFn: () => api.get(`/me/work-items/${workItemId}/activity?limit=${limit}`),
    enabled: !!workItemId,
  });
}

export function useCompanyActivity(limit = 50) {
  return useQuery<ActivityStreamResponse>({
    queryKey: ['activity', 'company', limit],
    queryFn: () => api.get(`/me/activity?limit=${limit}`),
  });
}
