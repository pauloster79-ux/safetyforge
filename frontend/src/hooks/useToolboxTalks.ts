import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ToolboxTalk } from '@/lib/constants';

interface ToolboxTalkListParams {
  status?: string;
}

interface CreateToolboxTalkPayload {
  topic: string;
  target_audience: string;
  target_trade?: string | null;
  duration_minutes: number;
  custom_points?: string;
}

interface UpdateToolboxTalkPayload {
  id: string;
  overall_notes?: string;
  presented_by?: string;
  status?: 'scheduled' | 'in_progress' | 'completed';
}

interface AddAttendeePayload {
  id: string;
  worker_name: string;
  language_preference: 'en' | 'es';
}

export function useToolboxTalks(projectId: string | undefined, params?: ToolboxTalkListParams) {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  const queryString = searchParams.toString();
  const base = `/me/projects/${projectId}/toolbox-talks`;
  const endpoint = queryString ? `${base}?${queryString}` : base;

  return useQuery<ToolboxTalk[]>({
    queryKey: ['toolbox-talks', projectId, params],
    queryFn: async () => {
      const response = await api.get<{ toolbox_talks: ToolboxTalk[]; total: number }>(endpoint);
      return response.toolbox_talks;
    },
    enabled: !!projectId,
  });
}

export function useToolboxTalk(projectId: string | undefined, id: string | undefined) {
  return useQuery<ToolboxTalk>({
    queryKey: ['toolbox-talks', projectId, id],
    queryFn: () => api.get<ToolboxTalk>(`/me/projects/${projectId}/toolbox-talks/${id}`),
    enabled: !!projectId && !!id,
  });
}

export function useCreateToolboxTalk(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateToolboxTalkPayload) =>
      api.post<ToolboxTalk>(`/me/projects/${projectId}/toolbox-talks`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['toolbox-talks', projectId] });
    },
  });
}

export function useUpdateToolboxTalk(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateToolboxTalkPayload) =>
      api.patch<ToolboxTalk>(`/me/projects/${projectId}/toolbox-talks/${id}`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['toolbox-talks', projectId] });
      queryClient.setQueryData(['toolbox-talks', projectId, data.id], data);
    },
  });
}

export function useDeleteToolboxTalk(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/me/projects/${projectId}/toolbox-talks/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['toolbox-talks', projectId] });
    },
  });
}

export function useAddAttendee(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: AddAttendeePayload) =>
      api.post<ToolboxTalk>(`/me/projects/${projectId}/toolbox-talks/${id}/attend`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['toolbox-talks', projectId] });
      queryClient.setQueryData(['toolbox-talks', projectId, data.id], data);
    },
  });
}

export function useCompleteTalk(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.post<ToolboxTalk>(`/me/projects/${projectId}/toolbox-talks/${id}/complete`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['toolbox-talks', projectId] });
      queryClient.setQueryData(['toolbox-talks', projectId, data.id], data);
    },
  });
}
