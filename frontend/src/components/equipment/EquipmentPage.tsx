import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Wrench,
  Search,
  Loader2,
  AlertTriangle,
  XCircle,
  Check,
  Clock,
  ChevronDown,
  ChevronUp,
  Truck,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useEquipment, useEquipmentSummary, useDotCompliance } from '@/hooks/useEquipment';
import { ROUTES, EQUIPMENT_TYPES } from '@/lib/constants';
import type { Equipment } from '@/lib/constants';

function EquipmentStatusBadge({ status }: { status: Equipment['status'] }) {
  const config = {
    active: { label: 'Active', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    out_of_service: { label: 'Out of Service', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
    maintenance: { label: 'Maintenance', className: 'bg-[var(--warn-bg)] text-[var(--warn)] hover:bg-[var(--warn-bg)]' },
    retired: { label: 'Retired', className: 'bg-muted text-muted-foreground hover:bg-muted' },
  };
  const { label, className } = config[status];
  return <Badge className={className}>{label}</Badge>;
}

function InspectionIndicator({ equipment }: { equipment: Equipment }) {
  if (!equipment.next_inspection_due) {
    return <span className="text-xs text-muted-foreground">No schedule</span>;
  }
  const now = new Date();
  const due = new Date(equipment.next_inspection_due);
  const daysUntil = Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (daysUntil < 0) {
    return (
      <div className="flex items-center gap-1.5 text-xs">
        <XCircle className="h-3.5 w-3.5 text-[var(--fail)]" />
        <span className="font-medium text-[var(--fail)]">Overdue</span>
      </div>
    );
  }
  if (daysUntil <= 30) {
    return (
      <div className="flex items-center gap-1.5 text-xs">
        <Clock className="h-3.5 w-3.5 text-[var(--warn)]" />
        <span className="font-medium text-[var(--warn)]">Due in {daysUntil}d</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1.5 text-xs">
      <Check className="h-3.5 w-3.5 text-[var(--pass)]" />
      <span className="text-[var(--pass)]">Current</span>
    </div>
  );
}

export function EquipmentPage() {
  const navigate = useNavigate();
  const [typeFilter, setTypeFilter] = useState<string>('All');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [alertsExpanded, setAlertsExpanded] = useState(false);

  const params: Record<string, string> = {};
  if (!typeFilter.startsWith('All')) params.type = typeFilter;
  if (!statusFilter.startsWith('All')) params.status = statusFilter;

  const { data: equipment, isLoading } = useEquipment(
    Object.keys(params).length > 0 ? params : undefined
  );
  const { data: summary } = useEquipmentSummary();
  const { data: dotCompliance } = useDotCompliance();

  const filteredEquipment = equipment?.filter(e => {
    if (!searchQuery) return true;
    const s = searchQuery.toLowerCase();
    return e.name.toLowerCase().includes(s) || e.make.toLowerCase().includes(s) || e.model.toLowerCase().includes(s);
  });

  const overdueCount = summary?.overdue_inspections ?? 0;
  const dotDueSoon = dotCompliance?.vehicles?.filter(d => d.status === 'overdue') ?? [];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Equipment & Fleet</h1>
          <p className="text-sm text-muted-foreground">
            Manage equipment, inspections, and DOT compliance
          </p>
        </div>
        <Button
          className="bg-primary hover:bg-[var(--machine-dark)]"
          onClick={() => navigate(ROUTES.EQUIPMENT_NEW)}
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Equipment
        </Button>
      </div>

      {/* Alert banners */}
      {(overdueCount > 0 || dotDueSoon.length > 0) && (
        <div className="space-y-2">
          {overdueCount > 0 && (
            <div className="rounded-lg border border-[var(--fail)] bg-[var(--fail-bg)] p-4">
              <button
                className="flex w-full items-center justify-between text-left"
                onClick={() => setAlertsExpanded(prev => !prev)}
              >
                <div className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-[var(--fail)]" />
                  <span className="font-medium text-[var(--fail)]">
                    {overdueCount} equipment item{overdueCount !== 1 ? 's' : ''} with overdue inspections
                  </span>
                </div>
                {alertsExpanded ? (
                  <ChevronUp className="h-4 w-4 text-[var(--fail)]" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-[var(--fail)]" />
                )}
              </button>
              {alertsExpanded && equipment && (
                <div className="mt-3 space-y-1">
                  {equipment
                    .filter(e => e.next_inspection_due && new Date(e.next_inspection_due) < new Date())
                    .map(e => (
                      <button
                        key={e.id}
                        className="flex w-full items-center gap-2 rounded p-1.5 text-left text-sm text-[var(--fail)] hover:bg-[var(--fail-bg)]"
                        onClick={() => navigate(ROUTES.EQUIPMENT_DETAIL(e.id))}
                      >
                        <span className="font-medium">{e.name}</span>
                        <span className="text-[var(--fail)]">-</span>
                        <span>Due: {e.next_inspection_due}</span>
                      </button>
                    ))}
                </div>
              )}
            </div>
          )}
          {dotDueSoon.length > 0 && (
            <div className="rounded-lg border border-[var(--warn)] bg-[var(--warn-bg)] p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-[var(--warn)]" />
                <span className="font-medium text-[var(--warn)]">
                  {dotDueSoon.length} DOT inspection{dotDueSoon.length !== 1 ? 's' : ''} due within 30 days
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 sm:max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search equipment..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v || 'All')}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="All Types">All Types</SelectItem>
            {EQUIPMENT_TYPES.map(t => (
              <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v || 'All')}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="All Status">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="out_of_service">Out of Service</SelectItem>
            <SelectItem value="maintenance">Maintenance</SelectItem>
            <SelectItem value="retired">Retired</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Equipment list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : filteredEquipment && filteredEquipment.length > 0 ? (
        <div className="space-y-3">
          {filteredEquipment.map((equip) => {
            const typeDef = EQUIPMENT_TYPES.find(t => t.id === equip.equipment_type);
            return (
              <Card
                key={equip.id}
                className="cursor-pointer transition-shadow hover:shadow-md"
                onClick={() => navigate(ROUTES.EQUIPMENT_DETAIL(equip.id))}
              >
                <CardContent className="flex items-center gap-4 py-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                    {equip.equipment_type === 'vehicle' ? (
                      <Truck className="h-5 w-5 text-muted-foreground" />
                    ) : (
                      <Wrench className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-foreground">{equip.name}</p>
                      <Badge variant="secondary" className="text-xs">{typeDef?.name || equip.equipment_type}</Badge>
                      <EquipmentStatusBadge status={equip.status} />
                    </div>
                    <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{equip.make} {equip.model}{equip.year ? ` (${equip.year})` : ''}</span>
                      {equip.serial_number && <span>S/N: {equip.serial_number}</span>}
                      {equip.license_plate && <span>{equip.license_plate}</span>}
                    </div>
                    {equip.required_certifications.length > 0 && (
                      <div className="mt-1 flex items-center gap-1">
                        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Certs:</span>
                        {equip.required_certifications.map(cert => (
                          <Badge key={cert} variant="outline" className="text-[10px] py-0">{cert.replace(/_/g, ' ')}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <InspectionIndicator equipment={equip} />
                    {equip.last_inspection_date && (
                      <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">
                        Last: {equip.last_inspection_date}
                      </p>
                    )}
                    {equip.dot_number && (
                      <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">
                        DOT: {equip.dot_number}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <Wrench className="h-16 w-16 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium text-muted-foreground">No equipment yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Add your first piece of equipment to start tracking inspections
          </p>
          <Button
            className="mt-4 bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => navigate(ROUTES.EQUIPMENT_NEW)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Equipment
          </Button>
        </div>
      )}
    </div>
  );
}
