import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Exclusion } from '@/lib/constants';

export function useExclusions(projectId: string | undefined) {
  return useQuery<Exclusion[]>({
    queryKey: ['exclusions', projectId],
    queryFn: async () => {
      const response = await api.get<{ exclusions: Exclusion[]; total: number }>(
        `/me/projects/${projectId}/exclusions`,
      );
      return response.exclusions;
    },
    enabled: !!projectId,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
