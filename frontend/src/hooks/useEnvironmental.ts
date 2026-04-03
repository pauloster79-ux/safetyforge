import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { EnvironmentalProgram, ExposureRecord, SwpppInspection } from '@/lib/constants';

interface ExposureSummaryEntry {
  agent_name: string;
  total_samples: number;
  above_action_level: number;
  above_pel: number;
  average_exposure: number;
}

interface ExposureSummaryResponse {
  summaries: ExposureSummaryEntry[];
  total_samples: number;
}

interface ComplianceStatusResponse {
  overall_status: string;
  areas: {
    area: string;
    status: string;
    details: string;
  }[];
  total_programs: number;
}

export function useEnvironmentalPrograms() {
  return useQuery<EnvironmentalProgram[]>({
    queryKey: ['environmental-programs'],
    queryFn: async () => {
      const response = await api.get<{ programs: EnvironmentalProgram[]; total: number }>(
        '/me/environmental/programs',
      );
      return response.programs;
    },
  });
}

export function useCreateEnvironmentalProgram() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<EnvironmentalProgram>) =>
      api.post<EnvironmentalProgram>('/me/environmental/programs', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environmental-programs'] });
      queryClient.invalidateQueries({ queryKey: ['environmental-compliance'] });
    },
  });
}

export function useExposureRecords(projectId?: string) {
  return useQuery<ExposureRecord[]>({
    queryKey: ['exposure-records', projectId],
    queryFn: async () => {
      const response = await api.get<{ records: ExposureRecord[]; total: number }>(
        `/me/projects/${projectId}/exposure-records`,
      );
      return response.records;
    },
    enabled: !!projectId,
  });
}

export function useCreateExposureRecord(projectId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<ExposureRecord>) => {
      if (!projectId) throw new Error('Project ID is required for exposure records');
      return api.post<ExposureRecord>(`/me/projects/${projectId}/exposure-records`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exposure-records', projectId] });
      queryClient.invalidateQueries({ queryKey: ['exposure-summary', projectId] });
      queryClient.invalidateQueries({ queryKey: ['environmental-compliance'] });
    },
  });
}

export function useExposureSummary(projectId?: string) {
  return useQuery<ExposureSummaryResponse>({
    queryKey: ['exposure-summary', projectId],
    queryFn: () =>
      api.get<ExposureSummaryResponse>(
        `/me/projects/${projectId}/exposure-records/summary`,
      ),
    enabled: !!projectId,
  });
}

export function useSwpppInspections(projectId?: string) {
  return useQuery<SwpppInspection[]>({
    queryKey: ['swppp-inspections', projectId],
    queryFn: async () => {
      const response = await api.get<{ inspections: SwpppInspection[]; total: number }>(
        `/me/projects/${projectId}/swppp-inspections`,
      );
      return response.inspections;
    },
    enabled: !!projectId,
  });
}

export function useCreateSwpppInspection(projectId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<SwpppInspection>) => {
      if (!projectId) throw new Error('Project ID is required for SWPPP inspections');
      return api.post<SwpppInspection>(`/me/projects/${projectId}/swppp-inspections`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['swppp-inspections', projectId] });
      queryClient.invalidateQueries({ queryKey: ['environmental-compliance'] });
    },
  });
}

export function useEnvironmentalCompliance() {
  return useQuery<ComplianceStatusResponse>({
    queryKey: ['environmental-compliance'],
    queryFn: () => api.get<ComplianceStatusResponse>('/me/environmental/compliance-status'),
  });
}
