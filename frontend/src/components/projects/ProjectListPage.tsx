import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  MapPin,
  Users,
  Building2,
  ClipboardCheck,
  FileText,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useProjects } from '@/hooks/useProjects';
import { ROUTES } from '@/lib/constants';
import type { Project } from '@/lib/constants';
import { ComplianceRing } from './ComplianceRing';

function StatusBadge({ status }: { status: Project['status'] }) {
  const config = {
    active: { label: 'Active', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    on_hold: { label: 'On Hold', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
    completed: { label: 'Completed', className: 'bg-muted text-muted-foreground hover:bg-muted' },
  };
  const { label, className } = config[status];
  return <Badge className={className}>{label}</Badge>;
}

export function ProjectListPage() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string>('All');

  const { data: projects, isLoading } = useProjects(
    !statusFilter.startsWith('All') ? { status: statusFilter } : undefined
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Projects</h1>
          <p className="text-sm text-muted-foreground">
            Manage all your construction projects and compliance
          </p>
        </div>
        <Button
          className="bg-primary hover:bg-[var(--machine-dark)]"
          onClick={() => navigate(ROUTES.PROJECT_NEW)}
        >
          <Plus className="mr-2 h-4 w-4" />
          New Project
        </Button>
      </div>

      <div className="flex items-center gap-3">
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v || 'All')}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="All Status">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="on_hold">On Hold</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : projects && projects.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => navigate(ROUTES.PROJECT_DETAIL(project.id))}
            >
              <CardContent className="pt-6">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate text-sm font-semibold text-foreground">
                      {project.name}
                    </h3>
                    <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                      <MapPin className="h-3 w-3 shrink-0" />
                      <span className="truncate">{project.address}</span>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">{project.client_name}</p>
                  </div>
                  <ComplianceRing score={project.compliance_score} size="sm" />
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <StatusBadge status={project.status} />
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Users className="h-3 w-3" />
                    <span>{project.estimated_workers} workers</span>
                  </div>
                </div>

                <div className="mt-3 flex items-center gap-2 border-t border-border pt-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 flex-1 text-xs text-muted-foreground hover:text-[var(--machine-dark)]"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(ROUTES.INSPECTION_NEW(project.id));
                    }}
                  >
                    <ClipboardCheck className="mr-1 h-3.5 w-3.5" />
                    Inspect
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 flex-1 text-xs text-muted-foreground hover:text-[var(--machine-dark)]"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(ROUTES.DOCUMENT_NEW);
                    }}
                  >
                    <FileText className="mr-1 h-3.5 w-3.5" />
                    Document
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 text-xs text-muted-foreground hover:text-[var(--machine-dark)]"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(ROUTES.PROJECT_DETAIL(project.id));
                    }}
                  >
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <Building2 className="h-16 w-16 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium text-muted-foreground">No projects yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Create your first project to start managing safety compliance
          </p>
          <Button
            className="mt-4 bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => navigate(ROUTES.PROJECT_NEW)}
          >
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        </div>
      )}
    </div>
  );
}
