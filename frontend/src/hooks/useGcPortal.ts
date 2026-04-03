import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { GcRelationship, SubComplianceSummary } from '@/lib/constants';

interface GcDashboardData {
  relationships: GcRelationship[];
  compliance: SubComplianceSummary[];
}

interface InviteSubPayload {
  email: string;
  project_name: string;
}

export function useMySubs() {
  return useQuery<GcRelationship[]>({
    queryKey: ['gc-portal', 'subs'],
    queryFn: () => api.get<GcRelationship[]>('/me/gc-portal/my-subs'),
  });
}

export function useMyGcs() {
  return useQuery<GcRelationship[]>({
    queryKey: ['gc-portal', 'gcs'],
    queryFn: () => api.get<GcRelationship[]>('/me/gc-portal/my-gcs'),
  });
}

export function useSubCompliance(subId: string | undefined) {
  return useQuery<SubComplianceSummary>({
    queryKey: ['gc-portal', 'subs', subId, 'compliance'],
    queryFn: () => api.get<SubComplianceSummary>(`/me/gc-portal/my-subs/${subId}/compliance`),
    enabled: !!subId,
  });
}

export function useGcDashboard() {
  return useQuery<GcDashboardData>({
    queryKey: ['gc-portal', 'dashboard'],
    queryFn: () => api.get<GcDashboardData>('/me/gc-portal/dashboard'),
  });
}

export function useInviteSub() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InviteSubPayload) =>
      api.post<GcRelationship>('/me/gc-portal/invite', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gc-portal'] });
    },
  });
}
