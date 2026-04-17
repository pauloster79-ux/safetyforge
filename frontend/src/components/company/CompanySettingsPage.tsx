import { useState, useEffect } from 'react';
import { Save, Loader2, Building2, User, Phone, Mail, Shield, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useCompany, useUpdateCompany } from '@/hooks/useCompany';
import { useAuth } from '@/hooks/useAuth';

export function CompanySettingsPage() {
  const { user } = useAuth();
  const { data: company, isLoading } = useCompany();
  const updateCompany = useUpdateCompany();

  const [formData, setFormData] = useState({
    name: '',
    address: '',
    phone: '',
    email: '',
    license_number: '',
    ein: '',
    safety_officer: '',
    safety_officer_phone: '',
  });
  const [hasChanges, setHasChanges] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (company) {
      setFormData({
        name: company.name || '',
        address: company.address || '',
        phone: company.phone || '',
        email: company.email || '',
        license_number: company.license_number || '',
        ein: company.ein || '',
        safety_officer: company.safety_officer || '',
        safety_officer_phone: company.safety_officer_phone || '',
      });
    }
  }, [company]);

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    await updateCompany.mutateAsync(formData);
    setHasChanges(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Company Settings</h1>
          <p className="text-sm text-muted-foreground">
            Manage your company profile. This information appears on generated documents.
          </p>
        </div>
        <Button
          className="bg-primary hover:bg-[var(--machine-dark)]"
          onClick={handleSave}
          disabled={!hasChanges || updateCompany.isPending}
        >
          {updateCompany.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : saveSuccess ? (
            <Check className="mr-2 h-4 w-4" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          {saveSuccess ? 'Saved' : 'Save Changes'}
        </Button>
      </div>

      {saveSuccess && (
        <Alert className="border-[var(--pass)] bg-[var(--pass-bg)] text-[var(--pass)]">
          <Check className="h-4 w-4 text-[var(--pass)]" />
          <AlertDescription>Company settings saved successfully.</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">Company Information</CardTitle>
          </div>
          <CardDescription>
            Basic company details used in document headers and compliance fields
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Company Name</Label>
              <Input
                id="name"
                placeholder="ABC Construction LLC"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="license_number">Contractor License #</Label>
              <Input
                id="license_number"
                placeholder="CL-123456"
                value={formData.license_number}
                onChange={(e) => handleChange('license_number', e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="address">Business Address</Label>
            <Input
              id="address"
              placeholder="123 Main Street, Suite 100, City, State 12345"
              value={formData.address}
              onChange={(e) => handleChange('address', e.target.value)}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="phone">
                <Phone className="mr-1 inline-block h-3 w-3" />
                Phone Number
              </Label>
              <Input
                id="phone"
                type="tel"
                placeholder="(555) 123-4567"
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">
                <Mail className="mr-1 inline-block h-3 w-3" />
                Company Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="info@abcconstruction.com"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="ein">EIN (Tax ID)</Label>
            <Input
              id="ein"
              placeholder="XX-XXXXXXX"
              value={formData.ein}
              onChange={(e) => handleChange('ein', e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">Safety Officer</CardTitle>
          </div>
          <CardDescription>
            Designated safety officer information for compliance documents
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="safety_officer">Safety Officer Name</Label>
              <Input
                id="safety_officer"
                placeholder="John Smith"
                value={formData.safety_officer}
                onChange={(e) => handleChange('safety_officer', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="safety_officer_phone">Safety Officer Phone</Label>
              <Input
                id="safety_officer_phone"
                type="tel"
                placeholder="(555) 987-6543"
                value={formData.safety_officer_phone}
                onChange={(e) => handleChange('safety_officer_phone', e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <User className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">Account</CardTitle>
          </div>
          <CardDescription>Your personal account information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input value={user?.fullName || ''} disabled className="bg-muted" />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input value={user?.primaryEmailAddress?.emailAddress || ''} disabled className="bg-muted" />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Account details are managed through your authentication provider.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
