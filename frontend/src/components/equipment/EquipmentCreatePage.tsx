import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
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
import { Separator } from '@/components/ui/separator';
import { useCreateEquipment } from '@/hooks/useEquipment';
import { useProjects } from '@/hooks/useProjects';
import { ROUTES, EQUIPMENT_TYPES, CERTIFICATION_TYPES } from '@/lib/constants';

export function EquipmentCreatePage() {
  const navigate = useCanvasNavigate();
  const createEquipment = useCreateEquipment();
  const { data: projects } = useProjects();

  const [form, setForm] = useState({
    name: '',
    equipment_type: '',
    make: '',
    model: '',
    year: '',
    serial_number: '',
    vin: '',
    license_plate: '',
    current_project_id: '',
    inspection_frequency: 'Monthly',
    dot_number: '',
    required_certifications: [] as string[],
    notes: '',
  });

  const handleChange = (field: string, value: string | null) => {
    setForm(prev => ({ ...prev, [field]: value ?? '' }));
  };

  const toggleCert = (certId: string) => {
    setForm(prev => ({
      ...prev,
      required_certifications: prev.required_certifications.includes(certId)
        ? prev.required_certifications.filter(c => c !== certId)
        : [...prev.required_certifications, certId],
    }));
  };

  const handleSubmit = () => {
    createEquipment.mutate({
      ...form,
      year: form.year ? parseInt(form.year, 10) : null,
      current_project_id: form.current_project_id || null,
    }, {
      onSuccess: (data) => {
        navigate(ROUTES.EQUIPMENT_DETAIL(data.id));
      },
    });
  };

  const isValid = form.name.trim() && form.equipment_type;

  return (
    <div className="mx-auto max-w-lg">
      <div className="mb-6 flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate(ROUTES.EQUIPMENT)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Add Equipment</h1>
          <p className="text-sm text-muted-foreground">Register a new piece of equipment</p>
        </div>
      </div>

      <Card>
        <CardContent className="space-y-4 pt-6">
          <div className="space-y-2">
            <Label>Equipment Name <span className="text-[var(--fail)]">*</span></Label>
            <Input
              value={form.name}
              onChange={e => handleChange('name', e.target.value)}
              placeholder="e.g., Tower Crane #1, Ford F-350 Work Truck"
              className="h-12 text-base"
            />
          </div>

          <div className="space-y-2">
            <Label>Equipment Type <span className="text-[var(--fail)]">*</span></Label>
            <Select value={form.equipment_type} onValueChange={v => handleChange('equipment_type', v)}>
              <SelectTrigger className="h-12"><SelectValue placeholder="Select type" /></SelectTrigger>
              <SelectContent>
                {EQUIPMENT_TYPES.map(t => (
                  <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Make</Label>
              <Input value={form.make} onChange={e => handleChange('make', e.target.value)} placeholder="e.g., Liebherr" />
            </div>
            <div className="space-y-2">
              <Label>Model</Label>
              <Input value={form.model} onChange={e => handleChange('model', e.target.value)} placeholder="e.g., 172 EC-B 8" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Year</Label>
              <Input type="number" value={form.year} onChange={e => handleChange('year', e.target.value)} placeholder="2024" />
            </div>
            <div className="space-y-2">
              <Label>Serial Number</Label>
              <Input value={form.serial_number} onChange={e => handleChange('serial_number', e.target.value)} placeholder="Serial #" />
            </div>
          </div>

          <Separator />

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>VIN</Label>
              <Input value={form.vin} onChange={e => handleChange('vin', e.target.value)} placeholder="Vehicle VIN" />
            </div>
            <div className="space-y-2">
              <Label>License Plate</Label>
              <Input value={form.license_plate} onChange={e => handleChange('license_plate', e.target.value)} placeholder="TX-ABC-1234" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>DOT Number</Label>
              <Input value={form.dot_number} onChange={e => handleChange('dot_number', e.target.value)} placeholder="DOT-XXXXXXX" />
            </div>
            <div className="space-y-2">
              <Label>Inspection Frequency</Label>
              <Select value={form.inspection_frequency} onValueChange={v => handleChange('inspection_frequency', v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Daily">Daily</SelectItem>
                  <SelectItem value="Weekly">Weekly</SelectItem>
                  <SelectItem value="Monthly">Monthly</SelectItem>
                  <SelectItem value="Quarterly">Quarterly</SelectItem>
                  <SelectItem value="Annually">Annually</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Assigned Project</Label>
            <Select value={form.current_project_id} onValueChange={v => handleChange('current_project_id', v)}>
              <SelectTrigger><SelectValue placeholder="Not assigned" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="">Not assigned</SelectItem>
                {projects?.map(p => (
                  <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Separator />

          <div className="space-y-2">
            <Label>Required Operator Certifications</Label>
            <div className="grid grid-cols-2 gap-1.5">
              {CERTIFICATION_TYPES.filter(c =>
                ['forklift_operator', 'crane_operator_nccco', 'aerial_lift', 'scaffold_competent', 'rigging_signal'].includes(c.id)
              ).map(cert => (
                <label key={cert.id} className="flex items-center gap-2 rounded-md border border-border p-2 text-sm cursor-pointer hover:bg-muted/50">
                  <input
                    type="checkbox"
                    checked={form.required_certifications.includes(cert.id)}
                    onChange={() => toggleCert(cert.id)}
                    className="h-4 w-4 rounded"
                  />
                  {cert.name}
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Notes</Label>
            <Textarea
              value={form.notes}
              onChange={e => handleChange('notes', e.target.value)}
              placeholder="Additional notes..."
              rows={3}
            />
          </div>

          <Separator />

          <Button
            className="h-12 w-full bg-primary text-base hover:bg-[var(--machine-dark)]"
            disabled={!isValid || createEquipment.isPending}
            onClick={handleSubmit}
          >
            {createEquipment.isPending ? (
              <><Loader2 className="mr-2 h-5 w-5 animate-spin" />Saving...</>
            ) : (
              <><Save className="mr-2 h-5 w-5" />Save Equipment</>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
