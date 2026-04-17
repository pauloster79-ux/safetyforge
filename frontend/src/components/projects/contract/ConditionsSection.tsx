import { Plus, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EditableCell } from '@/components/ui/editable-cell';
import {
  useConditions,
  useCreateCondition,
  useUpdateCondition,
  useDeleteCondition,
} from '@/hooks/useContractTerms';

const categoryColors: Record<string, string> = {
  site_access: 'bg-blue-50 text-blue-700 hover:bg-blue-50',
  working_hours: 'bg-amber-50 text-amber-700 hover:bg-amber-50',
  permits: 'bg-purple-50 text-purple-700 hover:bg-purple-50',
  materials: 'bg-green-50 text-green-700 hover:bg-green-50',
  client_obligations: 'bg-red-50 text-red-700 hover:bg-red-50',
  insurance: 'bg-teal-50 text-teal-700 hover:bg-teal-50',
  other: 'bg-gray-50 text-gray-700 hover:bg-gray-50',
};

function formatCategory(cat: string): string {
  return cat.replace(/_/g, ' ');
}

export function ConditionsSection({ projectId }: { projectId: string }) {
  const { data: conditions } = useConditions(projectId);
  const createCondition = useCreateCondition(projectId);
  const updateCondition = useUpdateCondition(projectId);
  const deleteCondition = useDeleteCondition(projectId);

  const items = conditions ?? [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          Conditions
          {items.length > 0 && (
            <Badge variant="secondary" className="ml-1">
              {items.length}
            </Badge>
          )}
        </CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            createCondition.mutate({
              category: 'other',
              description: 'New condition',
              responsible_party: '',
            })
          }
        >
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          Add condition
        </Button>
      </CardHeader>
      <CardContent>
        {items.length > 0 ? (
          <div className="space-y-2">
            {items.map((c) => (
              <div
                key={c.id}
                className="flex items-start gap-3 rounded-lg border border-muted p-3"
              >
                <Badge
                  className={
                    categoryColors[c.category] ??
                    'bg-gray-50 text-gray-700 hover:bg-gray-50'
                  }
                >
                  {formatCategory(c.category)}
                </Badge>
                <div className="min-w-0 flex-1 space-y-1">
                  <EditableCell
                    value={c.description}
                    type="text"
                    className="text-sm"
                    onSave={async (v) => {
                      await updateCondition.mutateAsync({
                        id: c.id,
                        description: String(v),
                      });
                    }}
                  />
                  {c.responsible_party && (
                    <p className="text-xs text-muted-foreground">
                      Responsible:{' '}
                      <EditableCell
                        value={c.responsible_party}
                        type="text"
                        className="inline text-xs"
                        onSave={async (v) => {
                          await updateCondition.mutateAsync({
                            id: c.id,
                            responsible_party: String(v),
                          });
                        }}
                      />
                    </p>
                  )}
                </div>
                <button
                  className="shrink-0 rounded p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                  onClick={() => deleteCondition.mutate(c.id)}
                  title="Delete condition"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No conditions added yet. Use the chat: &quot;Add site access conditions
            for this project&quot;
          </p>
        )}
      </CardContent>
    </Card>
  );
}
