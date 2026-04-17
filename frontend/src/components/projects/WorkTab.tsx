import { useEffect } from 'react';
import { Loader2, Hammer } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useEstimateSummary } from '@/hooks/useWorkItems';
import { useInspections } from '@/hooks/useInspections';
import { useShell } from '@/hooks/useShell';
import { formatCents } from '@/lib/format';
import { format } from 'date-fns';

export function WorkTab({ projectId }: { projectId: string }) {
  const { data: summary, isLoading, refetch, hasFetched } = useEstimateSummary(projectId);
  const { data: inspections } = useInspections(projectId);
  const shell = useShell();

  // Fetch on mount — but only once
  useEffect(() => {
    if (!hasFetched) refetch();
  }, [hasFetched, refetch]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const workItems = summary?.items?.filter(Boolean) || [];

  const stateBadgeClass: Record<string, string> = {
    draft: 'bg-muted text-muted-foreground',
    scheduled: 'bg-[var(--info-bg)] text-[var(--info)]',
    in_progress: 'bg-[var(--warn-bg)] text-[var(--warn)]',
    complete: 'bg-[var(--pass-bg)] text-[var(--pass)]',
    invoiced: 'bg-purple-50 text-purple-700',
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Scope Items</CardTitle>
        </CardHeader>
        <CardContent>
          {workItems.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Description</th>
                  <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Qty</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Unit</th>
                  <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Cost</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">State</th>
                </tr>
              </thead>
              <tbody>
                {workItems.map((item) => (
                  <tr key={item.id} className="border-b border-muted last:border-0">
                    <td className="px-3 py-2.5 font-medium">{item.description}</td>
                    <td className="px-3 py-2.5 text-right">{item.quantity}</td>
                    <td className="px-3 py-2.5">{item.unit}</td>
                    <td className="px-3 py-2.5 text-right">{formatCents(item.sell_price_cents)}</td>
                    <td className="px-3 py-2.5">
                      <Badge className={stateBadgeClass[item.state] || 'bg-muted text-muted-foreground'}>
                        {item.state}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="flex flex-col items-center py-12 text-center">
              <Hammer className="h-12 w-12 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">No work items yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Use the chat to add work items to this project.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upcoming Inspections */}
      {inspections && inspections.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Upcoming Inspections</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Date</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Type</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Inspector</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</th>
                </tr>
              </thead>
              <tbody>
                {inspections.slice(0, 5).map((insp) => (
                  <tr
                    key={insp.id}
                    className="cursor-pointer border-b border-muted last:border-0 hover:bg-muted/50"
                    onClick={() => shell.openCanvas({ component: 'InspectionDetailPage', props: { projectId, inspectionId: insp.id }, label: 'Inspection' })}
                  >
                    <td className="px-3 py-2.5">
                      {format(new Date(insp.inspection_date), 'MMM d')}
                    </td>
                    <td className="px-3 py-2.5">{insp.inspection_type}</td>
                    <td className="px-3 py-2.5">{insp.inspector_name}</td>
                    <td className="px-3 py-2.5">
                      <Badge className={
                        insp.overall_status === 'pass'
                          ? 'bg-[var(--pass-bg)] text-[var(--pass)]'
                          : insp.overall_status === 'fail'
                            ? 'bg-[var(--fail-bg)] text-[var(--fail)]'
                            : 'bg-[var(--warn-bg)] text-[var(--warn)]'
                      }>
                        {insp.overall_status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
