import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Worker, Certification } from '@/lib/constants';

interface WorkerListParams {
  status?: string;
  role?: string;
  trade?: string;
  search?: string;
}

interface CreateWorkerPayload {
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  role?: string;
  trade?: string;
  language_preference?: 'en' | 'es' | 'both';
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  hire_date?: string | null;
  notes?: string;
}

interface UpdateWorkerPayload {
  id: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  role?: string;
  trade?: string;
  language_preference?: 'en' | 'es' | 'both';
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  hire_date?: string | null;
  notes?: string;
  status?: 'active' | 'inactive' | 'terminated';
}

interface AddCertificationPayload {
  workerId: string;
  certification_type: string;
  custom_name?: string;
  issued_date: string;
  expiry_date?: string | null;
  issuing_body?: string;
  certificate_number?: string;
  status?: 'valid' | 'expired' | 'expiring_soon';
  notes?: string;
}

interface UpdateCertificationPayload {
  workerId: string;
  certId: string;
  certification_type?: string;
  custom_name?: string;
  issued_date?: string;
  expiry_date?: string | null;
  issuing_body?: string;
  certificate_number?: string;
  status?: 'valid' | 'expired' | 'expiring_soon';
  notes?: string;
}

interface ExpiringCertResult {
  worker_id: string;
  worker_name: string;
  certification: Certification;
}

interface CertificationMatrixEntry {
  worker_id: string;
  worker_name: string;
  role: string;
  [certType: string]: string;
}

export function useWorkers(params?: WorkerListParams) {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  if (params?.role) searchParams.set('role', params.role);
  if (params?.trade) searchParams.set('trade', params.trade);
  if (params?.search) searchParams.set('search', params.search);
  const queryString = searchParams.toString();
  const endpoint = queryString ? `/me/workers?${queryString}` : '/me/workers';

  return useQuery<Worker[]>({
    queryKey: ['workers', params],
    queryFn: async () => {
      const response = await api.get<{ workers: Worker[]; total: number }>(endpoint);
      return response.workers;
    },
  });
}

export function useWorker(id: string | undefined) {
  return useQuery<Worker>({
    queryKey: ['workers', id],
    queryFn: () => api.get<Worker>(`/me/workers/${id}`),
    enabled: !!id,
  });
}

export function useCreateWorker() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateWorkerPayload) =>
      api.post<Worker>('/me/workers', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workers'] });
    },
  });
}

export function useUpdateWorker() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateWorkerPayload) =>
      api.patch<Worker>(`/me/workers/${id}`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workers'] });
      queryClient.setQueryData(['workers', data.id], data);
    },
  });
}

export function useDeleteWorker() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/me/workers/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workers'] });
    },
  });
}

export function useAddCertification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workerId, ...data }: AddCertificationPayload) =>
      api.post<Certification>(`/me/workers/${workerId}/certifications`, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['workers'] });
      queryClient.invalidateQueries({ queryKey: ['workers', variables.workerId] });
      queryClient.invalidateQueries({ queryKey: ['expiring-certifications'] });
    },
  });
}

export function useUpdateCertification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workerId, certId, ...data }: UpdateCertificationPayload) =>
      api.patch<Certification>(`/me/workers/${workerId}/certifications/${certId}`, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['workers'] });
      queryClient.invalidateQueries({ queryKey: ['workers', variables.workerId] });
    },
  });
}

export function useRemoveCertification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workerId, certId }: { workerId: string; certId: string }) =>
      api.delete(`/me/workers/${workerId}/certifications/${certId}`),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['workers'] });
      queryClient.invalidateQueries({ queryKey: ['workers', variables.workerId] });
      queryClient.invalidateQueries({ queryKey: ['expiring-certifications'] });
    },
  });
}

export function useExpiringCertifications(days: number = 30) {
  return useQuery<ExpiringCertResult[]>({
    queryKey: ['expiring-certifications', days],
    queryFn: async () => {
      const response = await api.get<{ certifications: ExpiringCertResult[]; total: number }>(
        `/me/workers/expiring-certifications?days=${days}`,
      );
      return response.certifications;
    },
  });
}

export function useCertificationMatrix() {
  return useQuery<CertificationMatrixEntry[]>({
    queryKey: ['certification-matrix'],
    queryFn: async () => {
      const response = await api.get<{ matrix: CertificationMatrixEntry[]; total: number }>(
        '/me/workers/certification-matrix',
      );
      return response.matrix;
    },
  });
}
