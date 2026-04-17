import { Plus, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EditableCell } from '@/components/ui/editable-cell';
import {
  usePaymentMilestones,
  useCreatePaymentMilestone,
  useUpdatePaymentMilestone,
  useDeletePaymentMilestone,
} from '@/hooks/useContractTerms';
import { formatCents } from '@/lib/format';

const statusBadge: Record<string, string> = {
  pending: 'bg-muted text-muted-foreground',
  invoiced: 'bg-[var(--info-bg)] text-[var(--info)]',
  paid: 'bg-[var(--pass-bg)] text-[var(--pass)]',
};

export function PaymentMilestonesSection({ projectId }: { projectId: string }) {
  const { data: milestones } = usePaymentMilestones(projectId);
  const createMilestone = useCreatePaymentMilestone(projectId);
  const updateMilestone = useUpdatePaymentMilestone(projectId);
  const deleteMilestone = useDeletePaymentMilestone(projectId);

  const items = milestones ?? [];
  const totalPct = items.reduce((sum, m) => sum + (m.percentage ?? 0), 0);

  const progressColor =
    totalPct === 100
      ? 'bg-[var(--pass)]'
      : totalPct > 100
        ? 'bg-[var(--fail)]'
        : 'bg-[var(--warn)]';

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">Payment Milestones</CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            createMilestone.mutate({
              description: 'New milestone',
              percentage: 0,
              trigger_condition: '',
              status: 'pending',
            })
          }
        >
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          Add milestone
        </Button>
      </CardHeader>
      <CardContent>
        {items.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-xs text-muted-foreground">
                    <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide">
                      Description
                    </th>
                    <th className="px-3 py-2 text-right font-semibold uppercase tracking-wide">
                      % or Amount
                    </th>
                    <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide">
                      Trigger Condition
                    </th>
                    <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide">
                      Status
                    </th>
                    <th className="w-10 px-3 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {items.map((m) => (
                    <tr
                      key={m.id}
                      className="border-b border-muted last:border-0"
                    >
                      <td className="px-3 py-2">
                        <EditableCell
                          value={m.description}
                          type="text"
                          onSave={async (v) => {
                            await updateMilestone.mutateAsync({
                              id: m.id,
                              description: String(v),
                            });
                          }}
                        />
                      </td>
                      <td className="px-3 py-2 text-right">
                        {m.percentage != null ? (
                          <EditableCell
                            value={m.percentage}
                            type="percent"
                            onSave={async (v) => {
                              await updateMilestone.mutateAsync({
                                id: m.id,
                                percentage: Number(v),
                              });
                            }}
                          />
                        ) : m.amount_cents != null ? (
                          <EditableCell
                            value={m.amount_cents}
                            type="currency"
                            onSave={async (v) => {
                              await updateMilestone.mutateAsync({
                                id: m.id,
                                amount_cents: Number(v),
                              });
                            }}
                          />
                        ) : (
                          <EditableCell
                            value={0}
                            type="percent"
                            onSave={async (v) => {
                              await updateMilestone.mutateAsync({
                                id: m.id,
                                percentage: Number(v),
                              });
                            }}
                          />
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <EditableCell
                          value={m.trigger_condition}
                          type="text"
                          onSave={async (v) => {
                            await updateMilestone.mutateAsync({
                              id: m.id,
                              trigger_condition: String(v),
                            });
                          }}
                        />
                      </td>
                      <td className="px-3 py-2">
                        <Badge
                          className={
                            statusBadge[m.status] ??
                            'bg-muted text-muted-foreground'
                          }
                        >
                          {m.status}
                        </Badge>
                      </td>
                      <td className="px-3 py-2">
                        <button
                          className="rounded p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                          onClick={() => deleteMilestone.mutate(m.id)}
                          title="Delete milestone"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Progress bar */}
            <div className="mt-4">
              <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                <span>Total allocated</span>
                <span className={totalPct !== 100 ? 'font-semibold text-[var(--warn)]' : ''}>
                  {totalPct}%
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={`h-full rounded-full transition-all ${progressColor}`}
                  style={{ width: `${Math.min(totalPct, 100)}%` }}
                />
              </div>
              {totalPct !== 100 && (
                <p className="mt-1 text-xs text-[var(--warn)]">
                  {totalPct < 100
                    ? `${100 - totalPct}% unallocated`
                    : `${totalPct - 100}% over-allocated`}
                </p>
              )}
            </div>
          </>
        ) : (
          <p className="text-sm text-muted-foreground">
            No payment milestones yet. Use the chat: &quot;Set up a 50/25/25 payment
            schedule&quot;
          </p>
        )}
      </CardContent>
    </Card>
  );
}
