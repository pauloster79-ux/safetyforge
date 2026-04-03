import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Project } from '@/lib/constants';

interface ProjectListParams {
  status?: string;
}

interface CreateProjectPayload {
  name: string;
  address: string;
  client_name?: string;
  project_type?: string;
  trade_types?: string[];
  start_date?: string | null;
  end_date?: string | null;
  estimated_workers?: number;
  description?: string;
  special_hazards?: string;
  nearest_hospital?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
}

interface UpdateProjectPayload {
  id: string;
  name?: string;
  address?: string;
  client_name?: string;
  project_type?: string;
  trade_types?: string[];
  start_date?: string | null;
  end_date?: string | null;
  estimated_workers?: number;
  description?: string;
  special_hazards?: string;
  nearest_hospital?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  status?: 'active' | 'completed' | 'on_hold';
}

export function useProjects(params?: ProjectListParams) {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  const queryString = searchParams.toString();
  const endpoint = queryString ? `/me/projects?${queryString}` : '/me/projects';

  return useQuery<Project[]>({
    queryKey: ['projects', params],
    queryFn: async () => {
      const response = await api.get<{ projects: Project[]; total: number }>(endpoint);
      return response.projects;
    },
  });
}

export function useProject(id: string | undefined) {
  return useQuery<Project>({
    queryKey: ['projects', id],
    queryFn: () => api.get<Project>(`/me/projects/${id}`),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateProjectPayload) =>
      api.post<Project>('/me/projects', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateProjectPayload) =>
      api.patch<Project>(`/me/projects/${id}`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.setQueryData(['projects', data.id], data);
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/me/projects/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}
