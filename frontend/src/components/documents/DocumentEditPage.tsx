import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import {
  ArrowLeft,
  Save,
  Download,
  Trash2,
  Loader2,
  Check,
  RefreshCw,
  Pencil,
  Eye,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useDocument, useUpdateDocument, useDeleteDocument, useGenerateDocument } from '@/hooks/useDocuments';
import { useAuth } from '@/hooks/useAuth';
import { ROUTES, DOCUMENT_TYPES } from '@/lib/constants';
import { ContentRenderer } from './ContentRenderer';
import { cn } from '@/lib/utils';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/** Format a snake_case key into a readable section heading. */
function formatSectionKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Safely format an ISO date string. */
function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

export function DocumentEditPage({ documentId: propDocumentId }: { documentId?: string } = {}) {
  const params = useParams<{ id: string }>();
  const id = propDocumentId || params.id;
  const navigate = useCanvasNavigate();
  const { getToken, isDemoMode } = useAuth();

  const { data: document, isLoading } = useDocument(id);
  const updateDocument = useUpdateDocument();
  const deleteDocument = useDeleteDocument();
  const regenerateDocument = useGenerateDocument();

  const [title, setTitle] = useState('');
  const [contentSections, setContentSections] = useState<Record<string, unknown>>({});
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [editBuffer, setEditBuffer] = useState<string>('');
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [pdfMessage, setPdfMessage] = useState<string | null>(null);

  useEffect(() => {
    if (document) {
      setTitle(document.title);
      setContentSections(document.content || {});
    }
  }, [document]);

  const handleStartEdit = (key: string) => {
    setEditingSection(key);
    setEditBuffer(JSON.stringify(contentSections[key], null, 2));
  };

  const handleStopEdit = (key: string) => {
    try {
      const parsed = JSON.parse(editBuffer);
      setContentSections((prev) => ({ ...prev, [key]: parsed }));
      setHasChanges(true);
    } catch {
      // If JSON is invalid, keep the original value
    }
    setEditingSection(null);
    setEditBuffer('');
  };

  const handleSave = async (status?: 'draft' | 'final') => {
    if (!id) return;

    await updateDocument.mutateAsync({
      id,
      title,
      status: status || document?.status,
      content: contentSections,
    });

    setHasChanges(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handleDelete = async () => {
    if (!id) return;
    await deleteDocument.mutateAsync(id);
    navigate(ROUTES.DOCUMENTS);
  };

  const handleRegenerate = async () => {
    if (!id) return;
    setShowRegenerateDialog(false);
    await regenerateDocument.mutateAsync({ document_id: id });
  };

  const handleExportPdf = useCallback(async () => {
    if (!id || !document) return;

    if (isDemoMode) {
      setPdfMessage('PDF export available in production mode');
      setTimeout(() => setPdfMessage(null), 3000);
      return;
    }

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/me/documents/${id}/pdf`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = `${document.title}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setPdfMessage('Failed to export PDF. Please try again.');
      setTimeout(() => setPdfMessage(null), 3000);
    }
  }, [id, document, isDemoMode, getToken]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!document) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <h2 className="text-lg font-medium text-muted-foreground">Document not found</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          The document you are looking for does not exist or has been deleted.
        </p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate(ROUTES.DOCUMENTS)}
        >
          Back to Documents
        </Button>
      </div>
    );
  }

  const docType = DOCUMENT_TYPES.find((t) => t.id === document.document_type);
  const sectionKeys = Object.keys(contentSections);

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(ROUTES.DOCUMENTS)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="min-w-0 flex-1">
            <Input
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                setHasChanges(true);
              }}
              className="border-none bg-transparent p-0 text-xl font-bold text-foreground shadow-none focus-visible:ring-0"
            />
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{docType?.name || document.document_type}</span>
              <span>-</span>
              <span>Last updated {formatDate(document.updated_at)}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge
            variant={document.status === 'final' ? 'default' : 'secondary'}
            className={cn(
              'cursor-pointer',
              document.status === 'final'
                ? 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]'
                : 'hover:bg-muted'
            )}
            onClick={() =>
              handleSave(document.status === 'final' ? 'draft' : 'final')
            }
          >
            {document.status === 'final' ? 'Final' : 'Draft'}
          </Badge>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowRegenerateDialog(true)}
            disabled={regenerateDocument.isPending}
          >
            <RefreshCw className={cn('mr-1 h-4 w-4', regenerateDocument.isPending && 'animate-spin')} />
            Regenerate
          </Button>

          <Button variant="outline" size="sm" onClick={handleExportPdf}>
            <Download className="mr-1 h-4 w-4" />
            Export PDF
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="text-[var(--fail)] hover:bg-[var(--fail-bg)] hover:text-[var(--fail)]"
            onClick={() => setShowDeleteDialog(true)}
          >
            <Trash2 className="mr-1 h-4 w-4" />
            Delete
          </Button>

          <Button
            size="sm"
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => handleSave()}
            disabled={!hasChanges || updateDocument.isPending}
          >
            {updateDocument.isPending ? (
              <Loader2 className="mr-1 h-4 w-4 animate-spin" />
            ) : saveSuccess ? (
              <Check className="mr-1 h-4 w-4" />
            ) : (
              <Save className="mr-1 h-4 w-4" />
            )}
            {saveSuccess ? 'Saved' : 'Save'}
          </Button>
        </div>
      </div>

      {/* PDF toast */}
      {pdfMessage && (
        <div className="mb-4 rounded-lg border border-primary bg-[var(--machine-wash)] px-4 py-3 text-sm text-primary">
          {pdfMessage}
        </div>
      )}

      <Separator className="mb-6" />

      <div className="space-y-4">
        {sectionKeys.length > 0 ? (
          sectionKeys.map((key) => (
            <Card key={key}>
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <CardTitle className="text-base">{formatSectionKey(key)}</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    editingSection === key
                      ? handleStopEdit(key)
                      : handleStartEdit(key)
                  }
                >
                  {editingSection === key ? (
                    <>
                      <Eye className="mr-1 h-4 w-4" />
                      Preview
                    </>
                  ) : (
                    <>
                      <Pencil className="mr-1 h-4 w-4" />
                      Edit
                    </>
                  )}
                </Button>
              </CardHeader>
              <CardContent>
                {editingSection === key ? (
                  <Textarea
                    value={editBuffer}
                    onChange={(e) => setEditBuffer(e.target.value)}
                    rows={Math.max(8, editBuffer.split('\n').length + 2)}
                    className="font-mono text-sm"
                  />
                ) : (
                  <ContentRenderer data={contentSections[key]} sectionKey={key} />
                )}
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center py-12 text-center">
              <Loader2 className="h-8 w-8 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">
                No content generated yet
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Click Regenerate to create content for this document
              </p>
              <Button
                className="mt-4 bg-primary hover:bg-[var(--machine-dark)]"
                onClick={() => setShowRegenerateDialog(true)}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Generate Content
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Document</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &quot;{document.title}&quot;? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
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

      <Dialog open={showRegenerateDialog} onOpenChange={setShowRegenerateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Regenerate Document</DialogTitle>
            <DialogDescription>
              This will regenerate the entire document content using AI. Any manual edits will be lost. Continue?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRegenerateDialog(false)}>
              Cancel
            </Button>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={handleRegenerate}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Regenerate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
