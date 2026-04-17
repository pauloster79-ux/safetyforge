import { useState } from 'react';
import { useShell } from '@/hooks/useShell';
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
import type { Project } from '@/lib/constants';
import { ComplianceRing } from './ComplianceRing';

function StateBadge({ state }: { state: Project['state'] }) {
  const config: Record<string, { label: string; className: string }> = {
    lead: { label: 'Lead', className: 'bg-blue-50 text-blue-700 hover:bg-blue-50' },
    quoted: { label: 'Quoted', className: 'bg-purple-50 text-purple-700 hover:bg-purple-50' },
    active: { label: 'Active', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    completed: { label: 'Completed', className: 'bg-muted text-muted-foreground hover:bg-muted' },
    closed: { label: 'Closed', className: 'bg-muted text-muted-foreground hover:bg-muted' },
    lost: { label: 'Lost', className: 'bg-red-50 text-red-700 hover:bg-red-50' },
  };
  const { label, className } = config[state] || { label: state, className: 'bg-muted text-muted-foreground hover:bg-muted' };
  return <Badge className={className}>{label}</Badge>;
}

export function ProjectListPage() {
  const shell = useShell();
  const [statusFilter, setStatusFilter] = useState<string>('All');

  const { data: projects, isLoading } = useProjects(
    !statusFilter.startsWith('All') ? { state: statusFilter } : undefined
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
          onClick={() => shell.openCanvas({ component: 'ProjectCreatePage', props: {}, label: 'New Project' })}
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
            <SelectItem value="lead">Lead</SelectItem>
            <SelectItem value="quoted">Quoted</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="on_hold">On Hold</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
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
              onClick={() => shell.openCanvas({ component: 'ProjectDetailPage', props: { projectId: project.id }, label: project.name })}
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
                  <StateBadge state={project.state} />
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
                      shell.openCanvas({ component: 'InspectionCreatePage', props: { projectId: project.id }, label: 'New Inspection' });
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
                      shell.openCanvas({ component: 'DocumentCreatePage', props: {}, label: 'New Document' });
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
                      shell.openCanvas({ component: 'ProjectDetailPage', props: { projectId: project.id }, label: project.name });
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
            onClick={() => shell.openCanvas({ component: 'ProjectCreatePage', props: {}, label: 'New Project' })}
          >
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        </div>
      )}
    </div>
  );
}
