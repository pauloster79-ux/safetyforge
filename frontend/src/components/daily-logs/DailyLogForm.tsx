import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import { ArrowLeft, Plus, Trash2, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useProject } from '@/hooks/useProjects';
import { useDailyLog, useCreateDailyLog, useUpdateDailyLog } from '@/hooks/useDailyLogs';
import { ROUTES } from '@/lib/constants';
import type { DailyLogMaterial, DailyLogDelay, DailyLogVisitor } from '@/lib/constants';

const emptyMaterial: DailyLogMaterial = { material: '', quantity: '', supplier: '', received_by: '', notes: '' };
const emptyDelay: DailyLogDelay = { delay_type: '', duration_hours: 0, description: '', impact: '' };
const emptyVisitor: DailyLogVisitor = { name: '', company: '', purpose: '', time_in: '', time_out: '' };

export function DailyLogForm({
  projectId: propProjectId,
  dailyLogId: propDailyLogId,
}: { projectId?: string; dailyLogId?: string } = {}) {
  const navigate = useCanvasNavigate();
  const params = useParams<{ projectId: string; dailyLogId: string }>();
  const projectId = propProjectId || params.projectId;
  const dailyLogId = propDailyLogId || params.dailyLogId;
  const isEdit = !!dailyLogId;
  const { data: project } = useProject(projectId);
  const { data: existingLog, isLoading: loadingLog } = useDailyLog(projectId, dailyLogId);
  const createMutation = useCreateDailyLog(projectId || '');
  const updateMutation = useUpdateDailyLog(projectId || '');

  const [logDate, setLogDate] = useState(new Date().toISOString().split('T')[0]);
  const [superintendentName, setSuperintendentName] = useState('');
  const [weatherConditions, setWeatherConditions] = useState('');
  const [tempHigh, setTempHigh] = useState('');
  const [tempLow, setTempLow] = useState('');
  const [wind, setWind] = useState('');
  const [precipitation, setPrecipitation] = useState('');
  const [workersOnSite, setWorkersOnSite] = useState(0);
  const [workPerformed, setWorkPerformed] = useState('');
  const [materials, setMaterials] = useState<DailyLogMaterial[]>([]);
  const [delays, setDelays] = useState<DailyLogDelay[]>([]);
  const [visitors, setVisitors] = useState<DailyLogVisitor[]>([]);
  const [safetyIncidents, setSafetyIncidents] = useState('');
  const [equipmentUsed, setEquipmentUsed] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (isEdit && existingLog) {
      setLogDate(existingLog.log_date);
      setSuperintendentName(existingLog.superintendent_name);
      setWeatherConditions(existingLog.weather.conditions);
      setTempHigh(existingLog.weather.temperature_high);
      setTempLow(existingLog.weather.temperature_low);
      setWind(existingLog.weather.wind);
      setPrecipitation(existingLog.weather.precipitation);
      setWorkersOnSite(existingLog.workers_on_site);
      setWorkPerformed(existingLog.work_performed);
      setMaterials((existingLog.materials_delivered || []).length > 0 ? [...existingLog.materials_delivered] : []);
      setDelays((existingLog.delays || []).length > 0 ? [...existingLog.delays] : []);
      setVisitors((existingLog.visitors || []).length > 0 ? [...existingLog.visitors] : []);
      setSafetyIncidents(existingLog.safety_incidents);
      setEquipmentUsed(existingLog.equipment_used);
      setNotes(existingLog.notes);
    }
  }, [isEdit, existingLog]);

  const handleSubmit = () => {
    if (!logDate || !superintendentName) {
      toast.error('Date and superintendent name are required');
      return;
    }

    const payload = {
      log_date: logDate,
      superintendent_name: superintendentName,
      weather: {
        conditions: weatherConditions,
        temperature_high: tempHigh,
        temperature_low: tempLow,
        wind,
        precipitation,
      },
      workers_on_site: workersOnSite,
      work_performed: workPerformed,
      materials_delivered: materials.filter((m) => m.material),
      delays: delays.filter((d) => d.description),
      visitors: visitors.filter((v) => v.name),
      safety_incidents: safetyIncidents,
      equipment_used: equipmentUsed,
      notes,
    };

    if (isEdit && dailyLogId) {
      updateMutation.mutate(
        { id: dailyLogId, ...payload },
        {
          onSuccess: () => {
            toast.success('Daily log updated');
            navigate(ROUTES.DAILY_LOG_DETAIL(projectId!, dailyLogId));
          },
        },
      );
    } else {
      createMutation.mutate(payload, {
        onSuccess: (data) => {
          toast.success('Daily log created');
          navigate(ROUTES.DAILY_LOG_DETAIL(projectId!, data.id));
        },
      });
    }
  };

  const updateMaterial = (idx: number, field: keyof DailyLogMaterial, value: string) => {
    setMaterials((prev) => prev.map((m, i) => (i === idx ? { ...m, [field]: value } : m)));
  };

  const updateDelay = (idx: number, field: keyof DailyLogDelay, value: string | number) => {
    setDelays((prev) => prev.map((d, i) => (i === idx ? { ...d, [field]: value } : d)));
  };

  const updateVisitor = (idx: number, field: keyof DailyLogVisitor, value: string) => {
    setVisitors((prev) => prev.map((v, i) => (i === idx ? { ...v, [field]: value } : v)));
  };

  if (isEdit && loadingLog) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-start gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="mt-1"
          onClick={() => navigate(projectId ? ROUTES.DAILY_LOGS(projectId) : ROUTES.PROJECTS)}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {isEdit ? 'Edit Daily Log' : 'New Daily Log'}
          </h1>
          {project && (
            <p className="mt-0.5 text-sm text-muted-foreground">{project.name}</p>
          )}
        </div>
      </div>

      {/* Basic Info */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="log_date">Log Date</Label>
              <Input
                id="log_date"
                type="date"
                value={logDate}
                onChange={(e) => setLogDate(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="superintendent">Superintendent</Label>
              <Input
                id="superintendent"
                placeholder="Superintendent name"
                value={superintendentName}
                onChange={(e) => setSuperintendentName(e.target.value)}
              />
            </div>
          </div>
          <div>
            <Label htmlFor="workers">Workers on Site</Label>
            <Input
              id="workers"
              type="number"
              min={0}
              value={workersOnSite}
              onChange={(e) => setWorkersOnSite(parseInt(e.target.value) || 0)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Weather */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Weather</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="weather_conditions">Conditions</Label>
              <Input
                id="weather_conditions"
                placeholder="e.g., Sunny, Partly Cloudy"
                value={weatherConditions}
                onChange={(e) => setWeatherConditions(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="precipitation">Precipitation</Label>
              <Input
                id="precipitation"
                placeholder="e.g., None, Light rain"
                value={precipitation}
                onChange={(e) => setPrecipitation(e.target.value)}
              />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <Label htmlFor="temp_high">Temperature High</Label>
              <Input
                id="temp_high"
                placeholder="e.g., 78F"
                value={tempHigh}
                onChange={(e) => setTempHigh(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="temp_low">Temperature Low</Label>
              <Input
                id="temp_low"
                placeholder="e.g., 55F"
                value={tempLow}
                onChange={(e) => setTempLow(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="wind">Wind</Label>
              <Input
                id="wind"
                placeholder="e.g., Light 5mph"
                value={wind}
                onChange={(e) => setWind(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Work Performed */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Work Performed</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder="Describe work performed today..."
            rows={4}
            value={workPerformed}
            onChange={(e) => setWorkPerformed(e.target.value)}
          />
        </CardContent>
      </Card>

      {/* Materials Delivered */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-base">Materials Delivered</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setMaterials((prev) => [...prev, { ...emptyMaterial }])}
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Add
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {materials.length === 0 && (
            <p className="text-sm text-muted-foreground">No materials delivered</p>
          )}
          {materials.map((m, idx) => (
            <div key={idx}>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <Label>Material</Label>
                  <Input
                    placeholder="Material name"
                    value={m.material}
                    onChange={(e) => updateMaterial(idx, 'material', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Quantity</Label>
                  <Input
                    placeholder="e.g., 200 pcs"
                    value={m.quantity}
                    onChange={(e) => updateMaterial(idx, 'quantity', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Supplier</Label>
                  <Input
                    placeholder="Supplier name"
                    value={m.supplier}
                    onChange={(e) => updateMaterial(idx, 'supplier', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Received By</Label>
                  <Input
                    placeholder="Name"
                    value={m.received_by}
                    onChange={(e) => updateMaterial(idx, 'received_by', e.target.value)}
                  />
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between">
                <Input
                  placeholder="Notes"
                  className="mr-2"
                  value={m.notes}
                  onChange={(e) => updateMaterial(idx, 'notes', e.target.value)}
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="shrink-0 text-destructive"
                  onClick={() => setMaterials((prev) => prev.filter((_, i) => i !== idx))}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
              {idx < materials.length - 1 && <Separator className="mt-3" />}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Delays */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-base">Delays</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDelays((prev) => [...prev, { ...emptyDelay }])}
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Add
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {delays.length === 0 && (
            <p className="text-sm text-muted-foreground">No delays</p>
          )}
          {delays.map((d, idx) => (
            <div key={idx}>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <Label>Type</Label>
                  <Input
                    placeholder="e.g., weather, equipment"
                    value={d.delay_type}
                    onChange={(e) => updateDelay(idx, 'delay_type', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Duration (hours)</Label>
                  <Input
                    type="number"
                    min={0}
                    step={0.5}
                    value={d.duration_hours}
                    onChange={(e) => updateDelay(idx, 'duration_hours', parseFloat(e.target.value) || 0)}
                  />
                </div>
                <div className="sm:col-span-2">
                  <Label>Description</Label>
                  <Input
                    placeholder="Describe the delay"
                    value={d.description}
                    onChange={(e) => updateDelay(idx, 'description', e.target.value)}
                  />
                </div>
                <div className="sm:col-span-2">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 mr-2">
                      <Label>Impact</Label>
                      <Input
                        placeholder="Impact on schedule"
                        value={d.impact}
                        onChange={(e) => updateDelay(idx, 'impact', e.target.value)}
                      />
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="mt-5 shrink-0 text-destructive"
                      onClick={() => setDelays((prev) => prev.filter((_, i) => i !== idx))}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
              {idx < delays.length - 1 && <Separator className="mt-3" />}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Visitors */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-base">Visitors</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setVisitors((prev) => [...prev, { ...emptyVisitor }])}
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Add
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {visitors.length === 0 && (
            <p className="text-sm text-muted-foreground">No visitors</p>
          )}
          {visitors.map((v, idx) => (
            <div key={idx}>
              <div className="grid gap-3 sm:grid-cols-3">
                <div>
                  <Label>Name</Label>
                  <Input
                    placeholder="Visitor name"
                    value={v.name}
                    onChange={(e) => updateVisitor(idx, 'name', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Company</Label>
                  <Input
                    placeholder="Company"
                    value={v.company}
                    onChange={(e) => updateVisitor(idx, 'company', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Purpose</Label>
                  <Input
                    placeholder="Purpose of visit"
                    value={v.purpose}
                    onChange={(e) => updateVisitor(idx, 'purpose', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Time In</Label>
                  <Input
                    placeholder="e.g., 10:00 AM"
                    value={v.time_in}
                    onChange={(e) => updateVisitor(idx, 'time_in', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Time Out</Label>
                  <Input
                    placeholder="e.g., 11:30 AM"
                    value={v.time_out}
                    onChange={(e) => updateVisitor(idx, 'time_out', e.target.value)}
                  />
                </div>
                <div className="flex items-end">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive"
                    onClick={() => setVisitors((prev) => prev.filter((_, i) => i !== idx))}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              {idx < visitors.length - 1 && <Separator className="mt-3" />}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Other fields */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Additional Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="safety_incidents">Safety Incidents</Label>
            <Textarea
              id="safety_incidents"
              placeholder="Describe any safety incidents..."
              rows={3}
              value={safetyIncidents}
              onChange={(e) => setSafetyIncidents(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="equipment_used">Equipment Used</Label>
            <Textarea
              id="equipment_used"
              placeholder="List equipment used today..."
              rows={2}
              value={equipmentUsed}
              onChange={(e) => setEquipmentUsed(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              placeholder="Additional notes..."
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <Button
          variant="outline"
          onClick={() => navigate(projectId ? ROUTES.DAILY_LOGS(projectId) : ROUTES.PROJECTS)}
        >
          Cancel
        </Button>
        <Button
          className="bg-primary hover:bg-[var(--machine-dark)]"
          onClick={handleSubmit}
          disabled={isPending}
        >
          {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isEdit ? 'Save Changes' : 'Create Daily Log'}
        </Button>
      </div>
    </div>
  );
}
