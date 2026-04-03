import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { SafetyMetrics, EmrEstimate } from '@/lib/constants';

export function useAnalyticsDashboard() {
  return useQuery<SafetyMetrics>({
    queryKey: ['analytics', 'dashboard'],
    queryFn: () => api.get<SafetyMetrics>('/me/analytics/dashboard'),
  });
}

interface EmrEstimatePayload {
  current_emr: number;
  annual_payroll: number;
  wc_rate: number;
}

export function useEmrEstimate() {
  return useMutation({
    mutationFn: (data: EmrEstimatePayload) =>
      api.post<EmrEstimate>('/me/analytics/emr-estimate', data),
  });
}
