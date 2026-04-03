import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Document } from '@/lib/constants';

interface DocumentListParams {
  type?: string;
  status?: string;
  search?: string;
  sort?: string;
}

interface CreateDocumentPayload {
  title: string;
  document_type: string;
  project_info: Record<string, string>;
}

interface GenerateDocumentPayload {
  document_id: string;
}

interface UpdateDocumentPayload {
  id: string;
  title?: string;
  status?: string;
  content?: Record<string, unknown>;
}

export function useDocuments(params?: DocumentListParams) {
  const searchParams = new URLSearchParams();
  searchParams.set('limit', '20');
  searchParams.set('offset', '0');
  if (params?.type) searchParams.set('type', params.type);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.sort) searchParams.set('sort', params.sort);

  const queryString = searchParams.toString();

  return useQuery<Document[]>({
    queryKey: ['documents', params],
    queryFn: async () => {
      const response = await api.get<{ documents: Document[]; total: number }>(
        `/me/documents?${queryString}`,
      );
      return response.documents;
    },
  });
}

export function useDocument(id: string | undefined) {
  return useQuery<Document>({
    queryKey: ['documents', id],
    queryFn: () => api.get<Document>(`/me/documents/${id}`),
    enabled: !!id,
  });
}

export function useRecentDocuments(limit = 5) {
  return useQuery<Document[]>({
    queryKey: ['documents', 'recent', limit],
    queryFn: async () => {
      const response = await api.get<{ documents: Document[]; total: number }>(
        `/me/documents?limit=${limit}&sort=created_at:desc`,
      );
      return response.documents;
    },
  });
}

export function useCreateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateDocumentPayload) =>
      api.post<Document>('/me/documents', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

export function useGenerateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GenerateDocumentPayload) =>
      api.post<Document>(`/me/documents/${data.document_id}/generate`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.setQueryData(['documents', data.id], data);
    },
  });
}

export function useUpdateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: UpdateDocumentPayload) =>
      api.patch<Document>(`/me/documents/${id}`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.setQueryData(['documents', data.id], data);
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/me/documents/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

export function useDocumentStats() {
  return useQuery<{
    total_documents: number;
    documents_this_month: number;
    by_type: Record<string, number>;
    by_status: Record<string, number>;
  }>({
    queryKey: ['documents', 'stats'],
    queryFn: () => api.get('/me/documents/stats'),
  });
}
