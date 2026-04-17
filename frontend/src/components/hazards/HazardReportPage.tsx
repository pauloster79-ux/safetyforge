import { useState, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import {
  ArrowLeft,
  Camera,
  Upload,
  Loader2,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Info,
  Save,
  MapPin,
  Image as ImageIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { useProject } from '@/hooks/useProjects';
import { useAnalyzePhoto, useCreateHazardReport, useHazardReport, useUpdateHazardReport } from '@/hooks/useHazardReports';
import { ROUTES } from '@/lib/constants';
import type { IdentifiedHazard } from '@/lib/constants';

const SEVERITY_CONFIG: Record<IdentifiedHazard['severity'], { label: string; className: string; icon: typeof ShieldAlert }> = {
  imminent_danger: { label: 'Imminent Danger', className: 'bg-[var(--fail)] text-white hover:bg-[var(--fail)]', icon: ShieldAlert },
  high: { label: 'High', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]', icon: ShieldAlert },
  medium: { label: 'Medium', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]', icon: AlertTriangle },
  low: { label: 'Low', className: 'bg-[var(--info-bg)] text-[var(--info)] hover:bg-[var(--info-bg)]', icon: Info },
};

function SeverityBadge({ severity }: { severity: IdentifiedHazard['severity'] }) {
  const config = SEVERITY_CONFIG[severity];
  return <Badge className={config.className}>{config.label}</Badge>;
}

export function HazardReportPage({ projectId: propProjectId, id: propId }: { projectId?: string; id?: string } = {}) {
  const navigate = useCanvasNavigate();
  const params = useParams<{ projectId: string; id?: string }>();
  const projectId = propProjectId || params.projectId;
  const id = propId || params.id;
  const { data: project } = useProject(projectId);
  const { data: existingReport } = useHazardReport(projectId, id);
  const analyzePhoto = useAnalyzePhoto();
  const createReport = useCreateHazardReport(projectId || '');
  const updateReport = useUpdateHazardReport(projectId || '');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [photoBase64, setPhotoBase64] = useState<string | null>(null);
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [analysisResult, setAnalysisResult] = useState<{
    identified_hazards: IdentifiedHazard[];
    hazard_count: number;
    highest_severity: string | null;
    scene_description: string;
    positive_observations: string[];
    summary: string;
  } | null>(null);
  const [saved, setSaved] = useState(false);

  // If viewing an existing report
  const isViewMode = !!id && !!existingReport;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      setPhotoPreview(result);
      setPhotoBase64(result.split(',')[1]);
      setAnalysisResult(null);
      setSaved(false);
    };
    reader.readAsDataURL(file);
  };

  const handleAnalyze = async () => {
    if (!photoBase64) return;
    const result = await analyzePhoto.mutateAsync({
      photo_base64: photoBase64,
      description,
      location,
    });
    setAnalysisResult(result);
  };

  const handleSave = async () => {
    if (!analysisResult || !projectId) return;
    await createReport.mutateAsync({
      photo_url: photoPreview || '',
      description: description || analysisResult.scene_description,
      location,
      identified_hazards: analysisResult.identified_hazards,
      hazard_count: analysisResult.hazard_count,
      highest_severity: analysisResult.highest_severity,
      ai_analysis: {
        scene_description: analysisResult.scene_description,
        positive_observations: analysisResult.positive_observations,
      },
    });
    setSaved(true);
  };

  const handleUpdateStatus = async (status: 'in_progress' | 'corrected' | 'closed', correctiveAction?: string) => {
    if (!existingReport || !projectId) return;
    await updateReport.mutateAsync({
      id: existingReport.id,
      status,
      corrective_action_taken: correctiveAction,
    });
  };

  const displayHazards = isViewMode
    ? (existingReport.identified_hazards || [])
    : analysisResult?.identified_hazards ?? [];

  const displaySummary = isViewMode
    ? (existingReport.ai_analysis as Record<string, unknown>)?.scene_description as string | undefined
    : analysisResult?.scene_description;

  const displayPositives = isViewMode
    ? ((existingReport.ai_analysis as Record<string, unknown>)?.positive_observations as string[] | undefined) ?? []
    : analysisResult?.positive_observations ?? [];

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
          <h1 className="text-2xl font-bold text-foreground">
            {isViewMode ? 'Hazard Report' : 'New Photo Hazard Assessment'}
          </h1>
          <p className="text-sm text-muted-foreground">{project?.name || 'Project'}</p>
        </div>
      </div>

      {/* Existing report status */}
      {isViewMode && (
        <Card>
          <CardContent className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <Badge className={
                existingReport.status === 'open' ? 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' :
                existingReport.status === 'in_progress' ? 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' :
                existingReport.status === 'corrected' ? 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' :
                'bg-muted text-[var(--concrete-600)] hover:bg-muted'
              }>
                {existingReport.status.replace('_', ' ').toUpperCase()}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {existingReport.location} - {existingReport.hazard_count} hazard{existingReport.hazard_count !== 1 ? 's' : ''}
              </span>
            </div>
            {existingReport.status === 'open' && (
              <Button size="sm" variant="outline" onClick={() => handleUpdateStatus('in_progress')}>
                Mark In Progress
              </Button>
            )}
            {existingReport.status === 'in_progress' && (
              <Button size="sm" className="bg-[var(--pass)] hover:bg-[var(--pass)]" onClick={() => handleUpdateStatus('corrected', 'Corrective actions completed')}>
                Mark Corrected
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Photo capture section — only for new reports */}
      {!isViewMode && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Capture Photo</CardTitle>
            <CardDescription>Take a photo of the work area or upload an existing one</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={handleFileChange}
            />

            {photoPreview ? (
              <div className="space-y-3">
                <div className="relative overflow-hidden rounded-lg border">
                  <img
                    src={photoPreview}
                    alt="Photo preview"
                    className="h-64 w-full object-cover"
                  />
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Camera className="mr-2 h-4 w-4" />
                  Retake Photo
                </Button>
              </div>
            ) : (
              <div className="flex gap-3">
                <Button
                  className="bg-primary hover:bg-[var(--machine-dark)]"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Camera className="mr-2 h-4 w-4" />
                  Take Photo
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    // Remove capture attribute for file picker
                    if (fileInputRef.current) {
                      fileInputRef.current.removeAttribute('capture');
                      fileInputRef.current.click();
                      fileInputRef.current.setAttribute('capture', 'environment');
                    }
                  }}
                >
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Image
                </Button>
              </div>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Description (optional)</Label>
                <Input
                  placeholder="e.g., Scaffold on east side of building"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Location</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    className="pl-9"
                    placeholder="e.g., Building A, East Elevation"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <Separator />

            <Button
              className="w-full bg-primary hover:bg-[var(--machine-dark)]"
              disabled={!photoBase64 || analyzePhoto.isPending}
              onClick={handleAnalyze}
            >
              {analyzePhoto.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing for Hazards...
                </>
              ) : (
                <>
                  <ShieldAlert className="mr-2 h-4 w-4" />
                  Analyze for Hazards
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Analysis Results */}
      {(displayHazards.length > 0 || displaySummary) && (
        <>
          {/* Summary */}
          {displaySummary && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Scene Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-[var(--concrete-600)]">{displaySummary}</p>
                {displayPositives.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-[var(--pass)]">Positive Observations:</p>
                    <ul className="mt-1 list-disc space-y-1 pl-5">
                      {displayPositives.map((obs, i) => (
                        <li key={i} className="text-sm text-[var(--pass)]">{obs}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Hazard Cards */}
          <div>
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Identified Hazards ({displayHazards.length})
            </h2>
            <div className="space-y-3">
              {displayHazards.map((hazard) => (
                <Card key={hazard.hazard_id} className={
                  hazard.severity === 'imminent_danger' ? 'border-[var(--fail)] bg-[var(--fail-bg)]' :
                  hazard.severity === 'high' ? 'border-[var(--fail)]' :
                  hazard.severity === 'medium' ? 'border-[var(--warn)]' :
                  'border-[var(--info)]'
                }>
                  <CardContent className="py-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1 space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <SeverityBadge severity={hazard.severity} />
                          <Badge variant="outline" className="text-xs">
                            {hazard.osha_standard}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {hazard.category}
                          </Badge>
                        </div>
                        <p className="text-sm text-[var(--concrete-600)]">{hazard.description}</p>
                        <div className="rounded-md bg-muted p-3">
                          <p className="text-xs font-medium text-muted-foreground">Recommended Action</p>
                          <p className="mt-1 text-sm text-[var(--concrete-600)]">{hazard.recommended_action}</p>
                        </div>
                        {hazard.location_in_image && (
                          <p className="flex items-center gap-1 text-xs text-muted-foreground">
                            <ImageIcon className="h-3 w-3" />
                            {hazard.location_in_image}
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* AI Summary */}
          {!isViewMode && analysisResult && (
            <Card>
              <CardContent className="py-4">
                <p className="text-sm font-medium text-[var(--concrete-600)]">AI Summary</p>
                <p className="mt-1 text-sm text-muted-foreground">{analysisResult.summary}</p>
              </CardContent>
            </Card>
          )}

          {/* Corrective action for existing reports */}
          {isViewMode && existingReport.corrective_action_taken && (
            <Card className="border-[var(--pass)] bg-[var(--pass-bg)]">
              <CardContent className="py-4">
                <div className="flex items-start gap-2">
                  <ShieldCheck className="mt-0.5 h-5 w-5 text-[var(--pass)]" />
                  <div>
                    <p className="text-sm font-medium text-[var(--pass)]">Corrective Action Taken</p>
                    <p className="mt-1 text-sm text-[var(--pass)]">{existingReport.corrective_action_taken}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Save button for new reports */}
          {!isViewMode && analysisResult && !saved && (
            <Button
              className="w-full bg-primary hover:bg-[var(--machine-dark)]"
              disabled={createReport.isPending}
              onClick={handleSave}
            >
              {createReport.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save as Report
            </Button>
          )}

          {saved && (
            <Card className="border-[var(--pass)] bg-[var(--pass-bg)]">
              <CardContent className="flex items-center justify-between py-4">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-[var(--pass)]" />
                  <p className="text-sm font-medium text-[var(--pass)]">Report saved successfully</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(ROUTES.PROJECT_DETAIL(projectId || ''))}
                >
                  Back to Project
                </Button>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
