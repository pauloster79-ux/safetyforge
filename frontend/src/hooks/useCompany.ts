import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Company, Subscription } from '@/lib/constants';

interface UpdateCompanyPayload {
  name?: string;
  address?: string;
  phone?: string;
  email?: string;
  license_number?: string;
  trade_type?: string;
  owner_name?: string;
  ein?: string | null;
  safety_officer?: string | null;
  safety_officer_phone?: string | null;
}

export function useCompany() {
  return useQuery<Company>({
    queryKey: ['company'],
    queryFn: () => api.get<Company>('/me/company'),
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateCompanyPayload) =>
      api.patch<Company>('/me/company', data),
    onSuccess: (data) => {
      queryClient.setQueryData(['company'], data);
    },
  });
}

export function useSubscription() {
  return useQuery<Subscription>({
    queryKey: ['subscription'],
    queryFn: () => api.get<Subscription>('/me/subscription'),
  });
}

export function useUpgradeSubscription() {
  return useMutation({
    mutationFn: async (tier: string) => {
      const data = await api.post<{ checkout_url: string }>(
        '/me/subscription/create-checkout',
        { tier },
      );
      window.location.href = data.checkout_url;
      return data;
    },
  });
}
