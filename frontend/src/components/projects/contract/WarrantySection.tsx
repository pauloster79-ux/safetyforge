import { ShieldCheck } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EditableCell } from '@/components/ui/editable-cell';
import { useWarranty, useSetWarranty } from '@/hooks/useContractTerms';

const START_TRIGGER_OPTIONS = [
  'practical_completion',
  'handover',
  'final_payment',
  'certificate_of_occupancy',
] as const;

function formatTrigger(trigger: string): string {
  return trigger.replace(/_/g, ' ');
}

export function WarrantySection({ projectId }: { projectId: string }) {
  const { data: warranty } = useWarranty(projectId);
  const setWarranty = useSetWarranty(projectId);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <ShieldCheck className="h-4 w-4 text-muted-foreground" />
          Warranty
        </CardTitle>
      </CardHeader>
      <CardContent>
        {warranty ? (
          <div className="space-y-3">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Period
                </p>
                <div className="flex items-baseline gap-1">
                  <EditableCell
                    value={warranty.period_months}
                    type="number"
                    className="text-lg font-semibold"
                    onSave={async (v) => {
                      await setWarranty.mutateAsync({
                        period_months: Number(v),
                        scope: warranty.scope,
                        start_trigger: warranty.start_trigger,
                        terms: warranty.terms,
                      });
                    }}
                  />
                  <span className="text-sm text-muted-foreground">months</span>
                </div>
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Starts from
                </p>
                <EditableCell
                  value={warranty.start_trigger}
                  type="text"
                  formatDisplay={(v) => formatTrigger(String(v))}
                  className="text-sm"
                  onSave={async (v) => {
                    const val = String(v);
                    const trigger = START_TRIGGER_OPTIONS.includes(
                      val as (typeof START_TRIGGER_OPTIONS)[number],
                    )
                      ? val
                      : warranty.start_trigger;
                    await setWarranty.mutateAsync({
                      period_months: warranty.period_months,
                      scope: warranty.scope,
                      start_trigger: trigger,
                      terms: warranty.terms,
                    });
                  }}
                />
              </div>
            </div>
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Scope
              </p>
              <EditableCell
                value={warranty.scope}
                type="text"
                className="text-sm"
                onSave={async (v) => {
                  await setWarranty.mutateAsync({
                    period_months: warranty.period_months,
                    scope: String(v),
                    start_trigger: warranty.start_trigger,
                    terms: warranty.terms,
                  });
                }}
              />
            </div>
            {warranty.terms && (
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Terms
                </p>
                <EditableCell
                  value={warranty.terms}
                  type="text"
                  className="text-sm"
                  onSave={async (v) => {
                    await setWarranty.mutateAsync({
                      period_months: warranty.period_months,
                      scope: warranty.scope,
                      start_trigger: warranty.start_trigger,
                      terms: String(v),
                    });
                  }}
                />
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No warranty terms set. Use the chat: &quot;Set 12-month warranty from
            practical completion&quot;
          </p>
        )}
      </CardContent>
    </Card>
  );
}
