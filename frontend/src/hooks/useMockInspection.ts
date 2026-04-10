import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { MockInspectionResult } from '@/lib/constants';

interface RunMockInspectionPayload {
  project_id?: string;
  inspection_id?: string;
}

export function useRunMockInspection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data?: RunMockInspectionPayload) => {
      const inspectionId = data?.inspection_id || 'latest';
      return api.post<MockInspectionResult>(`/me/inspections/${inspectionId}/run-mock`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mock-inspection-results'] });
    },
  });
}

export function useMockInspectionResults() {
  return useQuery<MockInspectionResult[]>({
    queryKey: ['mock-inspection-results'],
    queryFn: async () => {
      const response = await api.get<{ results: MockInspectionResult[]; total: number } | MockInspectionResult[]>(
        '/me/mock-inspection/results',
      );
      // Handle both envelope and raw array responses
      if (Array.isArray(response)) return response;
      return response.results ?? [];
    },
  });
}

export function useMockInspectionResult(id: string | undefined) {
  return useQuery<MockInspectionResult>({
    queryKey: ['mock-inspection-results', id],
    queryFn: () => api.get<MockInspectionResult>(`/me/mock-inspection/results/${id}`),
    enabled: !!id,
  });
}
