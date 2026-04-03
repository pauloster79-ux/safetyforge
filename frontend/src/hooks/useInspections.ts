import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Inspection, InspectionTemplate } from '@/lib/constants';

interface InspectionListParams {
  type?: string;
}

interface CreateInspectionPayload {
  inspection_type: string;
  inspection_date: string;
  inspector_name: string;
  weather_conditions: string;
  temperature: string;
  wind_conditions: string;
  workers_on_site: number;
  items: {
    item_id: string;
    category: string;
    description: string;
    status: 'pass' | 'fail' | 'na';
    notes: string;
    photo_url: string | null;
  }[];
  overall_notes: string;
  corrective_actions_needed: string;
  overall_status: 'pass' | 'fail' | 'partial';
}

interface UpdateInspectionPayload {
  id: string;
  overall_notes?: string;
  corrective_actions_needed?: string;
  overall_status?: 'pass' | 'fail' | 'partial';
}

export function useInspections(projectId: string | undefined, params?: InspectionListParams) {
  const searchParams = new URLSearchParams();
  if (params?.type) searchParams.set('type', params.type);
  const queryString = searchParams.toString();
  const base = `/me/projects/${projectId}/inspections`;
  const endpoint = queryString ? `${base}?${queryString}` : base;

  return useQuery<Inspection[]>({
    queryKey: ['inspections', projectId, params],
    queryFn: async () => {
      const response = await api.get<{ inspections: Inspection[]; total: number }>(endpoint);
      return response.inspections;
    },
    enabled: !!projectId,
  });
}

export function useInspection(projectId: string | undefined, id: string | undefined) {
  return useQuery<Inspection>({
    queryKey: ['inspections', projectId, id],
    queryFn: () => api.get<Inspection>(`/me/projects/${projectId}/inspections/${id}`),
    enabled: !!projectId && !!id,
  });
}

export function useCreateInspection(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateInspectionPayload) =>
      api.post<Inspection>(`/me/projects/${projectId}/inspections`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inspections', projectId] });
    },
  });
}

export function useUpdateInspection(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateInspectionPayload) =>
      api.patch<Inspection>(`/me/projects/${projectId}/inspections/${id}`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['inspections', projectId] });
      queryClient.setQueryData(['inspections', projectId, data.id], data);
    },
  });
}

export function useDeleteInspection(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/me/projects/${projectId}/inspections/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inspections', projectId] });
    },
  });
}

export function useInspectionTemplate(type: string) {
  return useQuery<InspectionTemplate>({
    queryKey: ['inspection-templates', type],
    queryFn: () => api.get<InspectionTemplate>(`/me/inspection-templates/${type}`),
    enabled: !!type,
  });
}
