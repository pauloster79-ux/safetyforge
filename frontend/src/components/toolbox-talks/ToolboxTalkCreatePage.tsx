import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import { ArrowLeft, Loader2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useProject } from '@/hooks/useProjects';
import { useCreateToolboxTalk } from '@/hooks/useToolboxTalks';
import { ROUTES } from '@/lib/constants';

export function ToolboxTalkCreatePage({ projectId: propProjectId }: { projectId?: string } = {}) {
  const navigate = useCanvasNavigate();
  const params = useParams<{ projectId: string }>();
  const projectId = propProjectId || params.projectId;
  const { data: project } = useProject(projectId);
  const createTalk = useCreateToolboxTalk(projectId || '');

  const [topic, setTopic] = useState('');
  const [targetAudience, setTargetAudience] = useState('all_workers');
  const [duration, setDuration] = useState('15');
  const [customPoints, setCustomPoints] = useState('');
  const [language, setLanguage] = useState<'en' | 'es' | 'both'>('both');

  const isValid = topic.trim().length > 0;

  const handleSubmit = async () => {
    if (!projectId || !isValid) return;
    try {
      const talk = await createTalk.mutateAsync({
        topic: topic.trim(),
        target_audience: targetAudience,
        duration_minutes: parseInt(duration, 10) || 15,
        custom_points: customPoints.trim(),
        language,
      });
      navigate(ROUTES.TOOLBOX_TALK_DELIVER(projectId, talk.id));
    } catch {
      // Error handled by mutation
    }
  };

  return (
    <div className="mx-auto max-w-lg">
      <div className="mb-6 flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() =>
            navigate(projectId ? ROUTES.PROJECT_DETAIL(projectId) : ROUTES.PROJECTS)
          }
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">New Toolbox Talk</h1>
          <p className="text-sm text-muted-foreground">
            {project?.name || 'Create a new safety talk'}
          </p>
        </div>
      </div>

      <Card>
        <CardContent className="space-y-5 pt-6">
          <div className="space-y-2">
            <Label htmlFor="topic">
              Topic <span className="text-[var(--fail)]">*</span>
            </Label>
            <Input
              id="topic"
              placeholder="e.g., Fall Protection Best Practices"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="h-12 text-base"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="target_audience">Target Audience</Label>
            <Select value={targetAudience} onValueChange={(v) => v && setTargetAudience(v)}>
              <SelectTrigger className="h-12 text-base">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all_workers">All Workers</SelectItem>
                <SelectItem value="new_hires">New Hires</SelectItem>
                <SelectItem value="supervisors">Supervisors</SelectItem>
                <SelectItem value="specific_trade">Specific Trade</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="duration">Duration (minutes)</Label>
            <Input
              id="duration"
              type="number"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className="h-12 text-base"
              min="5"
              max="60"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="language">Language</Label>
            <Select value={language} onValueChange={(v) => v && setLanguage(v as 'en' | 'es' | 'both')}>
              <SelectTrigger className="h-12 text-base">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="both">Both (English &amp; Spanish)</SelectItem>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="es">Spanish</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="custom_points">
              Custom Points <span className="text-xs text-muted-foreground">(optional)</span>
            </Label>
            <Textarea
              id="custom_points"
              placeholder="Any specific points you want covered?"
              value={customPoints}
              onChange={(e) => setCustomPoints(e.target.value)}
              rows={3}
              className="text-base"
            />
          </div>

          <Separator />

          <Button
            className="h-12 w-full bg-primary text-base hover:bg-[var(--machine-dark)]"
            disabled={!isValid || createTalk.isPending}
            onClick={handleSubmit}
          >
            {createTalk.isPending ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5" />
                Generate Talk
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
