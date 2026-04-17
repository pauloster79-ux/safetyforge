import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import {
  ArrowLeft,
  Loader2,
  Phone,
  Mail,
  AlertTriangle,
  Plus,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Calendar,
  Shield,
  UserCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useWorker, useAddCertification, useRemoveCertification } from '@/hooks/useWorkers';
import { ROUTES, CERTIFICATION_TYPES, WORKER_ROLES } from '@/lib/constants';
import type { Worker, Certification } from '@/lib/constants';
import { differenceInDays, format } from 'date-fns';

function StatusBadge({ status }: { status: Worker['status'] }) {
  const config = {
    active: { label: 'Active', className: 'bg-[var(--pass-bg)] text-[var(--pass)] hover:bg-[var(--pass-bg)]' },
    inactive: { label: 'Inactive', className: 'bg-muted text-muted-foreground hover:bg-muted' },
    terminated: { label: 'Terminated', className: 'bg-[var(--fail-bg)] text-[var(--fail)] hover:bg-[var(--fail-bg)]' },
  };
  const { label, className } = config[status] || { label: status, className: 'bg-muted text-muted-foreground hover:bg-muted' };
  return <Badge className={className}>{label}</Badge>;
}

function CertStatusBadge({ cert }: { cert: Certification }) {
  if (cert.status === 'expired') {
    const daysAgo = cert.expiry_date ? differenceInDays(new Date(), new Date(cert.expiry_date)) : 0;
    return (
      <div className="flex items-center gap-1.5">
        <XCircle className="h-4 w-4 text-[var(--fail)]" />
        <span className="text-sm font-medium text-[var(--fail)]">Expired</span>
        {daysAgo > 0 && <span className="text-xs text-[var(--fail)]">({daysAgo}d ago)</span>}
      </div>
    );
  }
  if (cert.status === 'expiring_soon') {
    const daysLeft = cert.expiry_date ? differenceInDays(new Date(cert.expiry_date), new Date()) : 0;
    return (
      <div className="flex items-center gap-1.5">
        <AlertCircle className="h-4 w-4 text-[var(--warn)]" />
        <span className="text-sm font-medium text-[var(--warn)]">Expiring Soon</span>
        {daysLeft > 0 && <span className="text-xs text-[var(--warn)]">(in {daysLeft}d)</span>}
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1.5">
      <CheckCircle2 className="h-4 w-4 text-[var(--pass)]" />
      <span className="text-sm font-medium text-[var(--pass)]">Valid</span>
    </div>
  );
}

// Recommended certifications by role
const ROLE_RECOMMENDED_CERTS: Record<string, string[]> = {
  foreman: ['osha_30', 'fall_protection', 'first_aid_cpr', 'scaffold_competent'],
  superintendent: ['osha_30', 'fall_protection', 'first_aid_cpr', 'confined_space', 'scaffold_competent', 'excavation_competent'],
  laborer: ['osha_10', 'hazcom_ghs', 'first_aid_cpr'],
  apprentice: ['osha_10', 'hazcom_ghs'],
  journeyman: ['osha_10', 'fall_protection', 'first_aid_cpr'],
  operator: ['osha_10', 'forklift_operator', 'aerial_lift', 'first_aid_cpr'],
  safety_officer: ['osha_30', 'fall_protection', 'first_aid_cpr', 'confined_space', 'hazwoper', 'respiratory_fit_test'],
};

export function WorkerDetailPage() {
  const navigate = useCanvasNavigate();
  const { workerId } = useParams<{ workerId: string }>();
  const { data: worker, isLoading } = useWorker(workerId);
  const addCertification = useAddCertification();
  const removeCertification = useRemoveCertification();

  const [certDialogOpen, setCertDialogOpen] = useState(false);
  const [certForm, setCertForm] = useState({
    certification_type: '',
    issued_date: '',
    expiry_date: '',
    issuing_body: '',
    certificate_number: '',
    notes: '',
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!worker) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <p className="text-sm text-muted-foreground">Worker not found</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate(ROUTES.WORKERS)}>
          Back to Workers
        </Button>
      </div>
    );
  }

  const roleLabel = WORKER_ROLES.find(r => r.value === worker.role)?.label || worker.role;
  const getCertTypeName = (typeId: string) =>
    CERTIFICATION_TYPES.find(ct => ct.id === typeId)?.name || typeId;

  // Missing recommended certs
  const recommended = ROLE_RECOMMENDED_CERTS[worker.role] ?? [];
  const hasCertTypes = new Set((worker.certifications || []).map(c => c.certification_type));
  const missingRecommended = recommended.filter(certType => !hasCertTypes.has(certType));

  const handleOpenCertDialog = (prefillType?: string) => {
    const certTypeConfig = CERTIFICATION_TYPES.find(ct => ct.id === prefillType);
    setCertForm({
      certification_type: prefillType || '',
      issued_date: new Date().toISOString().split('T')[0],
      expiry_date: certTypeConfig && 'typical_years' in certTypeConfig && certTypeConfig.typical_years
        ? new Date(Date.now() + (certTypeConfig.typical_years as number) * 365.25 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
        : '',
      issuing_body: '',
      certificate_number: '',
      notes: '',
    });
    setCertDialogOpen(true);
  };

  const handleSaveCert = async () => {
    if (!workerId || !certForm.certification_type || !certForm.issued_date) return;
    await addCertification.mutateAsync({
      workerId,
      certification_type: certForm.certification_type,
      issued_date: certForm.issued_date,
      expiry_date: certForm.expiry_date || null,
      issuing_body: certForm.issuing_body,
      certificate_number: certForm.certificate_number,
      status: 'valid',
      notes: certForm.notes,
    });
    setCertDialogOpen(false);
  };

  const handleRemoveCert = async (certId: string) => {
    if (!workerId) return;
    await removeCertification.mutateAsync({ workerId, certId });
  };

  const handleCertTypeChange = (value: string | null) => {
    if (!value) return;
    const certTypeConfig = CERTIFICATION_TYPES.find(ct => ct.id === value);
    const expiresConfig = certTypeConfig && 'typical_years' in certTypeConfig && certTypeConfig.typical_years;
    setCertForm(prev => ({
      ...prev,
      certification_type: value,
      expiry_date: expiresConfig
        ? new Date(
            new Date(prev.issued_date || Date.now()).getTime() +
              (certTypeConfig.typical_years as number) * 365.25 * 24 * 60 * 60 * 1000
          ).toISOString().split('T')[0]
        : certTypeConfig && !certTypeConfig.expires
          ? ''
          : prev.expiry_date,
    }));
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="mt-1"
            onClick={() => navigate(ROUTES.WORKERS)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">
                {worker.first_name} {worker.last_name}
              </h1>
              <StatusBadge status={worker.status} />
            </div>
            <div className="mt-1 flex items-center gap-3 text-sm text-muted-foreground">
              <Badge variant="secondary" className="capitalize">{roleLabel}</Badge>
              <span className="capitalize">{worker.trade.replace('_', ' ')}</span>
              <span>
                {worker.language_preference === 'en' ? 'English' : worker.language_preference === 'es' ? 'Spanish' : 'Bilingual'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Contact Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Contact Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex items-center gap-2 text-sm">
              <Phone className="h-4 w-4 text-muted-foreground" />
              <span className="text-[var(--concrete-600)]">{worker.phone || 'No phone'}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span className="text-[var(--concrete-600)]">{worker.email || 'No email'}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <UserCircle className="h-4 w-4 text-muted-foreground" />
              <div>
                <span className="text-xs text-muted-foreground">Emergency Contact</span>
                <p className="text-[var(--concrete-600)]">
                  {worker.emergency_contact_name || 'Not set'}
                  {worker.emergency_contact_phone && ` - ${worker.emergency_contact_phone}`}
                </p>
              </div>
            </div>
            {worker.hire_date && (
              <div className="flex items-center gap-2 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <span className="text-xs text-muted-foreground">Hire Date</span>
                  <p className="text-[var(--concrete-600)]">{format(new Date(worker.hire_date), 'MMM d, yyyy')}</p>
                </div>
              </div>
            )}
          </div>
          {worker.notes && (
            <div className="mt-4 rounded-lg bg-muted p-3 text-sm text-muted-foreground">
              {worker.notes}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Certifications */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base">Certifications</CardTitle>
            <CardDescription>
              {worker.total_certifications} total
              {worker.expiring_soon > 0 && `, ${worker.expiring_soon} expiring soon`}
              {worker.expired > 0 && `, ${worker.expired} expired`}
            </CardDescription>
          </div>
          <Button
            size="sm"
            className="bg-primary hover:bg-[var(--machine-dark)]"
            onClick={() => handleOpenCertDialog()}
          >
            <Plus className="mr-1 h-4 w-4" />
            Add Certification
          </Button>
        </CardHeader>
        <CardContent>
          {(worker.certifications || []).length > 0 ? (
            <div className="space-y-3">
              {(worker.certifications || [])
                .sort((a, b) => {
                  const order = { expired: 0, expiring_soon: 1, valid: 2 };
                  return order[a.status] - order[b.status];
                })
                .map((cert) => (
                  <div
                    key={cert.id}
                    className={`flex items-center gap-4 rounded-lg border p-3 ${
                      cert.status === 'expired'
                        ? 'border-[var(--fail)] bg-[var(--fail-bg)]/50'
                        : cert.status === 'expiring_soon'
                          ? 'border-[var(--warn)] bg-[var(--warn-bg)]/50'
                          : 'border-border'
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-foreground">
                        {getCertTypeName(cert.certification_type)}
                      </p>
                      <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                        {cert.issuing_body && <span>{cert.issuing_body}</span>}
                        {cert.certificate_number && <span>#{cert.certificate_number}</span>}
                        <span>Issued: {format(new Date(cert.issued_date), 'MMM d, yyyy')}</span>
                        {cert.expiry_date && (
                          <span>Expires: {format(new Date(cert.expiry_date), 'MMM d, yyyy')}</span>
                        )}
                        {!cert.expiry_date && <span className="text-[var(--pass)]">No expiry</span>}
                      </div>
                      {cert.notes && (
                        <p className="mt-1 text-xs text-muted-foreground">{cert.notes}</p>
                      )}
                    </div>
                    <CertStatusBadge cert={cert} />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-[var(--fail)]"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveCert(cert.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
            </div>
          ) : (
            <div className="flex flex-col items-center py-8 text-center">
              <Shield className="h-12 w-12 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-muted-foreground">No certifications</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Add certifications to track compliance
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recommended Certifications */}
      {missingRecommended.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recommended Certifications</CardTitle>
            <CardDescription>
              Based on the {roleLabel} role, these certifications are recommended
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {missingRecommended.map((certType) => (
                <div
                  key={certType}
                  className="flex items-center justify-between rounded-lg border border-dashed border-border p-3"
                >
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-[var(--warn)]" />
                    <span className="text-sm text-[var(--concrete-600)]">{getCertTypeName(certType)}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleOpenCertDialog(certType)}
                  >
                    <Plus className="mr-1 h-3 w-3" />
                    Add
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Certification Dialog */}
      <Dialog open={certDialogOpen} onOpenChange={setCertDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Certification</DialogTitle>
            <DialogDescription>
              Record a new certification for {worker.first_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Certification Type</Label>
              <Select
                value={certForm.certification_type}
                onValueChange={handleCertTypeChange}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select certification..." />
                </SelectTrigger>
                <SelectContent>
                  {CERTIFICATION_TYPES.map(ct => (
                    <SelectItem key={ct.id} value={ct.id}>{ct.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Issued Date</Label>
                <Input
                  type="date"
                  value={certForm.issued_date}
                  onChange={(e) => setCertForm(prev => ({ ...prev, issued_date: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>
                  Expiry Date
                  {certForm.certification_type && !CERTIFICATION_TYPES.find(ct => ct.id === certForm.certification_type)?.expires && (
                    <span className="ml-1 text-xs text-muted-foreground">(no expiry)</span>
                  )}
                </Label>
                <Input
                  type="date"
                  value={certForm.expiry_date}
                  onChange={(e) => setCertForm(prev => ({ ...prev, expiry_date: e.target.value }))}
                  disabled={
                    !!certForm.certification_type &&
                    !CERTIFICATION_TYPES.find(ct => ct.id === certForm.certification_type)?.expires
                  }
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Issuing Body</Label>
              <Input
                value={certForm.issuing_body}
                onChange={(e) => setCertForm(prev => ({ ...prev, issuing_body: e.target.value }))}
                placeholder="e.g., OSHA Training Institute"
              />
            </div>
            <div className="space-y-2">
              <Label>Certificate Number</Label>
              <Input
                value={certForm.certificate_number}
                onChange={(e) => setCertForm(prev => ({ ...prev, certificate_number: e.target.value }))}
                placeholder="e.g., OT-30-2024-88321"
              />
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={certForm.notes}
                onChange={(e) => setCertForm(prev => ({ ...prev, notes: e.target.value }))}
                rows={2}
                placeholder="Optional notes..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCertDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={handleSaveCert}
              disabled={!certForm.certification_type || !certForm.issued_date || addCertification.isPending}
            >
              {addCertification.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Save Certification
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
