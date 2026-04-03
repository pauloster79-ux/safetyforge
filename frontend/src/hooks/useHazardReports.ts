import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { HazardReport } from '@/lib/constants';

interface HazardReportListParams {
  status?: string;
}

interface CreateHazardReportPayload {
  photo_url: string;
  description: string;
  location: string;
  identified_hazards: HazardReport['identified_hazards'];
  hazard_count: number;
  highest_severity: string | null;
  ai_analysis: Record<string, unknown>;
}

interface UpdateHazardReportPayload {
  id: string;
  status?: HazardReport['status'];
  corrective_action_taken?: string;
}

interface AnalyzePhotoResponse {
  identified_hazards: HazardReport['identified_hazards'];
  hazard_count: number;
  highest_severity: string | null;
  scene_description: string;
  positive_observations: string[];
  summary: string;
}

export function useHazardReports(projectId: string | undefined, params?: HazardReportListParams) {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  const queryString = searchParams.toString();
  const base = `/me/projects/${projectId}/hazard-reports`;
  const endpoint = queryString ? `${base}?${queryString}` : base;

  return useQuery<HazardReport[]>({
    queryKey: ['hazard-reports', projectId, params],
    queryFn: async () => {
      const response = await api.get<{ reports: HazardReport[]; total: number }>(endpoint);
      return response.reports;
    },
    enabled: !!projectId,
  });
}

export function useHazardReport(projectId: string | undefined, id: string | undefined) {
  return useQuery<HazardReport>({
    queryKey: ['hazard-reports', projectId, id],
    queryFn: () => api.get<HazardReport>(`/me/projects/${projectId}/hazard-reports/${id}`),
    enabled: !!projectId && !!id,
  });
}

export function useCreateHazardReport(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateHazardReportPayload) =>
      api.post<HazardReport>(`/me/projects/${projectId}/hazard-reports`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hazard-reports', projectId] });
    },
  });
}

export function useUpdateHazardReport(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateHazardReportPayload) =>
      api.patch<HazardReport>(`/me/projects/${projectId}/hazard-reports/${id}`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['hazard-reports', projectId] });
      queryClient.setQueryData(['hazard-reports', projectId, data.id], data);
    },
  });
}

export function useAnalyzePhoto() {
  return useMutation({
    mutationFn: (data: { photo_base64: string; description?: string; location?: string }) =>
      api.post<AnalyzePhotoResponse>('/me/analyze-photo', data),
  });
}
