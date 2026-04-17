import { useMemo, useState } from 'react';
import { useQueries } from '@tanstack/react-query';
import { AlertTriangle, ChevronDown, ChevronUp, Database } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { formatCents } from '@/lib/format';
import type { EstimateSummary } from '@/hooks/useWorkItems';

// ---------------------------------------------------------------------------
// Types for the labour + item children we fetch per work item
// ---------------------------------------------------------------------------

interface LabourChild {
  id: string;
  task: string;
  rate_cents: number;
  hours: number;
  cost_cents: number;
  rate_source_type?: string | null;
  rate_source_id?: string | null;
  productivity_source_type?: string | null;
  productivity_source_id?: string | null;
  source_reasoning?: string | null;
}

interface ItemChild {
  id: string;
  description: string;
  quantity: number;
  unit_cost_cents: number;
  total_cents: number;
  price_source_type?: string | null;
  price_source_id?: string | null;
  source_reasoning?: string | null;
  source_url?: string | null;
  price_fetched_at?: string | null;
}

interface LabourResponse {
  labour: LabourChild[];
  total: number;
}

interface ItemsResponse {
  items: ItemChild[];
  total: number;
}

// ---------------------------------------------------------------------------
// Source aggregation
// ---------------------------------------------------------------------------

interface LabourRateSourceEntry {
  key: string;
  task: string;
  rate_cents: number;
  source_type: string | null | undefined;
  source_reasoning: string | null | undefined;
}

interface ProductivitySourceEntry {
  key: string;
  task: string;
  source_type: string | null | undefined;
  source_reasoning: string | null | undefined;
}

interface MaterialPriceSourceEntry {
  key: string;
  description: string;
  unit_cost_cents: number;
  source_type: string | null | undefined;
  source_reasoning: string | null | undefined;
  source_url: string | null | undefined;
  price_fetched_at: string | null | undefined;
}

interface AggregatedSources {
  labourRates: LabourRateSourceEntry[];
  productivity: ProductivitySourceEntry[];
  materialPrices: MaterialPriceSourceEntry[];
  industryBaselineCount: number;
  contractorStatedUnconfirmedCount: number;
}

function sourceLabel(sourceType: string | null | undefined): string {
  switch (sourceType) {
    case 'resource_rate':
      return 'your rate library';
    case 'productivity_rate':
      return 'your productivity library';
    case 'insight':
      return 'past project insight';
    case 'industry_baseline':
      return 'industry baseline';
    case 'contractor_stated':
      return 'stated by you';
    case 'contractor_estimate':
      return 'your estimate';
    case 'inherited_from_similar_project':
      return 'inherited from a similar project';
    case 'material_catalog':
      return 'material catalog';
    case 'purchase_history':
      return 'purchase history';
    case 'estimate':
      return 'estimate';
    default:
      return 'unknown source';
  }
}

function describeLabourRate(entry: LabourRateSourceEntry): string {
  return entry.source_reasoning || sourceLabel(entry.source_type);
}

function describeProductivity(entry: ProductivitySourceEntry): string {
  return entry.source_reasoning || sourceLabel(entry.source_type);
}

function describeMaterialPrice(entry: MaterialPriceSourceEntry): string {
  return entry.source_reasoning || sourceLabel(entry.source_type);
}

function aggregate(
  labour: LabourChild[],
  items: ItemChild[],
): AggregatedSources {
  const labourRatesMap = new Map<string, LabourRateSourceEntry>();
  const productivityMap = new Map<string, ProductivitySourceEntry>();
  const materialPricesMap = new Map<string, MaterialPriceSourceEntry>();

  let industryBaselineCount = 0;
  let contractorStatedUnconfirmedCount = 0;

  for (const l of labour) {
    // Labour rate source
    const rateKey = l.rate_source_id
      ? `id:${l.rate_source_id}`
      : `task:${l.task}|rate:${l.rate_cents}|type:${l.rate_source_type ?? 'none'}`;
    if (!labourRatesMap.has(rateKey)) {
      labourRatesMap.set(rateKey, {
        key: rateKey,
        task: l.task,
        rate_cents: l.rate_cents,
        source_type: l.rate_source_type,
        source_reasoning: l.source_reasoning,
      });
    }
    if (l.rate_source_type === 'contractor_stated' && !l.source_reasoning) {
      contractorStatedUnconfirmedCount += 1;
    }

    // Productivity source (may be absent for some entries)
    if (l.productivity_source_type || l.productivity_source_id) {
      const prodKey = l.productivity_source_id
        ? `id:${l.productivity_source_id}`
        : `task:${l.task}|type:${l.productivity_source_type ?? 'none'}`;
      if (!productivityMap.has(prodKey)) {
        productivityMap.set(prodKey, {
          key: prodKey,
          task: l.task,
          source_type: l.productivity_source_type,
          source_reasoning: l.source_reasoning,
        });
      }
      if (l.productivity_source_type === 'industry_baseline') {
        industryBaselineCount += 1;
      }
    }
  }

  for (const i of items) {
    const priceKey = i.price_source_id
      ? `id:${i.price_source_id}`
      : `desc:${i.description}|cost:${i.unit_cost_cents}|type:${i.price_source_type ?? 'none'}`;
    if (!materialPricesMap.has(priceKey)) {
      materialPricesMap.set(priceKey, {
        key: priceKey,
        description: i.description,
        unit_cost_cents: i.unit_cost_cents,
        source_type: i.price_source_type,
        source_reasoning: i.source_reasoning,
        source_url: i.source_url,
        price_fetched_at: i.price_fetched_at,
      });
    }
    if (i.price_source_type === 'contractor_stated' && !i.source_reasoning) {
      contractorStatedUnconfirmedCount += 1;
    }
  }

  return {
    labourRates: Array.from(labourRatesMap.values()),
    productivity: Array.from(productivityMap.values()),
    materialPrices: Array.from(materialPricesMap.values()),
    industryBaselineCount,
    contractorStatedUnconfirmedCount,
  };
}

// ---------------------------------------------------------------------------
// SourcesPanel
// ---------------------------------------------------------------------------

export function SourcesPanel({
  projectId,
  summary,
}: {
  projectId: string;
  summary: EstimateSummary;
}) {
  const [expanded, setExpanded] = useState(false);

  const workItemIds = useMemo(
    () => (summary.items ?? []).filter(Boolean).map((w) => w.id),
    [summary.items],
  );

  const labourQueries = useQueries({
    queries: workItemIds.map((wid) => ({
      queryKey: ['labour', projectId, wid],
      queryFn: async () => {
        const res = await api.get<LabourResponse>(
          `/me/projects/${projectId}/work-items/${wid}/labour`,
        );
        return res.labour;
      },
      enabled: expanded,
      staleTime: 30_000,
    })),
  });

  const itemsQueries = useQueries({
    queries: workItemIds.map((wid) => ({
      queryKey: ['items', projectId, wid],
      queryFn: async () => {
        const res = await api.get<ItemsResponse>(
          `/me/projects/${projectId}/work-items/${wid}/items`,
        );
        return res.items;
      },
      enabled: expanded,
      staleTime: 30_000,
    })),
  });

  const isLoading =
    expanded &&
    (labourQueries.some((q) => q.isLoading) ||
      itemsQueries.some((q) => q.isLoading));

  const aggregated: AggregatedSources | null = useMemo(() => {
    if (!expanded) {
      return null;
    }
    if (isLoading) {
      return null;
    }
    const allLabour = labourQueries.flatMap((q) => q.data ?? []);
    const allItems = itemsQueries.flatMap((q) => q.data ?? []);
    return aggregate(allLabour, allItems);
  }, [expanded, isLoading, labourQueries, itemsQueries]);

  const totalSourceCount =
    (aggregated?.labourRates.length ?? 0) +
    (aggregated?.productivity.length ?? 0) +
    (aggregated?.materialPrices.length ?? 0);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          <Database className="h-4 w-4 text-muted-foreground" />
          Sources
          {aggregated && totalSourceCount > 0 && (
            <Badge variant="secondary" className="ml-1">
              {totalSourceCount}
            </Badge>
          )}
        </CardTitle>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
        >
          {expanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>
      </CardHeader>
      {expanded && (
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading sources...</p>
          ) : !aggregated || totalSourceCount === 0 ? (
            <p className="text-sm text-muted-foreground">
              No source information yet. Sources will appear as work items are priced.
            </p>
          ) : (
            <div className="space-y-5 text-sm">
              {/* Labour Rates */}
              {aggregated.labourRates.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Labour rates ({aggregated.labourRates.length})
                  </p>
                  <ul className="space-y-1.5">
                    {aggregated.labourRates.map((r) => (
                      <li key={r.key} className="flex items-baseline gap-2">
                        <span className="text-muted-foreground">&bull;</span>
                        <span className="flex-1">
                          <span className="text-foreground">{r.task}</span>
                          <span className="text-muted-foreground">
                            {' '}
                            ({formatCents(r.rate_cents)}/hr)
                          </span>
                          <span className="text-muted-foreground">
                            {' '}— {describeLabourRate(r)}
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Productivity */}
              {aggregated.productivity.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Productivity ({aggregated.productivity.length})
                  </p>
                  <ul className="space-y-1.5">
                    {aggregated.productivity.map((p) => (
                      <li key={p.key} className="flex items-baseline gap-2">
                        <span className="text-muted-foreground">&bull;</span>
                        <span className="flex-1">
                          <span className="text-foreground">{p.task}</span>
                          <span className="text-muted-foreground">
                            {' '}— {describeProductivity(p)}
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Material Prices */}
              {aggregated.materialPrices.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Material prices ({aggregated.materialPrices.length})
                  </p>
                  <ul className="space-y-1.5">
                    {aggregated.materialPrices.map((m) => (
                      <li key={m.key} className="flex items-baseline gap-2">
                        <span className="text-muted-foreground">&bull;</span>
                        <span className="flex-1">
                          <span className="text-foreground">{m.description}</span>
                          <span className="text-muted-foreground">
                            {' '}— {m.source_url ? (
                              <a
                                href={m.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                title={m.source_url}
                                className="underline decoration-dotted underline-offset-2 hover:text-foreground"
                              >
                                {describeMaterialPrice(m)}
                              </a>
                            ) : (
                              describeMaterialPrice(m)
                            )}
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Warnings */}
              {(aggregated.industryBaselineCount > 0 ||
                aggregated.contractorStatedUnconfirmedCount > 0) && (
                <div className="mt-4 space-y-1.5 border-t border-muted pt-3">
                  {aggregated.industryBaselineCount > 0 && (
                    <div className="flex items-start gap-2 text-xs text-[var(--warn)]">
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                      <span>
                        {aggregated.industryBaselineCount}{' '}
                        {aggregated.industryBaselineCount === 1 ? 'item uses' : 'items use'}{' '}
                        industry baselines (low confidence)
                      </span>
                    </div>
                  )}
                  {aggregated.contractorStatedUnconfirmedCount > 0 && (
                    <div className="flex items-start gap-2 text-xs text-[var(--warn)]">
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                      <span>
                        {aggregated.contractorStatedUnconfirmedCount}{' '}
                        {aggregated.contractorStatedUnconfirmedCount === 1
                          ? 'item is'
                          : 'items are'}{' '}
                        contractor-stated but not captured yet
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
