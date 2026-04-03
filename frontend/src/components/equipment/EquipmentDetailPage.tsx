import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Loader2,
  Check,
  X,
  Minus,
  Send,
  ClipboardCheck,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  useEquipmentItem,
  useEquipmentInspections,
  useCreateEquipmentInspection,
} from '@/hooks/useEquipment';
import {
  ROUTES,
  EQUIPMENT_TYPES,
  EQUIPMENT_INSPECTION_ITEMS,
  CERTIFICATION_TYPES,
} from '@/lib/constants';
import type { Equipment } from '@/lib/constants';
import { cn } from '@/lib/utils';

function StatusBadge({ status }: { status: Equipment['status'] }) {
  const config = {
    active: { label: 'Active', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    out_of_service: { label: 'Out of Service', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
    maintenance: { label: 'Maintenance', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
    retired: { label: 'Retired', className: 'bg-muted text-muted-foreground hover:bg-muted' },
  };
  const { label, className } = config[status];
  return <Badge className={className}>{label}</Badge>;
}

function InspectionStatusBadge({ status }: { status: 'pass' | 'fail' }) {
  if (status === 'pass') {
    return <Badge className="bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]">Pass</Badge>;
  }
  return <Badge className="bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]">Fail</Badge>;
}

interface ChecklistItemState {
  item: string;
  status: 'pass' | 'fail' | 'na' | 'pending';
  notes: string;
}

export function EquipmentDetailPage() {
  const navigate = useNavigate();
  const { equipmentId } = useParams<{ equipmentId: string }>();
  const { data: equipment, isLoading } = useEquipmentItem(equipmentId);
  const { data: inspections, isLoading: inspLoading } = useEquipmentInspections(equipmentId);
  const createInspection = useCreateEquipmentInspection(equipmentId || '');

  const [showInspection, setShowInspection] = useState(false);
  const [inspHeader, setInspHeader] = useState({
    inspection_date: new Date().toISOString().split('T')[0],
    inspector_name: '',
    inspection_type: 'Routine',
    deficiencies_found: '',
  });
  const [inspItems, setInspItems] = useState<ChecklistItemState[]>([]);
  const [outOfService, setOutOfService] = useState(false);

  const startInspection = () => {
    if (!equipment) return;
    const type = equipment.equipment_type;
    const templateItems = EQUIPMENT_INSPECTION_ITEMS[type as keyof typeof EQUIPMENT_INSPECTION_ITEMS]
      || EQUIPMENT_INSPECTION_ITEMS.general;
    setInspItems(templateItems.map(item => ({ item, status: 'pending' as const, notes: '' })));
    setShowInspection(true);
  };

  const handleItemStatus = (index: number, status: 'pass' | 'fail' | 'na') => {
    setInspItems(prev => prev.map((item, i) => i === index ? { ...item, status } : item));
  };

  const handleItemNotes = (index: number, notes: string) => {
    setInspItems(prev => prev.map((item, i) => i === index ? { ...item, notes } : item));
  };

  const allComplete = inspItems.length > 0 && inspItems.every(i => i.status !== 'pending');
  const failCount = inspItems.filter(i => i.status === 'fail').length;

  const handleSubmitInspection = () => {
    createInspection.mutate({
      ...inspHeader,
      items: inspItems.filter(i => i.status !== 'pending').map(i => ({
        item: i.item,
        status: i.status as string,
        notes: i.notes,
      })),
      out_of_service: outOfService,
    }, {
      onSuccess: () => {
        setShowInspection(false);
        setInspItems([]);
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!equipment) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Equipment not found</p>
      </div>
    );
  }

  // Inspection form flow
  if (showInspection) {
    return (
      <div className="mx-auto max-w-lg pb-24">
        <div className="mb-4 flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => setShowInspection(false)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-lg font-bold text-foreground">Equipment Inspection</h1>
            <p className="text-xs text-muted-foreground">{equipment.name}</p>
          </div>
        </div>

        {/* Header fields */}
        <Card className="mb-4">
          <CardContent className="space-y-3 pt-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Date</Label>
                <Input type="date" value={inspHeader.inspection_date} onChange={e => setInspHeader(prev => ({ ...prev, inspection_date: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>Type</Label>
                <Input value={inspHeader.inspection_type} onChange={e => setInspHeader(prev => ({ ...prev, inspection_type: e.target.value }))} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Inspector Name <span className="text-[var(--fail)]">*</span></Label>
              <Input value={inspHeader.inspector_name} onChange={e => setInspHeader(prev => ({ ...prev, inspector_name: e.target.value }))} placeholder="Your name" />
            </div>
          </CardContent>
        </Card>

        {/* Progress bar */}
        <div className="mb-4 h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all duration-300"
            style={{ width: `${inspItems.length > 0 ? (inspItems.filter(i => i.status !== 'pending').length / inspItems.length) * 100 : 0}%` }}
          />
        </div>

        <div className="space-y-2">
          {inspItems.map((item, index) => (
            <div
              key={item.item}
              className={cn(
                'rounded-lg border p-3 transition-colors',
                item.status === 'pass' && 'border-[var(--pass)] bg-[var(--pass-bg)]/50',
                item.status === 'fail' && 'border-[var(--fail)] bg-[var(--fail-bg)]/50',
                item.status === 'na' && 'border-border bg-muted/50',
                item.status === 'pending' && 'border-border bg-white',
              )}
            >
              <p className="mb-3 text-sm font-medium text-[var(--concrete-600)]">{item.item}</p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleItemStatus(index, 'pass')}
                  className={cn(
                    'flex h-10 flex-1 items-center justify-center gap-2 rounded-lg border-2 text-sm font-medium transition-all active:scale-95',
                    item.status === 'pass'
                      ? 'border-[var(--pass)] bg-[var(--pass)] text-white'
                      : 'border-border text-muted-foreground hover:border-[var(--pass)] hover:bg-[var(--pass-bg)]'
                  )}
                >
                  <Check className="h-4 w-4" /> Pass
                </button>
                <button
                  type="button"
                  onClick={() => handleItemStatus(index, 'fail')}
                  className={cn(
                    'flex h-10 flex-1 items-center justify-center gap-2 rounded-lg border-2 text-sm font-medium transition-all active:scale-95',
                    item.status === 'fail'
                      ? 'border-[var(--fail)] bg-[var(--fail)] text-white'
                      : 'border-border text-muted-foreground hover:border-[var(--fail)] hover:bg-[var(--fail-bg)]'
                  )}
                >
                  <X className="h-4 w-4" /> Fail
                </button>
                <button
                  type="button"
                  onClick={() => handleItemStatus(index, 'na')}
                  className={cn(
                    'flex h-10 w-14 shrink-0 items-center justify-center gap-1 rounded-lg border-2 text-sm font-medium transition-all active:scale-95',
                    item.status === 'na'
                      ? 'border-muted-foreground bg-muted-foreground text-white'
                      : 'border-border text-muted-foreground hover:border-border hover:bg-muted'
                  )}
                >
                  <Minus className="h-4 w-4" /> N/A
                </button>
              </div>
              {item.status === 'fail' && (
                <div className="mt-2">
                  <Textarea
                    placeholder="Describe the issue..."
                    value={item.notes}
                    onChange={e => handleItemNotes(index, e.target.value)}
                    rows={2}
                    className="text-sm"
                  />
                </div>
              )}
            </div>
          ))}
        </div>

        {failCount > 0 && (
          <Card className="mt-4">
            <CardContent className="space-y-3 pt-4">
              <div className="space-y-2">
                <Label>Deficiencies Found</Label>
                <Textarea
                  value={inspHeader.deficiencies_found}
                  onChange={e => setInspHeader(prev => ({ ...prev, deficiencies_found: e.target.value }))}
                  placeholder="Summary of deficiencies..."
                  rows={2}
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-[var(--fail)]">
                <input
                  type="checkbox"
                  checked={outOfService}
                  onChange={e => setOutOfService(e.target.checked)}
                  className="h-4 w-4 rounded border-[var(--fail)]"
                />
                Place equipment out of service
              </label>
            </CardContent>
          </Card>
        )}

        <div className="fixed bottom-0 left-0 right-0 border-t border-border bg-white p-4 lg:left-64">
          <div className="mx-auto max-w-lg">
            <Button
              className="h-12 w-full bg-primary text-base hover:bg-[var(--machine-dark)]"
              disabled={!allComplete || !inspHeader.inspector_name || createInspection.isPending}
              onClick={handleSubmitInspection}
            >
              {createInspection.isPending ? (
                <><Loader2 className="mr-2 h-5 w-5 animate-spin" />Submitting...</>
              ) : allComplete ? (
                <><Send className="mr-2 h-5 w-5" />Submit Inspection</>
              ) : (
                `Complete all items (${inspItems.filter(i => i.status !== 'pending').length}/${inspItems.length})`
              )}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const typeDef = EQUIPMENT_TYPES.find(t => t.id === equipment.equipment_type);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate(ROUTES.EQUIPMENT)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-foreground">{equipment.name}</h1>
            <StatusBadge status={equipment.status} />
          </div>
          <p className="text-sm text-muted-foreground">
            {equipment.make} {equipment.model}{equipment.year ? ` (${equipment.year})` : ''}
          </p>
        </div>
        <Button className="bg-primary hover:bg-[var(--machine-dark)]" onClick={startInspection}>
          <ClipboardCheck className="mr-2 h-4 w-4" />
          Run Inspection
        </Button>
      </div>

      {/* Details grid */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardContent className="pt-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Equipment Details</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Type</span>
                <span className="font-medium">{typeDef?.name || equipment.equipment_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Make / Model</span>
                <span className="font-medium">{equipment.make} {equipment.model}</span>
              </div>
              {equipment.year && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Year</span>
                  <span className="font-medium">{equipment.year}</span>
                </div>
              )}
              {equipment.serial_number && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Serial Number</span>
                  <span className="font-mono text-xs">{equipment.serial_number}</span>
                </div>
              )}
              {equipment.vin && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">VIN</span>
                  <span className="font-mono text-xs">{equipment.vin}</span>
                </div>
              )}
              {equipment.license_plate && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">License Plate</span>
                  <span className="font-medium">{equipment.license_plate}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Inspection Frequency</span>
                <span className="font-medium">{equipment.inspection_frequency}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Inspection Status</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last Inspection</span>
                <span className="font-mono text-xs">{equipment.last_inspection_date || 'None'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Next Due</span>
                <span className="font-mono text-xs">{equipment.next_inspection_due || 'Not set'}</span>
              </div>
              {equipment.annual_inspection_date && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Annual Inspection</span>
                  <span className="font-mono text-xs">{equipment.annual_inspection_date}</span>
                </div>
              )}
              {equipment.annual_inspection_due && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Annual Due</span>
                  <span className="font-mono text-xs">{equipment.annual_inspection_due}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* DOT section for vehicles */}
        {equipment.dot_number && (
          <Card>
            <CardContent className="pt-4">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">DOT Compliance</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">DOT Number</span>
                  <span className="font-mono text-xs">{equipment.dot_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">DOT Inspection Date</span>
                  <span className="font-mono text-xs">{equipment.dot_inspection_date || 'None'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">DOT Inspection Due</span>
                  <span className={cn('font-mono text-xs', equipment.dot_inspection_due && new Date(equipment.dot_inspection_due) < new Date() ? 'text-[var(--fail)] font-medium' : '')}>
                    {equipment.dot_inspection_due || 'Not set'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Required Certifications */}
        {equipment.required_certifications.length > 0 && (
          <Card>
            <CardContent className="pt-4">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Required Operator Certifications</h3>
              <div className="space-y-1">
                {equipment.required_certifications.map(certId => {
                  const certDef = CERTIFICATION_TYPES.find(c => c.id === certId);
                  return (
                    <div key={certId} className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2 text-sm">
                      <Check className="h-3.5 w-3.5 text-[var(--pass)]" />
                      <span>{certDef?.name || certId}</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Notes */}
      {equipment.notes && (
        <Card>
          <CardContent className="pt-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Notes</h3>
            <p className="text-sm text-muted-foreground">{equipment.notes}</p>
          </CardContent>
        </Card>
      )}

      {/* Inspection History */}
      <div>
        <h2 className="mb-3 text-lg font-bold text-foreground">Inspection History</h2>
        {inspLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
          </div>
        ) : inspections && inspections.length > 0 ? (
          <div className="space-y-3">
            {inspections.map((log) => (
              <Card key={log.id}>
                <CardContent className="flex items-center gap-4 py-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                    <ClipboardCheck className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-foreground">{log.inspection_type} Inspection</p>
                      <InspectionStatusBadge status={log.overall_status} />
                      {log.out_of_service && (
                        <Badge className="bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]">OOS</Badge>
                      )}
                    </div>
                    <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{log.inspection_date}</span>
                      <span>{log.inspector_name}</span>
                      <span>{log.items.filter(i => i.status === 'pass').length}/{log.items.length} passed</span>
                    </div>
                    {log.deficiencies_found && (
                      <p className="mt-1 text-xs text-[var(--fail)]">{log.deficiencies_found}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              <p>No inspection history yet</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
