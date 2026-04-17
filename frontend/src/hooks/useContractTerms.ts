import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface PaymentMilestone {
  id: string;
  description: string;
  percentage: number | null;
  amount_cents: number | null;
  trigger_condition: string;
  status: 'pending' | 'invoiced' | 'paid';
  created_at: string;
  updated_at: string;
}

export interface Condition {
  id: string;
  category: string;
  description: string;
  responsible_party: string;
  created_at: string;
  updated_at: string;
}

export interface Warranty {
  id: string;
  period_months: number;
  scope: string;
  start_trigger: string;
  terms: string;
  created_at: string;
  updated_at: string;
}

export interface ContractDetail {
  id: string;
  retention_pct: number | null;
  payment_terms_days: number | null;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Query hooks
// ---------------------------------------------------------------------------

/** Safe fetch that returns null on 404 (no contract yet). */
async function safeGet<T>(url: string): Promise<T | null> {
  try {
    return await api.get<T>(url);
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'status' in err && (err as { status: number }).status === 404) {
      return null;
    }
    throw err;
  }
}

export function usePaymentMilestones(projectId: string | undefined) {
  return useQuery<PaymentMilestone[]>({
    queryKey: ['payment-milestones', projectId],
    queryFn: async () => {
      const response = await safeGet<{ milestones: PaymentMilestone[]; total: number }>(
        `/me/projects/${projectId}/contract/payment-milestones`,
      );
      return response?.milestones ?? [];
    },
    enabled: !!projectId,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useConditions(projectId: string | undefined) {
  return useQuery<Condition[]>({
    queryKey: ['conditions', projectId],
    queryFn: async () => {
      const response = await safeGet<{ conditions: Condition[]; total: number }>(
        `/me/projects/${projectId}/contract/conditions`,
      );
      return response?.conditions ?? [];
    },
    enabled: !!projectId,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useWarranty(projectId: string | undefined) {
  return useQuery<Warranty | null>({
    queryKey: ['warranty', projectId],
    queryFn: () =>
      safeGet<Warranty>(`/me/projects/${projectId}/contract/warranty`),
    enabled: !!projectId,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useContractDetail(projectId: string | undefined) {
  return useQuery<ContractDetail | null>({
    queryKey: ['contract-detail', projectId],
    queryFn: () =>
      safeGet<ContractDetail>(`/me/projects/${projectId}/contract`),
    enabled: !!projectId,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks — Payment Milestones
// ---------------------------------------------------------------------------

interface CreatePaymentMilestonePayload {
  description: string;
  percentage?: number | null;
  amount_cents?: number | null;
  trigger_condition?: string;
  status?: string;
}

interface UpdatePaymentMilestonePayload {
  id: string;
  description?: string;
  percentage?: number | null;
  amount_cents?: number | null;
  trigger_condition?: string;
  status?: string;
}

export function useCreatePaymentMilestone(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePaymentMilestonePayload) =>
      api.post<PaymentMilestone>(
        `/me/projects/${projectId}/contract/payment-milestones`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payment-milestones', projectId] });
    },
  });
}

export function useUpdatePaymentMilestone(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdatePaymentMilestonePayload) =>
      api.patch<PaymentMilestone>(
        `/me/projects/${projectId}/contract/payment-milestones/${id}`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payment-milestones', projectId] });
    },
  });
}

export function useDeletePaymentMilestone(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/me/projects/${projectId}/contract/payment-milestones/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payment-milestones', projectId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks — Conditions
// ---------------------------------------------------------------------------

interface CreateConditionPayload {
  category: string;
  description: string;
  responsible_party?: string;
}

interface UpdateConditionPayload {
  id: string;
  category?: string;
  description?: string;
  responsible_party?: string;
}

export function useCreateCondition(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateConditionPayload) =>
      api.post<Condition>(
        `/me/projects/${projectId}/contract/conditions`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
    },
  });
}

export function useUpdateCondition(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateConditionPayload) =>
      api.patch<Condition>(
        `/me/projects/${projectId}/contract/conditions/${id}`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
    },
  });
}

export function useDeleteCondition(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/me/projects/${projectId}/contract/conditions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks — Warranty
// ---------------------------------------------------------------------------

interface SetWarrantyPayload {
  period_months: number;
  scope: string;
  start_trigger?: string;
  terms?: string;
}

export function useSetWarranty(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SetWarrantyPayload) =>
      api.post<Warranty>(
        `/me/projects/${projectId}/contract/warranty`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['warranty', projectId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks — Contract (retention / payment terms)
// ---------------------------------------------------------------------------

interface UpdateContractPayload {
  retention_pct?: number | null;
  payment_terms_days?: number | null;
}

export function useUpdateContract(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateContractPayload) =>
      api.patch<ContractDetail>(
        `/me/projects/${projectId}/contract`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contract-detail', projectId] });
    },
  });
}
