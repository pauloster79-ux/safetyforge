import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Incident } from '@/lib/constants';

interface CreateIncidentPayload {
  incident_date: string;
  incident_time: string;
  location: string;
  severity: Incident['severity'];
  description: string;
  persons_involved: string;
  witnesses: string;
  immediate_actions_taken: string;
  photo_urls?: string[];
}

interface UpdateIncidentPayload {
  id: string;
  status?: Incident['status'];
  root_cause?: string;
  corrective_actions?: string;
  description?: string;
  persons_involved?: string;
  witnesses?: string;
  immediate_actions_taken?: string;
}

export function useIncidents(projectId: string | undefined) {
  return useQuery<Incident[]>({
    queryKey: ['incidents', projectId],
    queryFn: async () => {
      const response = await api.get<{ incidents: Incident[]; total: number }>(
        `/me/projects/${projectId}/incidents`,
      );
      return response.incidents;
    },
    enabled: !!projectId,
  });
}

export function useIncident(projectId: string | undefined, id: string | undefined) {
  return useQuery<Incident>({
    queryKey: ['incidents', projectId, id],
    queryFn: () => api.get<Incident>(`/me/projects/${projectId}/incidents/${id}`),
    enabled: !!projectId && !!id,
  });
}

export function useCreateIncident(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateIncidentPayload) =>
      api.post<Incident>(`/me/projects/${projectId}/incidents`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents', projectId] });
    },
  });
}

export function useUpdateIncident(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateIncidentPayload) =>
      api.patch<Incident>(`/me/projects/${projectId}/incidents/${id}`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['incidents', projectId] });
      queryClient.setQueryData(['incidents', projectId, data.id], data);
    },
  });
}

export function useDeleteIncident(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/me/projects/${projectId}/incidents/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents', projectId] });
    },
  });
}

export function useInvestigateIncident(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.post<Incident>(`/me/projects/${projectId}/incidents/${id}/investigate`, {}),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['incidents', projectId] });
      queryClient.setQueryData(['incidents', projectId, data.id], data);
    },
  });
}
