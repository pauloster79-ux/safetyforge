import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Equipment, EquipmentInspectionLog } from '@/lib/constants';

interface EquipmentSummary {
  total_equipment: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  overdue_inspections: number;
  overdue_maintenance: number;
}

interface DotComplianceEntry {
  equipment_id: string;
  name: string;
  dot_number: string;
  last_inspection_date: string | null;
  next_inspection_due: string | null;
  status: string;
}

interface DotComplianceResponse {
  vehicles: DotComplianceEntry[];
  total: number;
  compliant: number;
  overdue: number;
  missing: number;
}

interface OverdueEquipment {
  equipment_id: string;
  name: string;
  equipment_type: string;
  last_inspection_date: string | null;
  next_inspection_due: string;
  days_overdue: number;
}

export function useEquipment(params?: { status?: string; type?: string; project_id?: string }) {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  if (params?.type) searchParams.set('type', params.type);
  if (params?.project_id) searchParams.set('project_id', params.project_id);
  const queryString = searchParams.toString();
  const endpoint = queryString ? `/me/equipment?${queryString}` : '/me/equipment';

  return useQuery<Equipment[]>({
    queryKey: ['equipment', params],
    queryFn: async () => {
      const response = await api.get<{ equipment: Equipment[]; total: number }>(endpoint);
      return response.equipment;
    },
  });
}

export function useEquipmentItem(id: string | undefined) {
  return useQuery<Equipment>({
    queryKey: ['equipment', id],
    queryFn: () => api.get<Equipment>(`/me/equipment/${id}`),
    enabled: !!id,
  });
}

export function useCreateEquipment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Equipment>) =>
      api.post<Equipment>('/me/equipment', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] });
    },
  });
}

export function useUpdateEquipment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: Partial<Equipment> & { id: string }) =>
      api.patch<Equipment>(`/me/equipment/${id}`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] });
      queryClient.setQueryData(['equipment', data.id], data);
    },
  });
}

export function useDeleteEquipment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/me/equipment/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] });
    },
  });
}

export function useEquipmentInspections(equipmentId: string | undefined) {
  return useQuery<EquipmentInspectionLog[]>({
    queryKey: ['equipment-inspections', equipmentId],
    queryFn: async () => {
      const response = await api.get<{ logs: EquipmentInspectionLog[]; total: number }>(
        `/me/equipment/${equipmentId}/inspections`,
      );
      return response.logs;
    },
    enabled: !!equipmentId,
  });
}

export function useCreateEquipmentInspection(equipmentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<EquipmentInspectionLog>) =>
      api.post<EquipmentInspectionLog>(`/me/equipment/${equipmentId}/inspections`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment-inspections', equipmentId] });
      queryClient.invalidateQueries({ queryKey: ['equipment'] });
    },
  });
}

export function useOverdueInspections() {
  return useQuery<OverdueEquipment[]>({
    queryKey: ['equipment-overdue-inspections'],
    queryFn: async () => {
      const response = await api.get<{ equipment: OverdueEquipment[]; total: number }>(
        '/me/equipment/overdue-inspections',
      );
      return response.equipment;
    },
  });
}

export function useEquipmentSummary() {
  return useQuery<EquipmentSummary>({
    queryKey: ['equipment-summary'],
    queryFn: () => api.get<EquipmentSummary>('/me/equipment/summary'),
  });
}

export function useDotCompliance() {
  return useQuery<DotComplianceResponse>({
    queryKey: ['dot-compliance'],
    queryFn: () => api.get<DotComplianceResponse>('/me/equipment/dot-compliance'),
  });
}
