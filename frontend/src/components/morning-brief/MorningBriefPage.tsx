import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Loader2,
  Sun,
  Wind,
  Droplets,
  CloudRain,
  Thermometer,
  AlertTriangle,
  AlertCircle,
  Info,
  ExternalLink,
  MessageSquare,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useProject } from '@/hooks/useProjects';
import { useMorningBrief } from '@/hooks/useMorningBrief';
import { ROUTES } from '@/lib/constants';
import type { MorningBriefAlert } from '@/lib/constants';

function getRiskColor(score: number): string {
  if (score <= 3) return 'text-[var(--pass)]';
  if (score <= 5) return 'text-[var(--warn)]';
  if (score <= 7) return 'text-primary';
  return 'text-[var(--fail)]';
}

function getRiskBg(score: number): string {
  if (score <= 3) return 'bg-[var(--pass-bg)] border-[var(--pass)]';
  if (score <= 5) return 'bg-[var(--warn-bg)] border-[var(--warn)]';
  if (score <= 7) return 'bg-[var(--machine-wash)] border-primary';
  return 'bg-[var(--fail-bg)] border-[var(--fail)]';
}

function getRiskLabel(level: string): string {
  const labels: Record<string, string> = {
    low: 'Low Risk',
    moderate: 'Moderate Risk',
    elevated: 'Elevated Risk',
    high: 'High Risk',
    critical: 'Critical Risk',
  };
  return labels[level] || level;
}

const ALERT_SEVERITY_CONFIG: Record<MorningBriefAlert['severity'], { icon: typeof AlertTriangle; className: string; borderClass: string }> = {
  critical: {
    icon: AlertTriangle,
    className: 'text-[var(--fail)]',
    borderClass: 'border-[var(--fail)] bg-[var(--fail-bg)]',
  },
  warning: {
    icon: AlertCircle,
    className: 'text-[var(--warn)]',
    borderClass: 'border-[var(--warn)] bg-[var(--warn-bg)]',
  },
  info: {
    icon: Info,
    className: 'text-[var(--info)]',
    borderClass: 'border-[var(--info)] bg-[var(--info-bg)]',
  },
};

export function MorningBriefPage() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const { data: project } = useProject(projectId);
  const { data: brief, isLoading } = useMorningBrief(projectId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!brief) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <Sun className="h-12 w-12 text-muted-foreground" />
        <p className="mt-3 text-sm font-medium text-muted-foreground">No morning brief available</p>
        <p className="mt-1 text-xs text-muted-foreground">Morning briefs are generated daily</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate(ROUTES.PROJECT_DETAIL(projectId || ''))}
        >
          Back to Project
        </Button>
      </div>
    );
  }

  // Sort alerts: critical first, then warning, then info
  const sortedAlerts = [...brief.alerts].sort((a, b) => {
    const order: Record<string, number> = { critical: 0, warning: 1, info: 2 };
    return (order[a.severity] ?? 3) - (order[b.severity] ?? 3);
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(ROUTES.PROJECT_DETAIL(projectId || ''))}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Morning Safety Brief</h1>
          <p className="text-sm text-muted-foreground">
            {project?.name || 'Project'} &mdash; {brief.date}
          </p>
        </div>
      </div>

      {/* Risk Score */}
      <Card className={getRiskBg(brief.risk_score)}>
        <CardContent className="flex items-center gap-6 py-6">
          <div className="text-center">
            <p className={`text-5xl font-bold ${getRiskColor(brief.risk_score)}`}>
              {brief.risk_score.toFixed(1)}
            </p>
            <p className="mt-1 text-xs font-medium text-muted-foreground">out of 10</p>
          </div>
          <Separator orientation="vertical" className="h-16" />
          <div>
            <p className={`text-lg font-semibold ${getRiskColor(brief.risk_score)}`}>
              {getRiskLabel(brief.risk_level)}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">{brief.summary}</p>
          </div>
        </CardContent>
      </Card>

      {/* Weather */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sun className="h-5 w-5 text-[var(--warn)]" />
            Weather Conditions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="flex items-center gap-2">
              <Thermometer className="h-5 w-5 text-[var(--fail)]" />
              <div>
                <p className="text-lg font-bold text-foreground">{brief.weather.temperature}°F</p>
                <p className="text-xs text-muted-foreground">{brief.weather.condition}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Wind className="h-5 w-5 text-[var(--info)]" />
              <div>
                <p className="text-lg font-bold text-foreground">{brief.weather.wind_speed} mph</p>
                <p className="text-xs text-muted-foreground">Wind</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Droplets className="h-5 w-5 text-cyan-400" />
              <div>
                <p className="text-lg font-bold text-foreground">{brief.weather.humidity}%</p>
                <p className="text-xs text-muted-foreground">Humidity</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <CloudRain className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-lg font-bold text-foreground">{brief.weather.precipitation_chance}%</p>
                <p className="text-xs text-muted-foreground">Rain Chance</p>
              </div>
            </div>
          </div>
          {brief.weather.alerts.length > 0 && (
            <div className="mt-4 space-y-2">
              {brief.weather.alerts.map((alert, i) => (
                <div key={i} className="flex items-center gap-2 rounded-md bg-[var(--warn-bg)] px-3 py-2">
                  <AlertTriangle className="h-4 w-4 shrink-0 text-[var(--warn)]" />
                  <p className="text-sm font-medium text-[var(--warn)]">{alert}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Alerts */}
      <div>
        <h2 className="mb-3 text-lg font-semibold text-foreground">
          Alerts ({sortedAlerts.length})
        </h2>
        <div className="space-y-3">
          {sortedAlerts.map((alert, i) => {
            const config = ALERT_SEVERITY_CONFIG[alert.severity];
            const Icon = config.icon;

            return (
              <Card key={i} className={config.borderClass}>
                <CardContent className="py-4">
                  <div className="flex items-start gap-3">
                    <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${config.className}`} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-foreground">{alert.title}</p>
                        <Badge variant="outline" className="text-xs capitalize">
                          {alert.type.replace('_', ' ')}
                        </Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{alert.description}</p>
                      {(alert.action_url || alert.action_label) && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="mt-2"
                          onClick={() => {
                            if (alert.action_url) {
                              navigate(alert.action_url);
                            }
                          }}
                        >
                          {alert.action_label || 'View'}
                          <ExternalLink className="ml-1 h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Recommended Toolbox Talk */}
      <Card className="border-[var(--info)] bg-[var(--info-bg)]">
        <CardContent className="flex items-center justify-between py-4">
          <div className="flex items-center gap-3">
            <MessageSquare className="h-5 w-5 text-[var(--info)]" />
            <div>
              <p className="text-sm font-medium text-foreground">Recommended Toolbox Talk</p>
              <p className="text-sm text-[var(--info)]">{brief.recommended_toolbox_talk_topic}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-[var(--info)] text-[var(--info)] hover:bg-[var(--info-bg)]"
            onClick={() => navigate(ROUTES.TOOLBOX_TALK_NEW(projectId || ''))}
          >
            Generate Talk
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
