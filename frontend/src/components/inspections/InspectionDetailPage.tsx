import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  MinusCircle,
  Cloud,
  Thermometer,
  Users,
  Calendar,
  Loader2,
  Printer,
  Download,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useProject } from '@/hooks/useProjects';
import { useInspection } from '@/hooks/useInspections';
import { ROUTES, INSPECTION_TYPES } from '@/lib/constants';
import type { Inspection, InspectionItem } from '@/lib/constants';
import { downloadPdf } from '@/lib/pdf';
import { format } from 'date-fns';

function OverallStatusBadge({ status }: { status: Inspection['overall_status'] }) {
  const config = {
    pass: { label: 'PASS', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]', icon: CheckCircle2 },
    fail: { label: 'FAIL', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]', icon: XCircle },
    partial: { label: 'PARTIAL', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]', icon: MinusCircle },
  };
  const { label, className, icon: Icon } = config[status];
  return (
    <Badge className={`${className} gap-1 px-3 py-1 text-sm`}>
      <Icon className="h-4 w-4" />
      {label}
    </Badge>
  );
}

function ItemStatusIcon({ status }: { status: InspectionItem['status'] }) {
  switch (status) {
    case 'pass':
      return <CheckCircle2 className="h-5 w-5 shrink-0 text-[var(--pass)]" />;
    case 'fail':
      return <XCircle className="h-5 w-5 shrink-0 text-[var(--fail)]" />;
    case 'na':
      return <MinusCircle className="h-5 w-5 shrink-0 text-muted-foreground" />;
  }
}

export function InspectionDetailPage() {
  const navigate = useNavigate();
  const { projectId, inspectionId } = useParams<{ projectId: string; inspectionId: string }>();
  const { data: project } = useProject(projectId);
  const { data: inspection, isLoading } = useInspection(projectId, inspectionId);

  const categories = useMemo(() => {
    if (!inspection) return [];
    const cats: { name: string; items: InspectionItem[] }[] = [];
    for (const item of inspection.items) {
      const existing = cats.find((c) => c.name === item.category);
      if (existing) {
        existing.items.push(item);
      } else {
        cats.push({ name: item.category, items: [item] });
      }
    }
    return cats;
  }, [inspection]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!inspection) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <p className="text-sm text-muted-foreground">Inspection not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate(projectId ? ROUTES.PROJECT_DETAIL(projectId) : ROUTES.PROJECTS)}
        >
          Back to Project
        </Button>
      </div>
    );
  }

  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    try {
      await downloadPdf(
        `/me/inspections/${inspectionId}/pdf`,
        `Inspection-${inspection.inspection_type}-${inspection.inspection_date}.pdf`,
      );
    } catch {
      // downloadPdf throws on failure; toast handled at caller if desired
    } finally {
      setIsDownloading(false);
    }
  };

  const typeName = INSPECTION_TYPES.find((t) => t.id === inspection.inspection_type)?.name || inspection.inspection_type;
  const passCount = inspection.items.filter((i) => i.status === 'pass').length;
  const failCount = inspection.items.filter((i) => i.status === 'fail').length;
  const naCount = inspection.items.filter((i) => i.status === 'na').length;

  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="mt-1"
            onClick={() => navigate(projectId ? ROUTES.PROJECT_DETAIL(projectId) : ROUTES.PROJECTS)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{typeName}</h1>
            {project && (
              <p className="mt-0.5 text-sm text-muted-foreground">{project.name}</p>
            )}
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <OverallStatusBadge status={inspection.overall_status} />
              <span className="flex items-center gap-1 text-sm text-muted-foreground">
                <Calendar className="h-3.5 w-3.5" />
                {format(new Date(inspection.inspection_date), 'MMMM d, yyyy')}
              </span>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => window.print()}>
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownloadPdf} disabled={isDownloading}>
            {isDownloading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
            Download PDF
          </Button>
        </div>
      </div>

      {/* Meta info */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-3 py-3">
            <Users className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Inspector</p>
              <p className="text-sm font-medium text-[var(--concrete-600)]">{inspection.inspector_name}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-3">
            <Cloud className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Weather</p>
              <p className="text-sm font-medium text-[var(--concrete-600)]">{inspection.weather_conditions || '-'}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-3">
            <Thermometer className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Temperature</p>
              <p className="text-sm font-medium text-[var(--concrete-600)]">{inspection.temperature || '-'}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-3">
            <Users className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Workers on Site</p>
              <p className="text-sm font-medium text-[var(--concrete-600)]">{inspection.workers_on_site}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="border-[var(--pass)] bg-[var(--pass-bg)]/50">
          <CardContent className="flex flex-col items-center py-4">
            <CheckCircle2 className="h-6 w-6 text-[var(--pass)]" />
            <p className="mt-1 text-xl font-bold text-[var(--pass)]">{passCount}</p>
            <p className="text-xs text-[var(--pass)]">Passed</p>
          </CardContent>
        </Card>
        <Card className="border-[var(--fail)] bg-[var(--fail-bg)]/50">
          <CardContent className="flex flex-col items-center py-4">
            <XCircle className="h-6 w-6 text-[var(--fail)]" />
            <p className="mt-1 text-xl font-bold text-[var(--fail)]">{failCount}</p>
            <p className="text-xs text-[var(--fail)]">Failed</p>
          </CardContent>
        </Card>
        <Card className="border-border bg-muted/50">
          <CardContent className="flex flex-col items-center py-4">
            <MinusCircle className="h-6 w-6 text-muted-foreground" />
            <p className="mt-1 text-xl font-bold text-muted-foreground">{naCount}</p>
            <p className="text-xs text-muted-foreground">N/A</p>
          </CardContent>
        </Card>
      </div>

      {/* Checklist items by category */}
      {categories.map((cat) => (
        <Card key={cat.name}>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              {cat.name}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {cat.items.map((item, idx) => (
              <div key={item.item_id}>
                <div className="flex items-start gap-3 py-2">
                  <ItemStatusIcon status={item.status} />
                  <div className="flex-1">
                    <p className="text-sm text-[var(--concrete-600)]">{item.description}</p>
                    {item.notes && (
                      <p className="mt-1 rounded-md bg-[var(--fail-bg)] p-2 text-xs text-[var(--fail)]">
                        {item.notes}
                      </p>
                    )}
                  </div>
                </div>
                {idx < cat.items.length - 1 && <Separator />}
              </div>
            ))}
          </CardContent>
        </Card>
      ))}

      {/* Notes & corrective actions */}
      {(inspection.overall_notes || inspection.corrective_actions_needed) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Notes & Corrective Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {inspection.overall_notes && (
              <div>
                <p className="text-xs font-semibold uppercase text-muted-foreground">Overall Notes</p>
                <p className="mt-1 text-sm text-[var(--concrete-600)]">{inspection.overall_notes}</p>
              </div>
            )}
            {inspection.corrective_actions_needed && (
              <div>
                <p className="text-xs font-semibold uppercase text-[var(--fail)]">Corrective Actions Required</p>
                <p className="mt-1 text-sm text-[var(--concrete-600)]">{inspection.corrective_actions_needed}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
