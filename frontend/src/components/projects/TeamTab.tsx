import { useState } from 'react';
import {
  Plus,
  Users,
  XCircle,
  Wrench,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useProjectAssignments, useCreateAssignment, useDeleteAssignment } from '@/hooks/useProjectAssignments';
import { useWorkers } from '@/hooks/useWorkers';
import { useEquipment } from '@/hooks/useEquipment';

export function TeamTab({ projectId }: { projectId: string }) {
  const { data: workerAssignments } = useProjectAssignments({ project_id: projectId, resource_type: 'worker', status: 'active' });
  const { data: equipmentAssignments } = useProjectAssignments({ project_id: projectId, resource_type: 'equipment' });
  const { data: allWorkers } = useWorkers();
  const { data: allEquipment } = useEquipment();
  const createAssignment = useCreateAssignment();
  const deleteAssignment = useDeleteAssignment();

  const [showAssignWorker, setShowAssignWorker] = useState(false);
  const [showAssignEquipment, setShowAssignEquipment] = useState(false);
  const [assignRole, setAssignRole] = useState('');
  const [selectedResourceId, setSelectedResourceId] = useState('');

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      {/* ── Workers ── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Workers</h2>
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => setShowAssignWorker(!showAssignWorker)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Assign Worker
          </Button>
        </div>

        {showAssignWorker && (
          <Card>
            <CardContent className="space-y-3 pt-4">
              <div className="space-y-3">
                <div>
                  <Label>Worker</Label>
                  <Select value={selectedResourceId} onValueChange={(v) => setSelectedResourceId(v ?? '')}>
                    <SelectTrigger><SelectValue placeholder="Select worker" /></SelectTrigger>
                    <SelectContent>
                      {allWorkers
                        ?.filter(w => !workerAssignments?.some(a => a.resource_id === w.id))
                        .map(w => (
                          <SelectItem key={w.id} value={w.id}>
                            {w.first_name} {w.last_name} — {w.role}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Role on Project</Label>
                  <Input
                    value={assignRole}
                    onChange={e => setAssignRole(e.target.value)}
                    placeholder="e.g. Foreman, Electrician"
                  />
                </div>
                <Button
                  className="bg-primary hover:bg-[var(--machine-dark)]"
                  disabled={!selectedResourceId}
                  onClick={() => {
                    createAssignment.mutate({
                      resource_type: 'worker',
                      resource_id: selectedResourceId,
                      project_id: projectId,
                      role: assignRole || undefined,
                      start_date: new Date().toISOString().split('T')[0],
                    });
                    setSelectedResourceId('');
                    setAssignRole('');
                    setShowAssignWorker(false);
                  }}
                >
                  Add
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {workerAssignments && workerAssignments.length > 0 ? (
          <div className="space-y-2">
            {workerAssignments.map(assignment => {
              const worker = allWorkers?.find(w => w.id === assignment.resource_id);
              return (
                <Card key={assignment.id}>
                  <CardContent className="flex items-center justify-between px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                        {worker ? `${worker.first_name[0]}${worker.last_name[0]}` : '??'}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {worker ? `${worker.first_name} ${worker.last_name}` : assignment.resource_id}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {assignment.role || worker?.role || 'No role assigned'}
                          {worker?.language_preference && (
                            <span className="ml-2 text-[var(--machine)]">{worker.language_preference.toUpperCase()}</span>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {worker && (
                        <div className="text-right text-xs">
                          <span className="text-[var(--pass)]">{worker.total_certifications || 0} certs</span>
                          {(worker.expiring_soon || 0) > 0 && (
                            <span className="ml-2 text-[var(--warn)]">{worker.expiring_soon} exp. soon</span>
                          )}
                          {(worker.expired || 0) > 0 && (
                            <span className="ml-2 text-[var(--fail)]">{worker.expired} expired</span>
                          )}
                        </div>
                      )}
                      <Badge className="bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]">
                        {assignment.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-muted-foreground hover:text-[var(--fail)]"
                        onClick={() => deleteAssignment.mutate(assignment.id)}
                      >
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <Users className="mx-auto h-10 w-10 text-muted-foreground/50" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">No workers assigned</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Assign workers to track certifications and training compliance
            </p>
          </div>
        )}
      </section>

      {/* ── Equipment ── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Equipment</h2>
          <Button
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => setShowAssignEquipment(!showAssignEquipment)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Assign Equipment
          </Button>
        </div>

        {showAssignEquipment && (
          <Card>
            <CardContent className="space-y-3 pt-4">
              <div className="space-y-3">
                <div>
                  <Label>Equipment</Label>
                  <Select value={selectedResourceId} onValueChange={(v) => setSelectedResourceId(v ?? '')}>
                    <SelectTrigger><SelectValue placeholder="Select equipment" /></SelectTrigger>
                    <SelectContent>
                      {allEquipment
                        ?.filter(e => !equipmentAssignments?.some(a => a.resource_id === e.id && a.status === 'active'))
                        .map(e => (
                          <SelectItem key={e.id} value={e.id}>
                            {e.name} — {e.equipment_type}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Role / Purpose</Label>
                  <Input
                    value={assignRole}
                    onChange={e => setAssignRole(e.target.value)}
                    placeholder="e.g. Main crane, Material transport"
                  />
                </div>
                <Button
                  className="bg-primary hover:bg-[var(--machine-dark)]"
                  disabled={!selectedResourceId}
                  onClick={() => {
                    createAssignment.mutate({
                      resource_type: 'equipment',
                      resource_id: selectedResourceId,
                      project_id: projectId,
                      role: assignRole || undefined,
                      start_date: new Date().toISOString().split('T')[0],
                    });
                    setSelectedResourceId('');
                    setAssignRole('');
                    setShowAssignEquipment(false);
                  }}
                >
                  Add
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {equipmentAssignments && equipmentAssignments.length > 0 ? (
          <div className="space-y-2">
            {equipmentAssignments.map(assignment => {
              const equip = allEquipment?.find(e => e.id === assignment.resource_id);
              return (
                <Card key={assignment.id}>
                  <CardContent className="flex items-center justify-between px-4 py-3">
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        {equip?.name || assignment.resource_id}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {equip?.equipment_type || ''} {equip?.make && equip?.model ? `— ${equip.make} ${equip.model}` : ''}
                        {assignment.role ? ` (${assignment.role})` : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right text-xs">
                        <span>Since {assignment.start_date}</span>
                        {assignment.end_date && (
                          <span className="ml-2 text-muted-foreground">to {assignment.end_date}</span>
                        )}
                      </div>
                      <Badge className={
                        assignment.status === 'active'
                          ? 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]'
                          : 'bg-muted text-muted-foreground hover:bg-muted'
                      }>
                        {assignment.status}
                      </Badge>
                      {assignment.status === 'active' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-muted-foreground hover:text-[var(--fail)]"
                          onClick={() => deleteAssignment.mutate(assignment.id)}
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <Wrench className="mx-auto h-10 w-10 text-muted-foreground/50" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">No equipment assigned</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Assign equipment to track inspections and certifications
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
