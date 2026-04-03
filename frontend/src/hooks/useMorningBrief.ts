import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { MorningBrief } from '@/lib/constants';

export function useMorningBrief(projectId: string | undefined) {
  return useQuery<MorningBrief>({
    queryKey: ['morning-brief', projectId],
    queryFn: () => api.get<MorningBrief>(`/me/projects/${projectId}/morning-brief`),
    enabled: !!projectId,
  });
}

export function useMorningBriefHistory(projectId: string | undefined) {
  return useQuery<MorningBrief[]>({
    queryKey: ['morning-briefs', projectId],
    queryFn: async () => {
      const response = await api.get<{ briefs: MorningBrief[]; total: number }>(
        `/me/projects/${projectId}/morning-briefs`,
      );
      return response.briefs;
    },
    enabled: !!projectId,
  });
}
