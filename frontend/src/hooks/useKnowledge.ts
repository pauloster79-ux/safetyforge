/**
 * useKnowledge — React Query hooks for Layer 4 "My Knowledge" data.
 *
 * Endpoints:
 *   GET    /me/knowledge/summary                     aggregated rates / productivity / insights / counts
 *   GET    /me/insights                              full insight list (with optional filters)
 *   POST   /me/insights                              create insight
 *   PATCH  /me/insights/{id}                         edit an insight (statement, adjustment, etc.)
 *   DELETE /me/insights/{id}                         remove an insight
 *   POST   /me/insights/{id}/validate                mark as applied
 *   GET    /me/rates                                 list resource rates
 *   PATCH  /me/rates/{rate_id}                       update resource rate
 *   POST   /me/rates/{rate_id}/deactivate            deactivate resource rate
 *   GET    /me/productivity-rates                    list productivity rates
 *   PATCH  /me/productivity-rates/{rate_id}          update productivity rate
 *   POST   /me/productivity-rates/{rate_id}/deactivate  deactivate productivity rate
 *
 * All responses come back verbatim from the backend; frontend components
 * that care about individual fields should define their own local narrow
 * interfaces rather than widening these.
 *
 * Note: the backend doesn't have a hard "delete" for rates — once you've used
 * one in a quote you don't want to lose its provenance. ``deactivate`` flips
 * ``active=false`` so it stops appearing in the source cascade but the row is
 * still queryable. The page surfaces this as "Off".
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// ---------------------------------------------------------------------------
// Shared types — mirror backend/app/models/insight.py etc.
// ---------------------------------------------------------------------------

export type InsightScope =
  | 'work_type'
  | 'trade'
  | 'jurisdiction'
  | 'client_type'
  | 'project_size'
  | 'other';

export interface Insight {
  id: string;
  company_id: string;
  scope: InsightScope;
  scope_value: string;
  statement: string;
  adjustment_type: string;
  adjustment_value: number | null;
  confidence: number;
  source_context: string | null;
  validation_count: number;
  last_applied_at: string | null;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

export interface ResourceRate {
  id: string;
  company_id: string;
  resource_type: 'labour' | 'material' | 'equipment';
  description: string;
  rate_cents: number;
  unit: string;
  source: string;
  base_rate_cents: number | null;
  burden_percent: number | null;
  non_productive_percent: number | null;
  supplier_name: string;
  quote_valid_until: string | null;
  sample_size: number | null;
  std_deviation_cents: number | null;
  last_derived_at: string | null;
  active: boolean;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

export interface ProductivityRate {
  id: string;
  company_id: string;
  description: string;
  rate: number;
  rate_unit: string;
  time_unit: 'per_hour' | 'per_day' | 'per_week';
  crew_composition: string;
  conditions: string;
  source: 'manual_entry' | 'derived_from_actuals';
  sample_size: number | null;
  std_deviation: number | null;
  includes_non_productive: boolean;
  last_derived_at: string | null;
  active: boolean;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

export interface KnowledgeSummary {
  company_id: string;
  resource_rates: { items: ResourceRate[]; total: number };
  productivity_rates: { items: ProductivityRate[]; total: number };
  insights: { items: Insight[]; total: number };
  material_catalog: { total: number };
  completed_projects: { total: number };
}

export interface InsightCreatePayload {
  scope: InsightScope;
  scope_value: string;
  statement: string;
  adjustment_type: string;
  adjustment_value?: number | null;
  confidence?: number;
  source_context?: string;
}

export interface InsightUpdatePayload {
  scope?: InsightScope;
  scope_value?: string;
  statement?: string;
  adjustment_type?: string;
  adjustment_value?: number | null;
  confidence?: number;
  source_context?: string;
}

export interface ResourceRateUpdatePayload {
  description?: string;
  rate_cents?: number;
  unit?: string;
  source?: string;
  base_rate_cents?: number | null;
  burden_percent?: number | null;
  non_productive_percent?: number | null;
  supplier_name?: string;
  quote_valid_until?: string | null;
}

export interface ProductivityRateUpdatePayload {
  description?: string;
  rate?: number;
  rate_unit?: string;
  time_unit?: 'per_hour' | 'per_day' | 'per_week';
  crew_composition?: string;
  conditions?: string;
  includes_non_productive?: boolean;
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

/** Aggregated Layer 4 knowledge for the current company. */
export function useKnowledgeSummary() {
  return useQuery<KnowledgeSummary>({
    queryKey: ['knowledge-summary'],
    queryFn: () => api.get<KnowledgeSummary>('/me/knowledge/summary'),
    staleTime: 60_000,
  });
}

/** Full list of contractor insights (not chat-extracted insights). */
export function useInsights(params?: { scope?: string; scope_value?: string }) {
  const qs = new URLSearchParams();
  if (params?.scope) qs.set('scope', params.scope);
  if (params?.scope_value) qs.set('scope_value', params.scope_value);
  const queryString = qs.toString();
  const endpoint = `/me/insights${queryString ? `?${queryString}` : ''}`;

  return useQuery<{ insights: Insight[]; total: number }>({
    queryKey: ['insights', params ?? {}],
    queryFn: () => api.get<{ insights: Insight[]; total: number }>(endpoint),
    staleTime: 60_000,
  });
}

/** Create a contractor insight. */
export function useCreateInsight() {
  const queryClient = useQueryClient();
  return useMutation<Insight, Error, InsightCreatePayload>({
    mutationFn: (payload: InsightCreatePayload) =>
      api.post<Insight>('/me/insights', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insights'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-summary'] });
    },
  });
}

/** Edit an insight (statement / adjustment / confidence / etc.). */
export function useUpdateInsight() {
  const queryClient = useQueryClient();
  return useMutation<Insight, Error, { id: string; patch: InsightUpdatePayload }>({
    mutationFn: ({ id, patch }) =>
      api.patch<Insight>(`/me/insights/${encodeURIComponent(id)}`, patch),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insights'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-summary'] });
    },
  });
}

/** Remove an insight. */
export function useDeleteInsight() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (id: string) =>
      api.delete<void>(`/me/insights/${encodeURIComponent(id)}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insights'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-summary'] });
    },
  });
}

/** Record a successful application; bumps confidence + validation_count. */
export function useValidateInsight() {
  const queryClient = useQueryClient();
  return useMutation<Insight, Error, string>({
    mutationFn: (id: string) =>
      api.post<Insight>(`/me/insights/${encodeURIComponent(id)}/validate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insights'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-summary'] });
    },
  });
}

/**
 * Correct an insight that Kerf misapplied. Uses the same update endpoint to
 * lower confidence and add a correction note; the server-side mcp_tools
 * ``correct_insight`` does more (deprecation at <0.3, source_context
 * appending) but we don't have an HTTP equivalent yet. This is a good-enough
 * frontend-triggered correction path for Layer 4 today. When a dedicated
 * ``POST /me/insights/{id}/correct`` lands, swap the call in here only.
 */
export function useCorrectInsight() {
  const queryClient = useQueryClient();
  return useMutation<Insight, Error, { id: string; note: string; currentConfidence: number }>({
    mutationFn: ({ id, note, currentConfidence }) => {
      const nextConfidence = Math.max(0.1, currentConfidence - 0.1);
      return api.patch<Insight>(`/me/insights/${encodeURIComponent(id)}`, {
        confidence: nextConfidence,
        source_context: `correction: ${note}`,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insights'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-summary'] });
    },
  });
}

// ---------------------------------------------------------------------------
// Resource rates (labour / material / equipment)
// ---------------------------------------------------------------------------

/**
 * List resource rates. Defaults to active-only because the My Knowledge page
 * only shows live rates; pass ``activeOnly: false`` to include deactivated
 * rows for archive views.
 */
export function useResourceRates(params?: {
  resourceType?: 'labour' | 'material' | 'equipment';
  activeOnly?: boolean;
}) {
  const qs = new URLSearchParams();
  if (params?.resourceType) qs.set('resource_type', params.resourceType);
  if (params?.activeOnly === false) qs.set('active_only', 'false');
  const queryString = qs.toString();
  const endpoint = `/me/rates${queryString ? `?${queryString}` : ''}`;

  return useQuery<{ rates: ResourceRate[]; total: number }>({
    queryKey: ['resource-rates', params ?? {}],
    queryFn: () => api.get<{ rates: ResourceRate[]; total: number }>(endpoint),
    staleTime: 60_000,
  });
}

/** Edit a resource rate (description / rate / supplier / etc.). */
export function useUpdateResourceRate() {
  const queryClient = useQueryClient();
  return useMutation<ResourceRate, Error, { id: string; patch: ResourceRateUpdatePayload }>({
    mutationFn: ({ id, patch }) =>
      api.patch<ResourceRate>(`/me/rates/${encodeURIComponent(id)}`, patch),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resource-rates'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-summary'] });
    },
  });
}

/**
 * Deactivate a resource rate. The backend keeps the row (so historical quotes
 * still resolve) but flips ``active=false`` so it won't be surfaced in source
 * cascades. This is the closest thing to a delete for rates.
 */
export function useDeactivateResourceRate() {
  const queryClient = useQueryClient();
  return useMutation<ResourceRate, Error, string>({
    mutationFn: (id: string) =>
      api.post<ResourceRate>(`/me/rates/${encodeURIComponent(id)}/deactivate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resource-rates'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-summary'] });
    },
  });
}

// ---------------------------------------------------------------------------
// Productivity rates
// ---------------------------------------------------------------------------

/** List productivity rates (active by default). */
export function useProductivityRates(params?: { activeOnly?: boolean }) {
  const qs = new URLSearchParams();
  if (params?.activeOnly === false) qs.set('active_only', 'false');
  const queryString = qs.toString();
  const endpoint = `/me/productivity-rates${queryString ? `?${queryString}` : ''}`;

  return useQuery<{ rates: ProductivityRate[]; total: number }>({
    queryKey: ['productivity-rates', params ?? {}],
    queryFn: () => api.get<{ rates: ProductivityRate[]; total: number }>(endpoint),
    staleTime: 60_000,
  });
}

/** Edit a productivity rate (description / rate / crew / etc.). */
export function useUpdateProductivityRate() {
  const queryClient = useQueryClient();
  return useMutation<ProductivityRate, Error, { id: string; patch: ProductivityRateUpdatePayload }>({
    mutationFn: ({ id, patch }) =>
      api.patch<ProductivityRate>(
        `/me/productivity-rates/${encodeURIComponent(id)}`,
        patch,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productivity-rates'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-summary'] });
    },
  });
}

/** Deactivate a productivity rate (keeps history, hides from cascades). */
export function useDeactivateProductivityRate() {
  const queryClient = useQueryClient();
  return useMutation<ProductivityRate, Error, string>({
    mutationFn: (id: string) =>
      api.post<ProductivityRate>(
        `/me/productivity-rates/${encodeURIComponent(id)}/deactivate`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productivity-rates'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-summary'] });
    },
  });
}
