import React, { useState } from 'react';
import { toast } from 'sonner';
import {
  ChevronRight,
  ChevronDown,
  Loader2,
  FileText,
  DollarSign,
  AlertTriangle,
  Ban,
  RefreshCw,
  Trash2,
  X,
} from 'lucide-react';
import { PaymentMilestonesSection } from '@/components/projects/contract/PaymentMilestonesSection';
import { ConditionsSection } from '@/components/projects/contract/ConditionsSection';
import { WarrantySection } from '@/components/projects/contract/WarrantySection';
import { RetentionSection } from '@/components/projects/contract/RetentionSection';
import { SourcesPanel } from '@/components/projects/contract/SourcesPanel';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EditableCell } from '@/components/ui/editable-cell';
import { useEstimateSummary } from '@/hooks/useWorkItems';
import { useAssumptions } from '@/hooks/useAssumptions';
import { useExclusions } from '@/hooks/useExclusions';
import {
  useUpdateWorkItem,
  useDeleteWorkItem,
  useRestoreWorkItem,
  useUpdateLabour,
  useUpdateItem,
  useUpdateAssumption,
  useDeleteAssumption,
  useUpdateExclusion,
  useDeleteExclusion,
} from '@/hooks/useContractMutations';
import { formatCents } from '@/lib/format';
import type { Project } from '@/lib/constants';
import { api } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';

// ---------------------------------------------------------------------------
// Labour & Items hooks (inline — fetch per work item on expand)
// ---------------------------------------------------------------------------

interface LabourEntry {
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

interface ItemEntry {
  id: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_cost_cents: number;
  total_cents: number;
  price_source_type?: string | null;
  price_source_id?: string | null;
  source_reasoning?: string | null;
  source_url?: string | null;
  price_fetched_at?: string | null;
}

function useLabour(projectId: string, workItemId: string | null) {
  return useQuery<LabourEntry[]>({
    queryKey: ['labour', projectId, workItemId],
    queryFn: async () => {
      const res = await api.get<{ labour: LabourEntry[]; total: number }>(
        `/me/projects/${projectId}/work-items/${workItemId}/labour`,
      );
      return res.labour;
    },
    enabled: !!workItemId,
  });
}

function useItems(projectId: string, workItemId: string | null) {
  return useQuery<ItemEntry[]>({
    queryKey: ['items', projectId, workItemId],
    queryFn: async () => {
      const res = await api.get<{ items: ItemEntry[]; total: number }>(
        `/me/projects/${projectId}/work-items/${workItemId}/items`,
      );
      return res.items;
    },
    enabled: !!workItemId,
  });
}

// ---------------------------------------------------------------------------
// Work Item Row (expandable, with inline editing)
// ---------------------------------------------------------------------------

function WorkItemRow({
  item,
  projectId,
  canDelete = false,
}: {
  item: {
    id: string;
    description: string;
    state: string;
    quantity: number;
    unit: string;
    labour_cost_cents: number;
    items_cost_cents: number;
    margin_pct: number;
    sell_price_cents: number;
  };
  projectId: string;
  canDelete?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const { data: labour } = useLabour(projectId, expanded ? item.id : null);
  const { data: items } = useItems(projectId, expanded ? item.id : null);

  const updateWorkItem = useUpdateWorkItem(projectId);
  const deleteWorkItem = useDeleteWorkItem(projectId);
  const restoreWorkItem = useRestoreWorkItem(projectId);
  const updateLabour = useUpdateLabour(projectId, item.id);
  const updateItem = useUpdateItem(projectId, item.id);

  const stateBadgeClass: Record<string, string> = {
    draft: 'bg-muted text-muted-foreground',
    scheduled: 'bg-[var(--info-bg)] text-[var(--info)]',
    in_progress: 'bg-[var(--warn-bg)] text-[var(--warn)]',
    complete: 'bg-[var(--pass-bg)] text-[var(--pass)]',
    invoiced: 'bg-purple-50 text-purple-700',
  };

  return (
    <>
      <tr
        className="cursor-pointer transition-colors hover:bg-muted/50"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="px-3 py-2.5">
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
        </td>
        <td className="px-3 py-2.5 text-sm font-medium text-foreground" onClick={(e) => e.stopPropagation()}>
          <EditableCell
            value={item.description}
            type="text"
            onSave={async (v) => {
              await updateWorkItem.mutateAsync({ id: item.id, description: String(v) });
            }}
          />
        </td>
        <td className="px-3 py-2.5 text-sm text-right" onClick={(e) => e.stopPropagation()}>
          <EditableCell
            value={item.quantity}
            type="number"
            onSave={async (v) => {
              await updateWorkItem.mutateAsync({ id: item.id, quantity: Number(v) });
            }}
          />
        </td>
        <td className="px-3 py-2.5 text-sm">{item.unit}</td>
        <td className="px-3 py-2.5 text-sm text-right">{formatCents(item.labour_cost_cents)}</td>
        <td className="px-3 py-2.5 text-sm text-right">{formatCents(item.items_cost_cents)}</td>
        <td className="px-3 py-2.5 text-sm text-right" onClick={(e) => e.stopPropagation()}>
          <EditableCell
            value={item.margin_pct}
            type="percent"
            onSave={async (v) => {
              await updateWorkItem.mutateAsync({ id: item.id, margin_pct: Number(v) });
            }}
          />
        </td>
        <td className="px-3 py-2.5 text-sm font-medium text-right">{formatCents(item.sell_price_cents)}</td>
        <td className="px-3 py-2.5">
          <Badge className={stateBadgeClass[item.state] || 'bg-muted text-muted-foreground'}>
            {item.state}
          </Badge>
        </td>
        {canDelete && (
          <td className="px-3 py-2.5 text-right" onClick={(e) => e.stopPropagation()}>
            <button
              className="rounded p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive disabled:opacity-50"
              onClick={() => {
                if (!window.confirm(`Delete "${item.description}"?`)) {
                  return;
                }
                deleteWorkItem.mutate(item.id, {
                  onSuccess: () => {
                    toast(`Removed "${item.description}"`, {
                      description: 'Labour and items were archived with it.',
                      duration: 8000,
                      action: {
                        label: 'Undo',
                        onClick: () => {
                          restoreWorkItem.mutate(item.id, {
                            onSuccess: () => toast.success('Restored'),
                            onError: () => toast.error('Could not restore — work item may no longer exist.'),
                          });
                        },
                      },
                    });
                  },
                  onError: () => toast.error('Could not remove work item.'),
                });
              }}
              disabled={deleteWorkItem.isPending}
              title="Remove work item"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </td>
        )}
      </tr>

      {expanded && (
        <tr>
          <td colSpan={9} className="bg-muted/30 px-6 py-3">
            <div className="grid gap-4 lg:grid-cols-2">
              {/* Labour */}
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Labour
                </p>
                {labour && labour.length > 0 ? (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-xs text-muted-foreground">
                        <th className="pb-1 text-left font-medium">Task</th>
                        <th className="pb-1 text-right font-medium">Rate</th>
                        <th className="pb-1 text-right font-medium">Hours</th>
                        <th className="pb-1 text-right font-medium">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {labour.map((l) => {
                        const sourceText = l.source_reasoning;
                        const isUnconfirmed =
                          !sourceText && l.rate_source_type === 'contractor_stated';
                        const hasSourceRow = Boolean(sourceText) || isUnconfirmed;
                        return (
                          <React.Fragment key={l.id}>
                            <tr className={hasSourceRow ? '' : 'border-b border-muted last:border-0'}>
                              <td className="py-1.5">
                                <EditableCell
                                  value={l.task}
                                  type="text"
                                  onSave={async (v) => {
                                    await updateLabour.mutateAsync({ id: l.id, task: String(v) });
                                  }}
                                />
                              </td>
                              <td className="py-1.5 text-right">
                                <EditableCell
                                  value={l.rate_cents}
                                  type="currency"
                                  formatDisplay={(v) => `${formatCents(Number(v))}/hr`}
                                  onSave={async (v) => {
                                    await updateLabour.mutateAsync({ id: l.id, rate_cents: Number(v) });
                                  }}
                                />
                              </td>
                              <td className="py-1.5 text-right">
                                <EditableCell
                                  value={l.hours}
                                  type="number"
                                  onSave={async (v) => {
                                    await updateLabour.mutateAsync({ id: l.id, hours: Number(v) });
                                  }}
                                />
                              </td>
                              <td className="py-1.5 text-right font-medium">{formatCents(l.cost_cents)}</td>
                            </tr>
                            {hasSourceRow && (
                              <tr className="border-b border-muted last:border-0">
                                <td colSpan={4} className="pb-1.5 pl-4 pt-0">
                                  {sourceText ? (
                                    <span className="text-[10px] leading-tight text-muted-foreground">
                                      {sourceText}
                                    </span>
                                  ) : (
                                    <span className="text-[10px] leading-tight text-[var(--warn)]">
                                      contractor-stated rate
                                    </span>
                                  )}
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-xs text-muted-foreground">No labour tasks</p>
                )}
              </div>

              {/* Items */}
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Items
                </p>
                {items && items.length > 0 ? (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-xs text-muted-foreground">
                        <th className="pb-1 text-left font-medium">Description</th>
                        <th className="pb-1 text-right font-medium">Qty</th>
                        <th className="pb-1 text-right font-medium">Unit Cost</th>
                        <th className="pb-1 text-right font-medium">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((i) => {
                        const sourceText = i.source_reasoning;
                        const isUnconfirmed =
                          !sourceText && i.price_source_type === 'contractor_stated';
                        const hasSourceRow = Boolean(sourceText) || isUnconfirmed;
                        return (
                          <React.Fragment key={i.id}>
                            <tr className={hasSourceRow ? '' : 'border-b border-muted last:border-0'}>
                              <td className="py-1.5">
                                <EditableCell
                                  value={i.description}
                                  type="text"
                                  onSave={async (v) => {
                                    await updateItem.mutateAsync({ id: i.id, description: String(v) });
                                  }}
                                />
                              </td>
                              <td className="py-1.5 text-right">
                                <EditableCell
                                  value={i.quantity}
                                  type="number"
                                  onSave={async (v) => {
                                    await updateItem.mutateAsync({ id: i.id, quantity: Number(v) });
                                  }}
                                />
                              </td>
                              <td className="py-1.5 text-right">
                                <EditableCell
                                  value={i.unit_cost_cents}
                                  type="currency"
                                  onSave={async (v) => {
                                    await updateItem.mutateAsync({ id: i.id, unit_cost_cents: Number(v) });
                                  }}
                                />
                              </td>
                              <td className="py-1.5 text-right font-medium">{formatCents(i.total_cents)}</td>
                            </tr>
                            {hasSourceRow && (
                              <tr className="border-b border-muted last:border-0">
                                <td colSpan={4} className="pb-1.5 pl-4 pt-0">
                                  {sourceText ? (
                                    i.source_url ? (
                                      <a
                                        href={i.source_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        title={i.source_url}
                                        className="text-[10px] leading-tight text-muted-foreground underline decoration-dotted underline-offset-2 hover:text-foreground"
                                      >
                                        {sourceText}
                                      </a>
                                    ) : (
                                      <span className="text-[10px] leading-tight text-muted-foreground">
                                        {sourceText}
                                      </span>
                                    )
                                  ) : (
                                    <span className="text-[10px] leading-tight text-[var(--warn)]">
                                      contractor-stated price
                                    </span>
                                  )}
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-xs text-muted-foreground">No items</p>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Stage A: Lead / Quoting view
// ---------------------------------------------------------------------------

function QuotingView({ project }: { project: Project }) {
  const { data: summary, isLoading, error, refetch } = useEstimateSummary(project.id);
  const { data: assumptions } = useAssumptions(project.id);
  const { data: exclusions } = useExclusions(project.id);

  const updateAssumption = useUpdateAssumption(project.id);
  const deleteAssumption = useDeleteAssumption(project.id);
  const updateExclusion = useUpdateExclusion(project.id);
  const deleteExclusion = useDeleteExclusion(project.id);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="mt-3 text-sm text-muted-foreground">Loading estimate...</p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <DollarSign className="h-12 w-12 text-muted-foreground" />
        <p className="mt-3 text-sm font-medium text-muted-foreground">
          {error ? 'Failed to load estimate data' : 'No estimate data available'}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Use the chat to create work items and build your quote.
        </p>
        <Button variant="outline" className="mt-4" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      </div>
    );
  }

  const workItems = summary.items?.filter(Boolean) || [];
  const hasItems = workItems.length > 0;

  return (
    <div className="space-y-6">
      {/* Work Items Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Work Items</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="mr-2 h-3.5 w-3.5" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {hasItems ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="w-8 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground" />
                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Description</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Qty</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Unit</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Labour</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Items</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Margin</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Sell Price</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">State</th>
                    <th className="w-10 px-3 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {workItems.map((item) => (
                    <WorkItemRow key={item.id} item={item} projectId={project.id} canDelete />
                  ))}
                </tbody>
              </table>

              {/* Summary Bar */}
              <div className="mt-3 flex gap-6 rounded-[var(--radius-card)] bg-muted px-4 py-3 text-sm font-semibold">
                <div>
                  <span className="font-normal text-muted-foreground">Total Labour </span>
                  {formatCents(summary.total_labour_cents)}
                </div>
                <div>
                  <span className="font-normal text-muted-foreground">Total Items </span>
                  {formatCents(summary.total_items_cents)}
                </div>
                <div>
                  <span className="font-normal text-muted-foreground">Quote Total </span>
                  <span className="text-base">{formatCents(summary.grand_total_cents)}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center py-12 text-center">
              <DollarSign className="h-12 w-12 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">No work items yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Use the chat to add work items: &quot;Create a work item for floor box installation&quot;
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Generate Proposal */}
      {hasItems && (
        <div className="flex justify-end">
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => {
              const input = document.querySelector('input[placeholder="Ask a question..."]') as HTMLInputElement;
              if (input) {
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                nativeInputValueSetter?.call(input, `Generate a proposal document for project ${project.id}`);
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.focus();
                setTimeout(() => {
                  input.form?.dispatchEvent(new Event('submit', { bubbles: true }));
                  const sendBtn = input.parentElement?.querySelector('button');
                  sendBtn?.click();
                }, 100);
              }
            }}
          >
            <FileText className="mr-2 h-4 w-4" />
            Generate Proposal
          </Button>
        </div>
      )}

      {/* Assumptions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertTriangle className="h-4 w-4 text-[var(--warn)]" />
            Assumptions
            {assumptions && assumptions.length > 0 && (
              <Badge variant="secondary" className="ml-1">{assumptions.length}</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {assumptions && assumptions.length > 0 ? (
            <div className="space-y-2">
              {assumptions.map((a) => (
                <div key={a.id} className="flex items-start gap-3 rounded-lg border border-muted p-3">
                  <Badge className="shrink-0 bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]">
                    {a.category}
                  </Badge>
                  <div className="min-w-0 flex-1">
                    <EditableCell
                      value={a.statement}
                      type="text"
                      className="text-sm"
                      onSave={async (v) => {
                        await updateAssumption.mutateAsync({ id: a.id, statement: String(v) });
                      }}
                    />
                    {a.variation_trigger && (
                      <p className="mt-1 text-xs text-[var(--fail)]">
                        Variation trigger: {a.trigger_description || 'Violation may trigger a variation'}
                      </p>
                    )}
                  </div>
                  <button
                    className="shrink-0 rounded p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => deleteAssumption.mutate(a.id)}
                    title="Delete assumption"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No assumptions added yet. Use the chat: &quot;Add an assumption that the programme is 19 weeks&quot;
            </p>
          )}
        </CardContent>
      </Card>

      {/* Exclusions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Ban className="h-4 w-4 text-muted-foreground" />
            Exclusions
            {exclusions && exclusions.length > 0 && (
              <Badge variant="secondary" className="ml-1">{exclusions.length}</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {exclusions && exclusions.length > 0 ? (
            <div className="space-y-2">
              {exclusions.map((e) => (
                <div key={e.id} className="flex items-start gap-3 rounded-lg border border-muted p-3">
                  <Badge variant="secondary" className="shrink-0">{e.category}</Badge>
                  <div className="min-w-0 flex-1">
                    <EditableCell
                      value={e.statement}
                      type="text"
                      className="text-sm"
                      onSave={async (v) => {
                        await updateExclusion.mutateAsync({ id: e.id, statement: String(v) });
                      }}
                    />
                    {e.partial_inclusion && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Partial inclusion: {e.partial_inclusion}
                      </p>
                    )}
                  </div>
                  <button
                    className="shrink-0 rounded p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => deleteExclusion.mutate(e.id)}
                    title="Delete exclusion"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No exclusions added yet. Use the chat to add exclusions.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Contract Terms Sections */}
      <PaymentMilestonesSection projectId={project.id} />
      <ConditionsSection projectId={project.id} />
      <WarrantySection projectId={project.id} />
      <RetentionSection projectId={project.id} />

      {/* Sources Panel — shows where every labour rate and material price came from */}
      {summary && workItems.length > 0 && (
        <SourcesPanel projectId={project.id} summary={summary} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stage B: Active Contract view
// ---------------------------------------------------------------------------

function ActiveContractView({ project }: { project: Project }) {
  const { data: summary, isLoading, refetch } = useEstimateSummary(project.id);
  const { data: assumptions } = useAssumptions(project.id);
  const { data: exclusions } = useExclusions(project.id);

  const workItems = summary?.items?.filter(Boolean) || [];
  const hasItems = workItems.length > 0;

  return (
    <div className="space-y-6">
      {/* Accepted Proposal Card */}
      <div className="flex items-center gap-3.5 rounded-[var(--radius-card)] border border-[rgba(45,138,78,0.15)] bg-[var(--pass-bg)] p-3 text-sm">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[var(--radius-card)] bg-[var(--pass)]">
          <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
        <div>
          <strong>Contract active</strong> — Project is in progress.
        </div>
      </div>

      {/* Contract Value + Change Orders */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Contract Value</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {isLoading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : hasItems ? (
              <>
                <p className="text-3xl font-bold">{formatCents(summary!.grand_total_cents)}</p>
                <div className="flex gap-4 text-muted-foreground">
                  <span>Labour: {formatCents(summary!.total_labour_cents)}</span>
                  <span>Items: {formatCents(summary!.total_items_cents)}</span>
                </div>
                <div className="flex gap-4 text-xs text-muted-foreground">
                  <span>{summary!.item_count} work items</span>
                </div>
              </>
            ) : (
              <p className="text-muted-foreground">No scope items found. Use the chat to add work items.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Change Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">No change orders yet.</p>
          </CardContent>
        </Card>
      </div>

      {/* Work Items — Est vs Actual tracking */}
      {hasItems && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Scope Tracking</CardTitle>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="mr-2 h-3.5 w-3.5" />
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="w-8 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground" />
                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Description</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Qty</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Unit</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Labour</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Items</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Margin</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Sell Price</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">State</th>
                  </tr>
                </thead>
                <tbody>
                  {workItems.map((item) => (
                    <WorkItemRow
                      key={item.id}
                      item={item}
                      projectId={project.id}
                    />
                  ))}
                </tbody>
              </table>

              <div className="mt-3 flex gap-6 rounded-[var(--radius-card)] bg-muted px-4 py-3 text-sm font-semibold">
                <div>
                  <span className="font-normal text-muted-foreground">Total Labour </span>
                  {formatCents(summary!.total_labour_cents)}
                </div>
                <div>
                  <span className="font-normal text-muted-foreground">Total Items </span>
                  {formatCents(summary!.total_items_cents)}
                </div>
                <div>
                  <span className="font-normal text-muted-foreground">Contract Total </span>
                  <span className="text-base">{formatCents(summary!.grand_total_cents)}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Contract Terms Sections */}
      <PaymentMilestonesSection projectId={project.id} />
      <ConditionsSection projectId={project.id} />
      <WarrantySection projectId={project.id} />
      <RetentionSection projectId={project.id} />

      {/* Assumptions */}
      {assumptions && assumptions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-4 w-4 text-[var(--warn)]" />
              Assumptions
              <Badge variant="secondary" className="ml-1">{assumptions.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {assumptions.map((a) => (
                <div key={a.id} className="flex items-start gap-3 rounded-lg border border-muted p-3">
                  <Badge className="shrink-0 bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]">
                    {a.category}
                  </Badge>
                  <p className="text-sm">{a.statement}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Exclusions */}
      {exclusions && exclusions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Ban className="h-4 w-4 text-muted-foreground" />
              Exclusions
              <Badge variant="secondary" className="ml-1">{exclusions.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {exclusions.map((e) => (
                <div key={e.id} className="flex items-start gap-3 rounded-lg border border-muted p-3">
                  <Badge variant="secondary" className="shrink-0">{e.category}</Badge>
                  <p className="text-sm">{e.statement}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stage C: Close-out view
// ---------------------------------------------------------------------------

function CloseoutView({ project }: { project: Project }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Close-out Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Use the chat to track close-out: &quot;Show me the close-out status&quot;
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Final Payments</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Use the chat to track payments: &quot;Show me the payment status&quot;
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Contract Tab
// ---------------------------------------------------------------------------

export function ContractTab({ project }: { project: Project }) {
  switch (project.state) {
    case 'lead':
    case 'quoted':
      return <QuotingView project={project} />;
    case 'active':
      return <ActiveContractView project={project} />;
    case 'completed':
    case 'closed':
      return <CloseoutView project={project} />;
    default:
      return <QuotingView project={project} />;
  }
}
