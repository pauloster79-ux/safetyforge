import { useState, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Plus,
  Search,
  LayoutGrid,
  List,
  FileText,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useDocuments, useDeleteDocument } from '@/hooks/useDocuments';
import { ROUTES, DOCUMENT_TYPES } from '@/lib/constants';
import { DocumentCard } from './DocumentCard';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

export function DocumentListPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [viewMode, setViewModeState] = useState<'grid' | 'table'>(() => {
    const saved = localStorage.getItem('kerf_doc_view_mode');
    return saved === 'table' ? 'table' : 'grid';
  });
  const setViewMode = (mode: 'grid' | 'table') => {
    setViewModeState(mode);
    localStorage.setItem('kerf_doc_view_mode', mode);
  };
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const typeFilter = searchParams.get('type') || '';
  const statusFilter = searchParams.get('status') || '';
  const searchQuery = searchParams.get('q') || '';
  const sortBy = searchParams.get('sort') || '-updated_at';

  const { data: documents, isLoading } = useDocuments({
    type: typeFilter || undefined,
    status: statusFilter || undefined,
    search: searchQuery || undefined,
    sort: sortBy,
  });

  const deleteDocument = useDeleteDocument();

  const filteredDocs = useMemo(() => {
    if (!documents) return [];
    let filtered = [...documents];

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (d) =>
          d.title.toLowerCase().includes(q) ||
          d.document_type.toLowerCase().includes(q)
      );
    }

    return filtered;
  }, [documents, searchQuery]);

  const handleSearch = (value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set('q', value);
    } else {
      params.delete('q');
    }
    setSearchParams(params);
  };

  const handleTypeFilter = (value: string | null) => {
    const params = new URLSearchParams(searchParams);
    if (value && !value.startsWith('All')) {
      params.set('type', value);
    } else {
      params.delete('type');
    }
    setSearchParams(params);
  };

  const handleStatusFilter = (value: string | null) => {
    const params = new URLSearchParams(searchParams);
    if (value && !value.startsWith('All')) {
      params.set('status', value);
    } else {
      params.delete('status');
    }
    setSearchParams(params);
  };

  const handleSortChange = (value: string | null) => {
    if (!value) return;
    const params = new URLSearchParams(searchParams);
    params.set('sort', value);
    setSearchParams(params);
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    await deleteDocument.mutateAsync(deleteId);
    setDeleteId(null);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Documents</h1>
          <p className="text-sm text-muted-foreground">
            Manage all your safety compliance documents
          </p>
        </div>
        <Button
          className="bg-primary hover:bg-[var(--machine-dark)]"
          onClick={() => navigate(ROUTES.DOCUMENT_NEW)}
        >
          <Plus className="mr-2 h-4 w-4" />
          New Document
        </Button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search documents..."
            className="pl-9"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </div>

        <div className="flex gap-2">
          <Select value={typeFilter || 'All'} onValueChange={handleTypeFilter}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All Types">All Types</SelectItem>
              {DOCUMENT_TYPES.map((type) => (
                <SelectItem key={type.id} value={type.id}>
                  {type.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={statusFilter || 'All'} onValueChange={handleStatusFilter}>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All Status">All Status</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="final">Final</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={handleSortChange}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="-updated_at">Last Updated</SelectItem>
              <SelectItem value="-created_at">Newest First</SelectItem>
              <SelectItem value="created_at">Oldest First</SelectItem>
              <SelectItem value="title">Title A-Z</SelectItem>
            </SelectContent>
          </Select>

          <div className="hidden items-center gap-1 rounded-lg border border-border p-1 sm:flex">
            <Button
              variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
              size="icon"
              className="h-7 w-7"
              onClick={() => setViewMode('grid')}
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'table' ? 'secondary' : 'ghost'}
              size="icon"
              className="h-7 w-7"
              onClick={() => setViewMode('table')}
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : filteredDocs.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredDocs.map((doc) => (
              <DocumentCard
                key={doc.id}
                document={doc}
                onDelete={setDeleteId}
                viewMode="grid"
              />
            ))}
          </div>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border bg-card">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted">
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                    Document
                  </th>
                  <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground md:table-cell">
                    Status
                  </th>
                  <th className="hidden px-4 py-3 text-left text-xs font-medium text-muted-foreground lg:table-cell">
                    Created
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                    Updated
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredDocs.map((doc) => (
                  <DocumentCard
                    key={doc.id}
                    document={doc}
                    onDelete={setDeleteId}
                    viewMode="table"
                  />
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <FileText className="h-16 w-16 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium text-muted-foreground">No documents found</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {searchQuery || typeFilter || statusFilter
              ? 'Try adjusting your filters or search query'
              : 'Create your first safety document to get started'}
          </p>
          {!searchQuery && !typeFilter && !statusFilter && (
            <Button
              className="mt-4 bg-primary hover:bg-[var(--machine-dark)]"
              onClick={() => navigate(ROUTES.DOCUMENT_NEW)}
            >
              <Plus className="mr-2 h-4 w-4" />
              Create Document
            </Button>
          )}
        </div>
      )}

      <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Document</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this document? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteDocument.isPending}
            >
              {deleteDocument.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
