import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { DailyLog } from '@/lib/constants';

interface DailyLogListParams {
  status?: string;
}

interface CreateDailyLogPayload {
  log_date: string;
  superintendent_name: string;
  weather?: {
    conditions: string;
    temperature_high: string;
    temperature_low: string;
    wind: string;
    precipitation: string;
  };
  workers_on_site?: number;
  work_performed?: string;
  materials_delivered?: Array<{
    material: string;
    quantity: string;
    supplier: string;
    received_by: string;
    notes: string;
  }>;
  delays?: Array<{
    delay_type: string;
    duration_hours: number;
    description: string;
    impact: string;
  }>;
  visitors?: Array<{
    name: string;
    company: string;
    purpose: string;
    time_in: string;
    time_out: string;
  }>;
  safety_incidents?: string;
  equipment_used?: string;
  notes?: string;
}

interface UpdateDailyLogPayload extends Partial<CreateDailyLogPayload> {
  id: string;
}

export function useDailyLogs(projectId: string | undefined, params?: DailyLogListParams) {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  const queryString = searchParams.toString();
  const base = `/me/projects/${projectId}/daily-logs`;
  const endpoint = queryString ? `${base}?${queryString}` : base;

  return useQuery<DailyLog[]>({
    queryKey: ['daily-logs', projectId, params],
    queryFn: async () => {
      const response = await api.get<{ daily_logs: DailyLog[]; total: number }>(endpoint);
      return response.daily_logs;
    },
    enabled: !!projectId,
  });
}

export function useDailyLog(projectId: string | undefined, id: string | undefined) {
  return useQuery<DailyLog>({
    queryKey: ['daily-logs', projectId, id],
    queryFn: () => api.get<DailyLog>(`/me/projects/${projectId}/daily-logs/${id}`),
    enabled: !!projectId && !!id,
  });
}

export function useCreateDailyLog(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateDailyLogPayload) =>
      api.post<DailyLog>(`/me/projects/${projectId}/daily-logs`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-logs', projectId] });
    },
  });
}

export function useUpdateDailyLog(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateDailyLogPayload) =>
      api.patch<DailyLog>(`/me/projects/${projectId}/daily-logs/${id}`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['daily-logs', projectId] });
      queryClient.setQueryData(['daily-logs', projectId, data.id], data);
    },
  });
}

export function useDeleteDailyLog(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/me/projects/${projectId}/daily-logs/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-logs', projectId] });
    },
  });
}

export function useSubmitDailyLog(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.post<DailyLog>(`/me/projects/${projectId}/daily-logs/${id}/submit`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['daily-logs', projectId] });
      queryClient.setQueryData(['daily-logs', projectId, data.id], data);
    },
  });
}

export function useApproveDailyLog(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.post<DailyLog>(`/me/projects/${projectId}/daily-logs/${id}/approve`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['daily-logs', projectId] });
      queryClient.setQueryData(['daily-logs', projectId, data.id], data);
    },
  });
}
