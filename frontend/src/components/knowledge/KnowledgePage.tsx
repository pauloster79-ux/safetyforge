/**
 * KnowledgePage — Layer 4 "My Knowledge" canvas.
 *
 * Surfaces the contractor's accumulated knowledge across three tabs:
 *
 *   Insights      lessons-learned ("low ceilings add 15% to rough-in") that
 *                 Kerf will apply to future quotes via apply_insight.
 *   Rates         labour, material, and equipment rates (resource_rate nodes)
 *                 grouped by type. Edit inline, deactivate to retire.
 *   Productivity  productivity rates (e.g. "80 LF/day for EMT rough-in") with
 *                 sample size and crew composition.
 *
 * Read/write surface — Marco/Sarah/Jake are expected to curate these because
 * they directly shape future estimates. Edits route through ``useUpdate*``
 * hooks; "Off" routes through ``useDeactivate*`` because the backend keeps
 * deactivated rows so historical quotes remain explainable.
 *
 * The 💡 lightbulb is the one allowed glyph (it's a Kerf-wide symbol for
 * Insight). Everything else stays clean and typographic per the design system.
 *
 * Data shape: see ``useKnowledgeSummary`` for the full payload. The
 * granular rate/insight lists are also available via dedicated hooks
 * (``useResourceRates`` etc.) but the summary endpoint is one round-trip
 * and is what we use here.
 */

import { useMemo, useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import {
  BookOpen, Hammer, Gauge, Box,
  Loader2, AlertCircle, Pencil, PowerOff, Trash2, Check, X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useKnowledgeSummary,
  useUpdateInsight,
  useDeleteInsight,
  useUpdateResourceRate,
  useDeactivateResourceRate,
  useUpdateProductivityRate,
  useDeactivateProductivityRate,
  type Insight,
  type ResourceRate,
  type ProductivityRate,
} from '@/hooks/useKnowledge';
import { formatCents } from '@/lib/format';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Small utilities
// ---------------------------------------------------------------------------

/** Format a resource rate as ``$NN.NN/unit`` (or just ``$NN.NN`` for lump sum). */
function formatRate(rate: ResourceRate): string {
  const dollars = formatCents(rate.rate_cents);
  const unitLabel = rate.unit.replace(/^per_/, '').toLowerCase();
  if (unitLabel === 'lump_sum' || unitLabel === '') return dollars;
  return `${dollars}/${unitLabel}`;
}

/** Format a productivity rate as ``80 LF/day`` (rate + unit + time unit). */
function formatProductivity(r: ProductivityRate): string {
  const time = r.time_unit.replace(/^per_/, '');
  const rateDisplay = Number.isInteger(r.rate) ? r.rate.toString() : r.rate.toFixed(2);
  return `${rateDisplay} ${r.rate_unit}/${time}`;
}

function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

/** Robust relative-time helper. ``formatDistanceToNow`` throws on bad dates. */
function relativeTime(iso: string | null | undefined): string {
  if (!iso) return 'never';
  try {
    return formatDistanceToNow(new Date(iso), { addSuffix: true });
  } catch {
    return 'unknown';
  }
}

/**
 * Confidence visualisation as 5 dots — full circle for filled, ring for empty.
 * Spec calls for ●●●●○ style; we render with text characters for crisp pixels
 * at any zoom level (Tailwind class colors so it inherits dark mode).
 */
function ConfidenceDots({ confidence }: { confidence: number }) {
  const filled = Math.round(Math.max(0, Math.min(1, confidence)) * 5);
  return (
    <span className="inline-flex items-center gap-px font-mono text-[11px] leading-none tracking-tight">
      {Array.from({ length: 5 }).map((_, i) => (
        <span
          key={i}
          className={cn(
            i < filled ? 'text-machine-dark' : 'text-muted-foreground/40',
          )}
        >
          ●
        </span>
      ))}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Empty-state row
// ---------------------------------------------------------------------------

function EmptyRow({ children }: { children: React.ReactNode }) {
  return (
    <div className="py-6 text-center text-xs text-muted-foreground">
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Resource rate row — inline edit on description + rate, plus deactivate
// ---------------------------------------------------------------------------

function ResourceRateRow({ rate }: { rate: ResourceRate }) {
  const [editing, setEditing] = useState(false);
  const [draftDescription, setDraftDescription] = useState(rate.description);
  const [draftDollars, setDraftDollars] = useState((rate.rate_cents / 100).toFixed(2));

  const update = useUpdateResourceRate();
  const deactivate = useDeactivateResourceRate();

  const reset = () => {
    setDraftDescription(rate.description);
    setDraftDollars((rate.rate_cents / 100).toFixed(2));
    setEditing(false);
  };

  const save = () => {
    const trimmedDesc = draftDescription.trim();
    const dollars = parseFloat(draftDollars);
    if (!trimmedDesc || Number.isNaN(dollars) || dollars < 0) {
      reset();
      return;
    }
    const nextCents = Math.round(dollars * 100);
    if (trimmedDesc === rate.description && nextCents === rate.rate_cents) {
      setEditing(false);
      return;
    }
    update.mutate(
      {
        id: rate.id,
        patch: { description: trimmedDesc, rate_cents: nextCents },
      },
      { onSettled: () => setEditing(false) },
    );
  };

  const handleDeactivate = () => {
    if (
      !window.confirm(
        `Turn off "${rate.description}"? It won't be used in future quotes, ` +
        'but historical quotes will still reference it.',
      )
    ) {
      return;
    }
    deactivate.mutate(rate.id);
  };

  const unitLabel = rate.unit.replace(/^per_/, '').toLowerCase();

  if (editing) {
    return (
      <li className="flex items-center gap-2 py-2 text-sm">
        <Input
          value={draftDescription}
          onChange={(e) => setDraftDescription(e.target.value)}
          autoFocus
          className="h-7 flex-1 text-sm"
          onKeyDown={(e) => {
            if (e.key === 'Enter') save();
            if (e.key === 'Escape') reset();
          }}
        />
        <div className="flex shrink-0 items-center gap-0.5 rounded-sm border border-border px-1">
          <span className="text-xs text-muted-foreground">$</span>
          <Input
            value={draftDollars}
            onChange={(e) => setDraftDollars(e.target.value)}
            className="h-6 w-20 border-0 bg-transparent p-0 text-right font-mono text-sm focus-visible:ring-0"
            inputMode="decimal"
            onKeyDown={(e) => {
              if (e.key === 'Enter') save();
              if (e.key === 'Escape') reset();
            }}
          />
          {unitLabel && unitLabel !== 'lump_sum' && (
            <span className="text-[10px] text-muted-foreground">/{unitLabel}</span>
          )}
        </div>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={save}
          disabled={update.isPending}
          title="Save"
        >
          <Check className="h-3.5 w-3.5" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={reset}
          title="Cancel"
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      </li>
    );
  }

  return (
    <li className="flex items-center justify-between gap-2 py-2 text-sm">
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{rate.description}</div>
        <div className="mt-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
          source: {rate.source.replace(/_/g, ' ')}
          {rate.supplier_name && ` · ${rate.supplier_name}`}
          {rate.sample_size != null && rate.sample_size > 0 && ` · ${rate.sample_size} samples`}
        </div>
      </div>
      <div className="ml-3 shrink-0 font-mono text-sm">{formatRate(rate)}</div>
      <div className="flex shrink-0 items-center gap-0.5">
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={() => setEditing(true)}
          title="Edit rate"
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7 text-muted-foreground hover:text-destructive"
          onClick={handleDeactivate}
          disabled={deactivate.isPending}
          title="Turn off — Kerf will stop using this rate"
        >
          <PowerOff className="h-3.5 w-3.5" />
        </Button>
      </div>
    </li>
  );
}

// ---------------------------------------------------------------------------
// Rates tab — labour / material / equipment grouped
// ---------------------------------------------------------------------------

function RatesTabContent({ rates }: { rates: ResourceRate[] }) {
  const groups = useMemo(() => {
    const out: Record<string, ResourceRate[]> = {
      labour: [],
      material: [],
      equipment: [],
    };
    for (const r of rates) {
      (out[r.resource_type] ??= []).push(r);
    }
    return out;
  }, [rates]);

  if (rates.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <EmptyRow>
            You haven&apos;t added any rates yet. Kerf will learn your rates as you quote.
          </EmptyRow>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {(['labour', 'material', 'equipment'] as const).map((type) => {
        const list = groups[type] ?? [];
        if (list.length === 0) return null;
        const label = type === 'labour' ? 'Labour' : type === 'material' ? 'Materials' : 'Equipment';
        const Icon = type === 'labour' ? Hammer : type === 'material' ? Box : Gauge;
        return (
          <Card key={type}>
            <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-sm font-semibold">{label}</CardTitle>
                <Badge variant="secondary" className="text-[10px]">{list.length}</Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <ul className="divide-y divide-border/60">
                {list.map((r) => (
                  <ResourceRateRow key={r.id} rate={r} />
                ))}
              </ul>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Productivity rate row — inline edit on description + rate, plus deactivate
// ---------------------------------------------------------------------------

function ProductivityRow({ rate }: { rate: ProductivityRate }) {
  const [editing, setEditing] = useState(false);
  const [draftDescription, setDraftDescription] = useState(rate.description);
  const [draftRate, setDraftRate] = useState(String(rate.rate));

  const update = useUpdateProductivityRate();
  const deactivate = useDeactivateProductivityRate();

  const reset = () => {
    setDraftDescription(rate.description);
    setDraftRate(String(rate.rate));
    setEditing(false);
  };

  const save = () => {
    const trimmed = draftDescription.trim();
    const num = parseFloat(draftRate);
    if (!trimmed || Number.isNaN(num) || num < 0) {
      reset();
      return;
    }
    if (trimmed === rate.description && num === rate.rate) {
      setEditing(false);
      return;
    }
    update.mutate(
      { id: rate.id, patch: { description: trimmed, rate: num } },
      { onSettled: () => setEditing(false) },
    );
  };

  const handleDeactivate = () => {
    if (
      !window.confirm(
        `Turn off "${rate.description}"? Kerf will stop using this productivity rate, ` +
        'but historical quotes will still reference it.',
      )
    ) {
      return;
    }
    deactivate.mutate(rate.id);
  };

  const time = rate.time_unit.replace(/^per_/, '');

  if (editing) {
    return (
      <li className="flex items-center gap-2 py-2 text-sm">
        <Input
          value={draftDescription}
          onChange={(e) => setDraftDescription(e.target.value)}
          autoFocus
          className="h-7 flex-1 text-sm"
          onKeyDown={(e) => {
            if (e.key === 'Enter') save();
            if (e.key === 'Escape') reset();
          }}
        />
        <div className="flex shrink-0 items-center gap-1 rounded-sm border border-border px-1">
          <Input
            value={draftRate}
            onChange={(e) => setDraftRate(e.target.value)}
            className="h-6 w-16 border-0 bg-transparent p-0 text-right font-mono text-sm focus-visible:ring-0"
            inputMode="decimal"
            onKeyDown={(e) => {
              if (e.key === 'Enter') save();
              if (e.key === 'Escape') reset();
            }}
          />
          <span className="text-[10px] text-muted-foreground">{rate.rate_unit}/{time}</span>
        </div>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={save}
          disabled={update.isPending}
          title="Save"
        >
          <Check className="h-3.5 w-3.5" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={reset}
          title="Cancel"
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      </li>
    );
  }

  return (
    <li className="flex items-center justify-between gap-2 py-2 text-sm">
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{rate.description}</div>
        <div className="mt-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
          source: {rate.source.replace(/_/g, ' ')}
          {rate.sample_size != null && rate.sample_size > 0 && ` · ${rate.sample_size} samples`}
          {rate.crew_composition && ` · ${rate.crew_composition}`}
          {rate.last_derived_at && ` · derived ${relativeTime(rate.last_derived_at)}`}
        </div>
      </div>
      <div className="ml-3 shrink-0 font-mono text-sm">{formatProductivity(rate)}</div>
      <div className="flex shrink-0 items-center gap-0.5">
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={() => setEditing(true)}
          title="Edit productivity rate"
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7 text-muted-foreground hover:text-destructive"
          onClick={handleDeactivate}
          disabled={deactivate.isPending}
          title="Turn off — Kerf will stop using this rate"
        >
          <PowerOff className="h-3.5 w-3.5" />
        </Button>
      </div>
    </li>
  );
}

function ProductivityTabContent({ rates }: { rates: ProductivityRate[] }) {
  if (rates.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <EmptyRow>
            No productivity patterns yet. Kerf will record rates as you close out
            jobs and feed actuals back in — &ldquo;80 LF/day of EMT for residential
            rough-in&rdquo;, that kind of thing.
          </EmptyRow>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
        <div className="flex items-center gap-2">
          <Gauge className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-sm font-semibold">Productivity</CardTitle>
          <Badge variant="secondary" className="text-[10px]">{rates.length}</Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <ul className="divide-y divide-border/60">
          {rates.map((r) => (
            <ProductivityRow key={r.id} rate={r} />
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Insight row — inline edit on statement, dot confidence, applied count, etc.
// ---------------------------------------------------------------------------

function InsightRow({ insight }: { insight: Insight }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(insight.statement);
  const update = useUpdateInsight();
  const remove = useDeleteInsight();

  const save = () => {
    const trimmed = draft.trim();
    if (!trimmed || trimmed === insight.statement) {
      setEditing(false);
      setDraft(insight.statement);
      return;
    }
    update.mutate(
      { id: insight.id, patch: { statement: trimmed } },
      { onSettled: () => setEditing(false) },
    );
  };

  const cancel = () => {
    setDraft(insight.statement);
    setEditing(false);
  };

  const confirmRemove = () => {
    if (!window.confirm('Remove this insight? Kerf will stop applying it to quotes.')) {
      return;
    }
    remove.mutate(insight.id);
  };

  const adjustmentLabel = (() => {
    if (
      (insight.adjustment_type === 'productivity_multiplier'
        || insight.adjustment_type === 'rate_adjustment')
      && insight.adjustment_value != null
    ) {
      const pct = Math.round((insight.adjustment_value - 1) * 100);
      return pct > 0 ? `+${pct}%` : `${pct}%`;
    }
    if (insight.adjustment_type === 'qualitative') return 'qualitative';
    return insight.adjustment_type.replace(/_/g, ' ');
  })();

  return (
    <li className="flex items-start gap-2 py-3">
      <span className="shrink-0 text-base leading-none" aria-hidden>💡</span>
      <div className="min-w-0 flex-1">
        {editing ? (
          <div className="flex items-center gap-1">
            <Input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              autoFocus
              className="h-7 text-sm"
              onKeyDown={(e) => {
                if (e.key === 'Enter') save();
                if (e.key === 'Escape') cancel();
              }}
            />
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7"
              onClick={save}
              disabled={update.isPending}
              title="Save"
            >
              <Check className="h-3.5 w-3.5" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7"
              onClick={cancel}
              title="Cancel"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm font-medium">
            <span className="min-w-0 flex-1 truncate">{insight.statement}</span>
            {insight.adjustment_value != null || insight.adjustment_type === 'qualitative' ? (
              <Badge variant="outline" className="shrink-0 font-mono text-[10px]">
                {adjustmentLabel}
              </Badge>
            ) : null}
          </div>
        )}
        <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground">
          <span className="uppercase tracking-wider">scope:</span>
          <span>{insight.scope.replace(/_/g, ' ')}</span>
          <span>/</span>
          <span className="font-mono">{insight.scope_value}</span>
          <span>·</span>
          <span className="flex items-center gap-1">
            <ConfidenceDots confidence={insight.confidence} />
            <span>{formatConfidence(insight.confidence)}</span>
          </span>
          <span>·</span>
          <span>
            applied {insight.validation_count}
            {insight.validation_count === 1 ? ' time' : ' times'}
          </span>
          {insight.last_applied_at && (
            <>
              <span>·</span>
              <span>last {relativeTime(insight.last_applied_at)}</span>
            </>
          )}
        </div>
      </div>
      {!editing && (
        <div className="flex shrink-0 items-center gap-0.5">
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={() => setEditing(true)}
            title="Edit statement"
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7 text-muted-foreground hover:text-destructive"
            onClick={confirmRemove}
            disabled={remove.isPending}
            title="Delete insight"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </li>
  );
}

function InsightsTabContent({ insights }: { insights: Insight[] }) {
  if (insights.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <EmptyRow>
            No lessons captured yet. Kerf will record patterns you mention as you
            quote — &ldquo;low-ceiling renos always add 15%&rdquo; or &ldquo;medical
            offices need shielded cable.&rdquo;
          </EmptyRow>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-sm font-semibold">Lessons Learned</CardTitle>
          <Badge variant="secondary" className="text-[10px]">{insights.length}</Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <ul className="divide-y divide-border/60">
          {insights.map((i) => (
            <InsightRow key={i.id} insight={i} />
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Top-level page
// ---------------------------------------------------------------------------

export function KnowledgePage() {
  const { data, isLoading, error } = useKnowledgeSummary();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center py-12 text-center text-muted-foreground">
        <AlertCircle className="mb-2 h-6 w-6" />
        <p className="text-sm">Failed to load your knowledge.</p>
        <p className="text-xs">{error?.message ?? 'Unknown error'}</p>
      </div>
    );
  }

  const completedProjects = data.completed_projects.total;
  const insightCount = data.insights.total;
  const ratesCount = data.resource_rates.total;
  const productivityCount = data.productivity_rates.total;
  const materialCatalogCount = data.material_catalog.total;

  return (
    <div className="mx-auto max-w-4xl space-y-4 pb-8">
      <div>
        <h1 className="text-xl font-bold text-foreground">My Knowledge</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your patterns, rates, and productivity — what Kerf learns from your jobs and
          applies to future quotes.
          {completedProjects > 0 && (
            <>
              {' '}Derived from{' '}
              <span className="font-semibold text-foreground">{completedProjects}</span>{' '}
              completed {completedProjects === 1 ? 'project' : 'projects'}.
            </>
          )}
        </p>
      </div>

      <Tabs defaultValue="insights" className="space-y-4">
        <TabsList>
          <TabsTrigger value="insights">
            Insights
            <Badge variant="secondary" className="ml-1 text-[10px]">{insightCount}</Badge>
          </TabsTrigger>
          <TabsTrigger value="rates">
            Rates
            <Badge variant="secondary" className="ml-1 text-[10px]">{ratesCount}</Badge>
          </TabsTrigger>
          <TabsTrigger value="productivity">
            Productivity
            <Badge variant="secondary" className="ml-1 text-[10px]">{productivityCount}</Badge>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="insights" className="space-y-4">
          <InsightsTabContent insights={data.insights.items} />
        </TabsContent>

        <TabsContent value="rates" className="space-y-4">
          <RatesTabContent rates={data.resource_rates.items} />
          {/* Material catalog summary lives under the Rates tab — it's
              priceable data and conceptually overlaps with the Materials
              section. We only expose the count for now; a dedicated catalog
              browser can land later. */}
          {materialCatalogCount > 0 && (
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
                <div className="flex items-center gap-2">
                  <Box className="h-4 w-4 text-muted-foreground" />
                  <CardTitle className="text-sm font-semibold">Material Catalog</CardTitle>
                  <Badge variant="secondary" className="text-[10px]">{materialCatalogCount}</Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-xs text-muted-foreground">
                  {materialCatalogCount} material{' '}
                  {materialCatalogCount === 1 ? 'entry' : 'entries'} stored from supplier
                  quotes and historical jobs. Kerf surfaces these first during price
                  lookups.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="productivity" className="space-y-4">
          <ProductivityTabContent rates={data.productivity_rates.items} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
