import { useNavigate } from 'react-router-dom';
import { FileText, Clock, MoreVertical, Pencil, Trash2, Download } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ROUTES, DOCUMENT_TYPES, type Document } from '@/lib/constants';
import { format } from 'date-fns';

interface DocumentCardProps {
  document: Document;
  onDelete: (id: string) => void;
  viewMode: 'grid' | 'table';
}

export function DocumentCard({ document, onDelete, viewMode }: DocumentCardProps) {
  const navigate = useNavigate();
  const docType = DOCUMENT_TYPES.find((t) => t.id === document.document_type);

  if (viewMode === 'table') {
    return (
      <tr
        className="cursor-pointer border-b border-border transition-colors hover:bg-muted"
        onClick={() => navigate(ROUTES.DOCUMENT_EDIT(document.id))}
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
              <FileText className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--concrete-600)]">{document.title}</p>
              <p className="text-xs text-muted-foreground">{docType?.name || document.document_type}</p>
            </div>
          </div>
        </td>
        <td className="hidden px-4 py-3 md:table-cell">
          <Badge
            variant={document.status === 'final' ? 'default' : 'secondary'}
            className={
              document.status === 'final'
                ? 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]'
                : ''
            }
          >
            {document.status === 'final' ? 'Final' : 'Draft'}
          </Badge>
        </td>
        <td className="hidden px-4 py-3 text-sm text-muted-foreground lg:table-cell">
          {format(new Date(document.created_at), 'MMM d, yyyy')}
        </td>
        <td className="px-4 py-3 text-sm text-muted-foreground">
          {format(new Date(document.updated_at), 'MMM d, yyyy')}
        </td>
        <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
          <DropdownMenu>
            <DropdownMenuTrigger className="inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent">
                <MoreVertical className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => navigate(ROUTES.DOCUMENT_EDIT(document.id))}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Download className="mr-2 h-4 w-4" />
                Export PDF
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-[var(--fail)]"
                onClick={() => onDelete(document.id)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </td>
      </tr>
    );
  }

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={() => navigate(ROUTES.DOCUMENT_EDIT(document.id))}
    >
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
            <FileText className="h-5 w-5 text-muted-foreground" />
          </div>
          <div onClick={(e) => e.stopPropagation()}>
            <DropdownMenu>
              <DropdownMenuTrigger className="inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent">
                  <MoreVertical className="h-4 w-4" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => navigate(ROUTES.DOCUMENT_EDIT(document.id))}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Download className="mr-2 h-4 w-4" />
                  Export PDF
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-[var(--fail)]"
                  onClick={() => onDelete(document.id)}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        <div className="mt-3">
          <h3 className="truncate text-sm font-semibold text-foreground">{document.title}</h3>
          <p className="text-xs text-muted-foreground">{docType?.name || document.document_type}</p>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <Badge
            variant={document.status === 'final' ? 'default' : 'secondary'}
            className={
              document.status === 'final'
                ? 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]'
                : ''
            }
          >
            {document.status === 'final' ? 'Final' : 'Draft'}
          </Badge>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {format(new Date(document.updated_at), 'MMM d')}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
