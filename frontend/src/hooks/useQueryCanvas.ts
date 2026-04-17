import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface RegisteredQuery {
  id: string;
  name: string;
  description: string;
  category: string;
  columns: string[];
}

export interface QueryResult {
  query_id: string;
  name: string;
  columns: string[];
  rows: Record<string, unknown>[];
  total: number;
}

export function useQueries() {
  return useQuery<RegisteredQuery[]>({
    queryKey: ['query-canvas'],
    queryFn: async () => {
      const response = await api.get<{ queries: RegisteredQuery[]; total: number }>('/me/queries');
      return response.queries;
    },
  });
}

export function useQueryExecution() {
  return useMutation<QueryResult, Error, string>({
    mutationFn: (queryId: string) =>
      api.get<QueryResult>(`/me/queries/${queryId}/run`),
  });
}
