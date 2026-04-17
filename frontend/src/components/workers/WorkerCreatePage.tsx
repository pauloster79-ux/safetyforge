import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import { useCreateWorker } from '@/hooks/useWorkers';
import { ROUTES, WORKER_ROLES, TRADE_TYPES } from '@/lib/constants';

export function WorkerCreatePage() {
  const navigate = useCanvasNavigate();
  const createWorker = useCreateWorker();

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    role: 'laborer',
    trade: 'general',
    language_preference: 'en' as 'en' | 'es' | 'both',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    hire_date: '',
    notes: '',
  });

  const handleChange = (field: string, value: string | null) => {
    if (value !== null) setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!form.first_name || !form.last_name) return;
    const result = await createWorker.mutateAsync({
      ...form,
      hire_date: form.hire_date || null,
    });
    navigate(ROUTES.WORKER_DETAIL(result.id));
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(ROUTES.WORKERS)}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Add Worker</h1>
          <p className="text-sm text-muted-foreground">Add a new crew member to your team</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Worker Details</CardTitle>
          <CardDescription>Basic information about the worker</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>First Name *</Label>
              <Input
                value={form.first_name}
                onChange={(e) => handleChange('first_name', e.target.value)}
                placeholder="First name"
              />
            </div>
            <div className="space-y-2">
              <Label>Last Name *</Label>
              <Input
                value={form.last_name}
                onChange={(e) => handleChange('last_name', e.target.value)}
                placeholder="Last name"
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Role</Label>
              <Select value={form.role} onValueChange={(v) => handleChange('role', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {WORKER_ROLES.map(r => (
                    <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Trade</Label>
              <Select value={form.trade} onValueChange={(v) => handleChange('trade', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">General</SelectItem>
                  {TRADE_TYPES.map(t => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Language Preference</Label>
            <Select
              value={form.language_preference}
              onValueChange={(v) => handleChange('language_preference', v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="es">Spanish</SelectItem>
                <SelectItem value="both">Bilingual (EN/ES)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Phone</Label>
              <Input
                value={form.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                placeholder="(555) 123-4567"
              />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                type="email"
                value={form.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="worker@company.com"
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Emergency Contact Name</Label>
              <Input
                value={form.emergency_contact_name}
                onChange={(e) => handleChange('emergency_contact_name', e.target.value)}
                placeholder="Contact name"
              />
            </div>
            <div className="space-y-2">
              <Label>Emergency Contact Phone</Label>
              <Input
                value={form.emergency_contact_phone}
                onChange={(e) => handleChange('emergency_contact_phone', e.target.value)}
                placeholder="(555) 123-4567"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Hire Date</Label>
            <Input
              type="date"
              value={form.hire_date}
              onChange={(e) => handleChange('hire_date', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Notes</Label>
            <Textarea
              value={form.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
              rows={3}
              placeholder="Additional notes about this worker..."
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={() => navigate(ROUTES.WORKERS)}>
              Cancel
            </Button>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={handleSubmit}
              disabled={!form.first_name || !form.last_name || createWorker.isPending}
            >
              {createWorker.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Add Worker
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
