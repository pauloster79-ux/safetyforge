/**
 * QueryCanvasPage — browse and execute registered graph queries.
 *
 * Shows query cards grouped by category. Clicking a card executes the query
 * and renders results in a table below.
 */

import { useState, useMemo } from 'react';
import {
  Database,
  Loader2,
  Play,
  ShieldCheck,
  DollarSign,
  CalendarDays,
  AlertTriangle,
  BarChart3,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useQueries,
  useQueryExecution,
  type RegisteredQuery,
  type QueryResult,
} from '@/hooks/useQueryCanvas';

const CATEGORY_CONFIG: Record<string, { label: string; icon: typeof Database; color: string }> = {
  compliance: {
    label: 'Compliance',
    icon: ShieldCheck,
    color: 'text-blue-600 bg-blue-50 border-blue-200',
  },
  cost: {
    label: 'Cost',
    icon: DollarSign,
    color: 'text-emerald-600 bg-emerald-50 border-emerald-200',
  },
  schedule: {
    label: 'Schedule',
    icon: CalendarDays,
    color: 'text-purple-600 bg-purple-50 border-purple-200',
  },
  safety: {
    label: 'Safety',
    icon: AlertTriangle,
    color: 'text-amber-600 bg-amber-50 border-amber-200',
  },
};

function CategoryBadge({ category }: { category: string }) {
  const config = CATEGORY_CONFIG[category] || {
    label: category,
    icon: BarChart3,
    color: 'text-gray-600 bg-gray-50 border-gray-200',
  };
  const Icon = config.icon;
  return (
    <Badge
      variant="outline"
      className={`gap-1 text-[10px] px-1.5 py-0 ${config.color}`}
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  );
}

function QueryCard({
  query,
  isActive,
  isRunning,
  onRun,
}: {
  query: RegisteredQuery;
  isActive: boolean;
  isRunning: boolean;
  onRun: () => void;
}) {
  return (
    <Card
      className={`cursor-pointer transition-all hover:shadow-md ${
        isActive ? 'ring-2 ring-primary border-primary' : ''
      }`}
      onClick={onRun}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-sm font-medium leading-snug">
            {query.name}
          </CardTitle>
          <CategoryBadge category={query.category} />
        </div>
        <CardDescription className="text-xs">
          {query.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <Button
          variant="ghost"
          size="sm"
          className="h-7 gap-1 px-2 text-xs text-primary hover:text-primary"
          onClick={(e) => {
            e.stopPropagation();
            onRun();
          }}
          disabled={isRunning}
        >
          {isRunning ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Play className="h-3 w-3" />
          )}
          Run
        </Button>
      </CardContent>
    </Card>
  );
}

function ResultTable({ result }: { result: QueryResult }) {
  if (result.rows.length === 0) {
    return (
      <div className="flex flex-col items-center py-12 text-center text-muted-foreground">
        <Database className="h-10 w-10 mb-2 opacity-40" />
        <p className="text-sm font-medium">No results</p>
        <p className="text-xs mt-1">This query returned 0 rows.</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            {result.columns.map((col) => (
              <TableHead key={col} className="text-xs font-semibold uppercase tracking-wider whitespace-nowrap">
                {col.replace(/_/g, ' ')}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {result.rows.map((row, idx) => (
            <TableRow key={idx}>
              {result.columns.map((col) => (
                <TableCell key={col} className="text-sm whitespace-nowrap max-w-[300px] truncate">
                  {row[col] != null ? String(row[col]) : '-'}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export function QueryCanvasPage() {
  const { data: queries, isLoading, error } = useQueries();
  const execution = useQueryExecution();
  const [activeQueryId, setActiveQueryId] = useState<string | null>(null);

  // Group queries by category
  const grouped = useMemo(() => {
    if (!queries) return {};
    const groups: Record<string, RegisteredQuery[]> = {};
    for (const q of queries) {
      (groups[q.category] ??= []).push(q);
    }
    return groups;
  }, [queries]);

  const handleRun = (queryId: string) => {
    setActiveQueryId(queryId);
    execution.mutate(queryId);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center py-16 text-center text-muted-foreground">
        <Database className="h-10 w-10 mb-2 opacity-40" />
        <p className="text-sm">Failed to load queries</p>
        <p className="text-xs mt-1">{error.message}</p>
      </div>
    );
  }

  const categoryOrder = ['compliance', 'safety', 'schedule', 'cost'];

  return (
    <div className="mx-auto max-w-5xl space-y-6 pb-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Query Canvas</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Browse and run pre-built graph queries against your project data.
        </p>
      </div>

      {/* Query cards grouped by category */}
      {categoryOrder.map((cat) => {
        const catQueries = grouped[cat];
        if (!catQueries || catQueries.length === 0) return null;
        const config = CATEGORY_CONFIG[cat] || { label: cat, icon: Database };
        const Icon = config.icon;
        return (
          <div key={cat}>
            <div className="flex items-center gap-2 mb-3">
              <Icon className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                {config.label}
              </h2>
              <span className="text-xs text-muted-foreground">({catQueries.length})</span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {catQueries.map((q) => (
                <QueryCard
                  key={q.id}
                  query={q}
                  isActive={activeQueryId === q.id}
                  isRunning={execution.isPending && activeQueryId === q.id}
                  onRun={() => handleRun(q.id)}
                />
              ))}
            </div>
          </div>
        );
      })}

      {/* Remaining categories not in the ordered list */}
      {Object.keys(grouped)
        .filter((cat) => !categoryOrder.includes(cat))
        .map((cat) => {
          const catQueries = grouped[cat];
          if (!catQueries || catQueries.length === 0) return null;
          return (
            <div key={cat}>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                {cat} ({catQueries.length})
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {catQueries.map((q) => (
                  <QueryCard
                    key={q.id}
                    query={q}
                    isActive={activeQueryId === q.id}
                    isRunning={execution.isPending && activeQueryId === q.id}
                    onRun={() => handleRun(q.id)}
                  />
                ))}
              </div>
            </div>
          );
        })}

      {/* Results */}
      {execution.isPending && (
        <Card>
          <CardContent className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Running query...</span>
          </CardContent>
        </Card>
      )}

      {execution.isSuccess && execution.data && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">{execution.data.name}</CardTitle>
              <Badge variant="secondary" className="text-xs">
                {execution.data.total} {execution.data.total === 1 ? 'row' : 'rows'}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <ResultTable result={execution.data} />
          </CardContent>
        </Card>
      )}

      {execution.isError && (
        <Card className="border-[var(--fail)]">
          <CardContent className="py-6 text-center text-sm text-[var(--fail)]">
            Query failed: {execution.error?.message || 'Unknown error'}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
