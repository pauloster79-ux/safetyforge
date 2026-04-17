import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface EstimateWorkItem {
  id: string;
  description: string;
  state: string;
  quantity: number;
  unit: string;
  labour_cost_cents: number;
  items_cost_cents: number;
  margin_pct: number;
  sell_price_cents: number;
  is_alternate: boolean;
}

export interface EstimateSummary {
  project_id: string;
  project_name: string;
  project_state: string;
  estimate_confidence: string | null;
  target_margin_percent: number | null;
  items: EstimateWorkItem[];
  total_labour_cents: number;
  total_items_cents: number;
  grand_total_cents: number;
  item_count: number;
  currency: string;
}

/**
 * Fetches estimate summary for a project via the direct REST endpoint.
 *
 * `refetchOnMount: 'always'` guarantees fresh data whenever the component
 * remounts (e.g. switching between project tabs), and `staleTime: 0` ensures
 * invalidations from chat-driven mutations always trigger an immediate
 * network refetch rather than serving cached data.
 */
export function useEstimateSummary(projectId: string | undefined) {
  return useQuery<EstimateSummary>({
    queryKey: ['estimate-summary', projectId],
    queryFn: () =>
      api.get<EstimateSummary>(`/me/projects/${projectId}/estimate-summary`),
    enabled: !!projectId,
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: false,
  });
}
