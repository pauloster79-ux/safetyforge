import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Assumption } from '@/lib/constants';

export function useAssumptions(projectId: string | undefined) {
  return useQuery<Assumption[]>({
    queryKey: ['assumptions', projectId],
    queryFn: async () => {
      const response = await api.get<{ assumptions: Assumption[]; total: number }>(
        `/me/projects/${projectId}/assumptions`,
      );
      return response.assumptions;
    },
    enabled: !!projectId,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
