import { Percent } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EditableCell } from '@/components/ui/editable-cell';
import { useContractDetail, useUpdateContract } from '@/hooks/useContractTerms';
import { useEstimateSummary } from '@/hooks/useWorkItems';
import { formatCents } from '@/lib/format';

export function RetentionSection({ projectId }: { projectId: string }) {
  const { data: contract } = useContractDetail(projectId);
  const { data: summary } = useEstimateSummary(projectId);
  const updateContract = useUpdateContract(projectId);

  const retentionPct = contract?.retention_pct ?? null;
  const paymentDays = contract?.payment_terms_days ?? null;
  const grandTotal = summary?.grand_total_cents ?? 0;
  const retentionAmount =
    retentionPct != null && grandTotal > 0
      ? Math.round((retentionPct / 100) * grandTotal)
      : null;

  const hasData = retentionPct != null || paymentDays != null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Percent className="h-4 w-4 text-muted-foreground" />
          Retention &amp; Payment Terms
        </CardTitle>
      </CardHeader>
      <CardContent>
        {hasData ? (
          <div className="flex flex-wrap gap-6">
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Retention
              </p>
              <div className="flex items-baseline gap-1">
                <EditableCell
                  value={retentionPct ?? 0}
                  type="percent"
                  className="text-lg font-semibold"
                  onSave={async (v) => {
                    await updateContract.mutateAsync({
                      retention_pct: Number(v),
                    });
                  }}
                />
                {retentionAmount != null && (
                  <span className="text-sm text-muted-foreground">
                    ({formatCents(retentionAmount)})
                  </span>
                )}
              </div>
            </div>
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Payment terms
              </p>
              <div className="flex items-baseline gap-1">
                <span className="text-sm text-muted-foreground">Net</span>
                <EditableCell
                  value={paymentDays ?? 30}
                  type="number"
                  className="text-lg font-semibold"
                  onSave={async (v) => {
                    await updateContract.mutateAsync({
                      payment_terms_days: Number(v),
                    });
                  }}
                />
                <span className="text-sm text-muted-foreground">days</span>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            Defaults: 5% retention, Net 30 payment terms. Use the chat to adjust:
            &quot;Set retention to 10% with Net 45 terms&quot;
          </p>
        )}
      </CardContent>
    </Card>
  );
}
