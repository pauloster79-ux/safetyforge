import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface ProjectAssignment {
  id: string;
  company_id: string;
  resource_type: 'worker' | 'equipment';
  resource_id: string;
  project_id: string;
  role: string | null;
  start_date: string;
  end_date: string | null;
  status: 'active' | 'completed' | 'transferred';
  notes: string | null;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

interface AssignmentListParams {
  project_id?: string;
  resource_type?: 'worker' | 'equipment';
  resource_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

interface CreateAssignmentPayload {
  resource_type: 'worker' | 'equipment';
  resource_id: string;
  project_id: string;
  role?: string;
  start_date: string;
  end_date?: string;
  status?: string;
  notes?: string;
}

interface UpdateAssignmentPayload {
  id: string;
  role?: string;
  start_date?: string;
  end_date?: string;
  status?: string;
  notes?: string;
}

export function useProjectAssignments(params?: AssignmentListParams) {
  const searchParams = new URLSearchParams();
  if (params?.project_id) searchParams.set('project_id', params.project_id);
  if (params?.resource_type) searchParams.set('resource_type', params.resource_type);
  if (params?.resource_id) searchParams.set('resource_id', params.resource_id);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));
  const queryString = searchParams.toString();
  const endpoint = queryString ? `/me/assignments?${queryString}` : '/me/assignments';

  return useQuery<ProjectAssignment[]>({
    queryKey: ['assignments', params],
    queryFn: async () => {
      const response = await api.get<{ assignments: ProjectAssignment[]; total: number }>(endpoint);
      return response.assignments;
    },
  });
}

export function useCreateAssignment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAssignmentPayload) =>
      api.post<ProjectAssignment>('/me/assignments', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });
}

export function useUpdateAssignment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateAssignmentPayload) =>
      api.patch<ProjectAssignment>(`/me/assignments/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });
}

export function useDeleteAssignment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/me/assignments/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });
}
