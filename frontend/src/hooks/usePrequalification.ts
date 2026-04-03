import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { PrequalPackage } from '@/lib/constants';

interface GeneratePackagePayload {
  platform: string;
  client_name: string;
}

export function useGeneratePackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GeneratePackagePayload) =>
      api.post<PrequalPackage>('/me/prequalification/generate', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prequalification', 'packages'] });
    },
  });
}

export function usePrequalPackages() {
  return useQuery<PrequalPackage[]>({
    queryKey: ['prequalification', 'packages'],
    queryFn: () => api.get<PrequalPackage[]>('/me/prequalification/packages'),
  });
}

export function usePrequalPackage(packageId: string | undefined) {
  return useQuery<PrequalPackage>({
    queryKey: ['prequalification', 'packages', packageId],
    queryFn: () => api.get<PrequalPackage>(`/me/prequalification/packages/${packageId}`),
    enabled: !!packageId,
  });
}

export function usePrequalRequirements(platform: string) {
  return useQuery<string[]>({
    queryKey: ['prequalification', 'requirements', platform],
    queryFn: () => api.get<string[]>(`/me/prequalification/requirements?platform=${platform}`),
    enabled: !!platform,
  });
}
