import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// ---------------------------------------------------------------------------
// Work Items
// ---------------------------------------------------------------------------

interface UpdateWorkItemPayload {
  id: string;
  description?: string;
  quantity?: number;
  unit?: string;
  margin_pct?: number;
  state?: string;
}

export function useUpdateWorkItem(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateWorkItemPayload) =>
      api.patch(`/me/projects/${projectId}/work-items/${id}`, data),
    onSuccess: (_res, variables) => {
      queryClient.invalidateQueries({ queryKey: ['estimate-summary', projectId] });
      queryClient.invalidateQueries({ queryKey: ['work-items', projectId] });
      // A quantity change rescales the child labour/items on the server —
      // invalidate them so expanded rows show the new values.
      if (variables.quantity !== undefined) {
        queryClient.invalidateQueries({ queryKey: ['labour', projectId, variables.id] });
        queryClient.invalidateQueries({ queryKey: ['items', projectId, variables.id] });
      }
    },
  });
}

export function useDeleteWorkItem(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/me/projects/${projectId}/work-items/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['estimate-summary', projectId] });
      queryClient.invalidateQueries({ queryKey: ['work-items', projectId] });
    },
  });
}

export function useRestoreWorkItem(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/me/projects/${projectId}/work-items/${id}/restore`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['estimate-summary', projectId] });
      queryClient.invalidateQueries({ queryKey: ['work-items', projectId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Labour
// ---------------------------------------------------------------------------

interface UpdateLabourPayload {
  id: string;
  task?: string;
  rate_cents?: number;
  hours?: number;
}

export function useUpdateLabour(projectId: string, workItemId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateLabourPayload) =>
      api.patch(
        `/me/projects/${projectId}/work-items/${workItemId}/labour/${id}`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['labour', projectId, workItemId] });
      queryClient.invalidateQueries({ queryKey: ['estimate-summary', projectId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Items
// ---------------------------------------------------------------------------

interface UpdateItemPayload {
  id: string;
  description?: string;
  quantity?: number;
  unit?: string;
  unit_cost_cents?: number;
}

export function useUpdateItem(projectId: string, workItemId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateItemPayload) =>
      api.patch(
        `/me/projects/${projectId}/work-items/${workItemId}/items/${id}`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items', projectId, workItemId] });
      queryClient.invalidateQueries({ queryKey: ['estimate-summary', projectId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Assumptions
// ---------------------------------------------------------------------------

interface UpdateAssumptionPayload {
  id: string;
  statement?: string;
  category?: string;
  variation_trigger?: boolean;
  trigger_description?: string;
}

export function useUpdateAssumption(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateAssumptionPayload) =>
      api.patch(`/me/projects/${projectId}/assumptions/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assumptions', projectId] });
    },
  });
}

export function useDeleteAssumption(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/me/projects/${projectId}/assumptions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assumptions', projectId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Exclusions
// ---------------------------------------------------------------------------

interface UpdateExclusionPayload {
  id: string;
  statement?: string;
  category?: string;
  partial_inclusion?: string;
}

export function useUpdateExclusion(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateExclusionPayload) =>
      api.patch(`/me/projects/${projectId}/exclusions/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exclusions', projectId] });
    },
  });
}

export function useDeleteExclusion(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/me/projects/${projectId}/exclusions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exclusions', projectId] });
    },
  });
}
