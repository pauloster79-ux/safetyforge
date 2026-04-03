import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  AlertTriangle,
  MessageSquare,
  FileWarning,
  Siren,
  ArrowRight,
  FileText,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DOCUMENT_TYPES, ROUTES } from '@/lib/constants';

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  ShieldCheck,
  AlertTriangle,
  MessageSquare,
  FileWarning,
  Siren,
};

const COLOR_MAP: Record<string, { bg: string; icon: string; badge: string }> = {
  sssp: { bg: 'bg-[var(--info-bg)]', icon: 'text-[var(--info)]', badge: 'bg-[var(--info-bg)] text-[var(--info)]' },
  jha: { bg: 'bg-[var(--warn-bg)]', icon: 'text-[var(--warn)]', badge: 'bg-[var(--warn-bg)] text-[var(--warn)]' },
  toolbox_talk: { bg: 'bg-[var(--pass-bg)]', icon: 'text-[var(--pass)]', badge: 'bg-[var(--pass-bg)] text-[var(--pass)]' },
  incident_report: { bg: 'bg-[var(--fail-bg)]', icon: 'text-[var(--fail)]', badge: 'bg-[var(--fail-bg)] text-[var(--fail)]' },
  fall_protection: { bg: 'bg-purple-50', icon: 'text-purple-500', badge: 'bg-purple-100 text-purple-700' },
};

export function TemplatePickerPage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Document Templates</h1>
        <p className="text-sm text-muted-foreground">
          Choose a template to create a new safety document. Our AI will generate
          comprehensive, regulation-compliant content.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {DOCUMENT_TYPES.map((type) => {
          const IconComponent = ICON_MAP[type.icon] || FileText;
          const colors = COLOR_MAP[type.id] || { bg: 'bg-muted', icon: 'text-muted-foreground', badge: 'bg-muted text-[var(--concrete-600)]' };

          return (
            <Card
              key={type.id}
              className="group flex flex-col transition-shadow hover:shadow-lg"
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${colors.bg}`}>
                    <IconComponent className={`h-6 w-6 ${colors.icon}`} />
                  </div>
                  <Badge variant="secondary" className={colors.badge}>
                    {type.fields.length} fields
                  </Badge>
                </div>
                <CardTitle className="mt-3 text-lg">{type.name}</CardTitle>
                <CardDescription className="leading-relaxed">
                  {type.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="flex flex-1 flex-col justify-end">
                <div className="mb-4 space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">Required information:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {type.fields
                      .filter((f) => f.required)
                      .slice(0, 4)
                      .map((field) => (
                        <span
                          key={field.id}
                          className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                        >
                          {field.label}
                        </span>
                      ))}
                    {type.fields.filter((f) => f.required).length > 4 && (
                      <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                        +{type.fields.filter((f) => f.required).length - 4} more
                      </span>
                    )}
                  </div>
                </div>

                <Button
                  className="w-full bg-primary hover:bg-[var(--machine-dark)]"
                  onClick={() => navigate(`${ROUTES.DOCUMENT_NEW}?type=${type.id}`)}
                >
                  Use Template
                  <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
