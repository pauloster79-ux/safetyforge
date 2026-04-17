import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useCreateProject } from '@/hooks/useProjects';
import { ROUTES, PROJECT_TYPES, TRADE_TYPES } from '@/lib/constants';

export function ProjectCreatePage() {
  const navigate = useCanvasNavigate();
  const createProject = useCreateProject();

  const [form, setForm] = useState({
    name: '',
    address: '',
    client_name: '',
    project_type: '',
    trade_types: [] as string[],
    start_date: '',
    end_date: '',
    estimated_workers: '',
    description: '',
    special_hazards: '',
    nearest_hospital: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
  });

  const handleChange = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const toggleTrade = (trade: string) => {
    setForm((prev) => ({
      ...prev,
      trade_types: prev.trade_types.includes(trade)
        ? prev.trade_types.filter((t) => t !== trade)
        : [...prev.trade_types, trade],
    }));
  };

  const isValid = form.name.trim() && form.address.trim();

  const handleSubmit = async () => {
    if (!isValid) return;
    try {
      const project = await createProject.mutateAsync({
        name: form.name,
        address: form.address,
        client_name: form.client_name,
        project_type: form.project_type,
        trade_types: form.trade_types,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        estimated_workers: form.estimated_workers ? parseInt(form.estimated_workers, 10) : 0,
        description: form.description,
        special_hazards: form.special_hazards,
        nearest_hospital: form.nearest_hospital,
        emergency_contact_name: form.emergency_contact_name,
        emergency_contact_phone: form.emergency_contact_phone,
      });
      navigate(ROUTES.PROJECT_DETAIL(project.id));
    } catch {
      // Error handled by mutation
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6 flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(ROUTES.PROJECTS)}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">New Project</h1>
          <p className="text-sm text-muted-foreground">Set up a new construction project</p>
        </div>
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Project Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">
                Project Name <span className="text-[var(--fail)]">*</span>
              </Label>
              <Input
                id="name"
                placeholder="e.g., Downtown Office Tower"
                value={form.name}
                onChange={(e) => handleChange('name', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="address">
                Project Address <span className="text-[var(--fail)]">*</span>
              </Label>
              <Input
                id="address"
                placeholder="123 Main St, City, State ZIP"
                value={form.address}
                onChange={(e) => handleChange('address', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="client_name">Client / Owner</Label>
              <Input
                id="client_name"
                placeholder="ABC Development Corp"
                value={form.client_name}
                onChange={(e) => handleChange('client_name', e.target.value)}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="project_type">Project Type</Label>
                <Select
                  value={form.project_type}
                  onValueChange={(v) => handleChange('project_type', v ?? '')}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {PROJECT_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="estimated_workers">Estimated Workers</Label>
                <Input
                  id="estimated_workers"
                  type="number"
                  placeholder="25"
                  value={form.estimated_workers}
                  onChange={(e) => handleChange('estimated_workers', e.target.value)}
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={form.start_date}
                  onChange={(e) => handleChange('start_date', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end_date">End Date</Label>
                <Input
                  id="end_date"
                  type="date"
                  value={form.end_date}
                  onChange={(e) => handleChange('end_date', e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Trade Types</Label>
              <div className="flex flex-wrap gap-2">
                {TRADE_TYPES.map((trade) => (
                  <button
                    key={trade.value}
                    type="button"
                    onClick={() => toggleTrade(trade.value)}
                    className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                      form.trade_types.includes(trade.value)
                        ? 'border-primary bg-[var(--machine-wash)] text-primary'
                        : 'border-border bg-white text-muted-foreground hover:border-border'
                    }`}
                  >
                    {trade.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Brief project description..."
                value={form.description}
                onChange={(e) => handleChange('description', e.target.value)}
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Safety & Emergency</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="special_hazards">Special Hazards / Considerations</Label>
              <Textarea
                id="special_hazards"
                placeholder="e.g., Confined spaces, working at height above 30ft, proximity to live traffic"
                value={form.special_hazards}
                onChange={(e) => handleChange('special_hazards', e.target.value)}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="nearest_hospital">Nearest Hospital</Label>
              <Input
                id="nearest_hospital"
                placeholder="Hospital name, address, distance"
                value={form.nearest_hospital}
                onChange={(e) => handleChange('nearest_hospital', e.target.value)}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="emergency_contact_name">Emergency Contact Name</Label>
                <Input
                  id="emergency_contact_name"
                  placeholder="Site Safety Officer"
                  value={form.emergency_contact_name}
                  onChange={(e) => handleChange('emergency_contact_name', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="emergency_contact_phone">Emergency Contact Phone</Label>
                <Input
                  id="emergency_contact_phone"
                  placeholder="(555) 123-4567"
                  value={form.emergency_contact_phone}
                  onChange={(e) => handleChange('emergency_contact_phone', e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Separator />

        <div className="flex justify-end gap-3 pb-8">
          <Button variant="outline" onClick={() => navigate(ROUTES.PROJECTS)}>
            Cancel
          </Button>
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            disabled={!isValid || createProject.isPending}
            onClick={handleSubmit}
          >
            {createProject.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Create Project
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
