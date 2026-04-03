import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { OshaLogEntry, Osha300Summary } from '@/lib/constants';

interface CreateOshaEntryPayload {
  employee_name: string;
  job_title: string;
  date_of_injury: string;
  where_event_occurred: string;
  description: string;
  classification: OshaLogEntry['classification'];
  injury_type: OshaLogEntry['injury_type'];
  days_away_from_work: number;
  days_of_restricted_work: number;
  died: boolean;
  privacy_case: boolean;
}

interface UpdateOshaEntryPayload extends Partial<CreateOshaEntryPayload> {
  id: string;
}

export function useOshaLogEntries(year?: number) {
  const endpoint = year ? `/me/osha-log/entries?year=${year}` : '/me/osha-log/entries';

  return useQuery<OshaLogEntry[]>({
    queryKey: ['osha-log-entries', year],
    queryFn: async () => {
      const response = await api.get<{ entries: OshaLogEntry[]; total: number }>(endpoint);
      return response.entries;
    },
  });
}

export function useOshaLogEntry(id: string | undefined) {
  return useQuery<OshaLogEntry>({
    queryKey: ['osha-log-entries', id],
    queryFn: () => api.get<OshaLogEntry>(`/me/osha-log/entries/${id}`),
    enabled: !!id,
  });
}

export function useCreateOshaLogEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateOshaEntryPayload) =>
      api.post<OshaLogEntry>('/me/osha-log/entries', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['osha-log-entries'] });
      queryClient.invalidateQueries({ queryKey: ['osha-summary'] });
    },
  });
}

export function useUpdateOshaLogEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateOshaEntryPayload) =>
      api.patch<OshaLogEntry>(`/me/osha-log/entries/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['osha-log-entries'] });
      queryClient.invalidateQueries({ queryKey: ['osha-summary'] });
    },
  });
}

export function useDeleteOshaLogEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/me/osha-log/entries/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['osha-log-entries'] });
      queryClient.invalidateQueries({ queryKey: ['osha-summary'] });
    },
  });
}

export function useOsha300Summary(year?: number) {
  const endpoint = year ? `/me/osha-log/summary?year=${year}` : '/me/osha-log/summary';

  return useQuery<Osha300Summary>({
    queryKey: ['osha-summary', year],
    queryFn: () => api.get<Osha300Summary>(endpoint),
  });
}

export function useCertifySummary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { certified_by: string; year?: number }) =>
      api.post<Osha300Summary>('/me/osha-log/summary/certify', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['osha-summary'] });
    },
  });
}
