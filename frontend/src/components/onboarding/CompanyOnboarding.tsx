import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { HardHat, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';
import { ROUTES } from '@/lib/constants';

const JURISDICTIONS = [
  { code: 'US', name: 'United States', flag: '\uD83C\uDDFA\uD83C\uDDF8' },
  { code: 'UK', name: 'United Kingdom', flag: '\uD83C\uDDEC\uD83C\uDDE7' },
  { code: 'AU', name: 'Australia', flag: '\uD83C\uDDE6\uD83C\uDDFA' },
  { code: 'CA', name: 'Canada', flag: '\uD83C\uDDE8\uD83C\uDDE6' },
] as const;

const TRADE_TYPES = [
  { value: 'general', label: 'General Contractor' },
  { value: 'electrical', label: 'Electrical' },
  { value: 'plumbing', label: 'Plumbing' },
  { value: 'hvac', label: 'HVAC' },
  { value: 'carpentry', label: 'Carpentry' },
  { value: 'masonry', label: 'Masonry' },
  { value: 'roofing', label: 'Roofing' },
  { value: 'steel', label: 'Welding' },
  { value: 'concrete', label: 'Equipment' },
  { value: 'demolition', label: 'Demolition' },
  { value: 'excavation', label: 'Excavation' },
  { value: 'other', label: 'Other' },
] as const;

export function CompanyOnboarding() {
  const [jurisdictionCode, setJurisdictionCode] = useState('US');
  const [name, setName] = useState('');
  const [tradeType, setTradeType] = useState('general');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const selectedJurisdiction = JURISDICTIONS.find(j => j.code === jurisdictionCode) || JURISDICTIONS[0];

  const { clearNewUserFlag } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Company name is required.');
      return;
    }

    setLoading(true);
    try {
      const updateData: Record<string, string> = {
        name: name.trim(),
        trade_type: tradeType,
        jurisdiction_code: jurisdictionCode,
      };

      if (phone.trim()) {
        updateData.phone = phone.trim();
      }
      if (address.trim()) {
        updateData.address = address.trim();
      }

      await api.patch('/me/company', updateData);
      clearNewUserFlag();
      navigate(ROUTES.DASHBOARD, { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update company profile';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--concrete-50)] px-4">
      <div className="w-full max-w-lg">
        <div className="mb-8 flex flex-col items-center">
          <div
            className="flex items-center justify-center"
            style={{
              width: 34,
              height: 34,
              background: 'var(--machine)',
              borderRadius: 6,
            }}
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path
                d="M4 9.5L7.5 13L14 5.5"
                stroke="white"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <h1
            className="mt-4 text-[20px] font-bold"
            style={{ color: 'var(--concrete-900)', fontFamily: 'IBM Plex Sans, sans-serif' }}
          >
            Safety<span style={{ color: 'var(--machine)' }}>Forge</span>
          </h1>
          <p
            className="mt-1 text-[13px]"
            style={{ color: 'var(--concrete-400)', fontFamily: 'IBM Plex Sans, sans-serif' }}
          >
            Let's set up your company profile
          </p>
        </div>

        <Card className="border-[var(--concrete-100)]" style={{ borderRadius: 0 }}>
          <CardHeader className="text-center">
            <CardTitle
              className="text-[16px] font-bold"
              style={{ color: 'var(--concrete-900)', fontFamily: 'IBM Plex Sans, sans-serif' }}
            >
              Company Details
            </CardTitle>
            <CardDescription
              className="text-[13px]"
              style={{ color: 'var(--concrete-400)', fontFamily: 'IBM Plex Sans, sans-serif' }}
            >
              Tell us about your company to get started
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label
                  htmlFor="jurisdiction"
                  className="text-[13px] font-medium"
                  style={{ color: 'var(--concrete-800)', fontFamily: 'IBM Plex Sans, sans-serif' }}
                >
                  Country / Jurisdiction <span style={{ color: 'var(--fail)' }}>*</span>
                </Label>
                <select
                  id="jurisdiction"
                  value={jurisdictionCode}
                  onChange={(e) => setJurisdictionCode(e.target.value)}
                  disabled={loading}
                  className="flex h-9 w-full border border-[var(--concrete-200)] bg-white px-3 py-1 text-[13px] shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--machine)]"
                  style={{
                    borderRadius: 3,
                    fontFamily: 'IBM Plex Sans, sans-serif',
                    color: 'var(--concrete-800)',
                  }}
                >
                  {JURISDICTIONS.map((j) => (
                    <option key={j.code} value={j.code}>
                      {j.flag} {j.name}
                    </option>
                  ))}
                </select>
                <p className="text-[11px]" style={{ color: 'var(--concrete-400)', fontFamily: 'IBM Plex Mono, monospace' }}>
                  This determines your regulatory framework, document types, and compliance standards
                </p>
              </div>

              <div className="space-y-2">
                <Label
                  htmlFor="company-name"
                  className="text-[13px] font-medium"
                  style={{ color: 'var(--concrete-800)', fontFamily: 'IBM Plex Sans, sans-serif' }}
                >
                  Company Name <span style={{ color: 'var(--fail)' }}>*</span>
                </Label>
                <Input
                  id="company-name"
                  type="text"
                  placeholder="e.g. Torres Construction LLC"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  disabled={loading}
                  className="border-[var(--concrete-200)] font-mono text-[13px]"
                  style={{ borderRadius: 3, fontFamily: 'IBM Plex Mono, monospace' }}
                />
              </div>

              <div className="space-y-2">
                <Label
                  htmlFor="trade-type"
                  className="text-[13px] font-medium"
                  style={{ color: 'var(--concrete-800)', fontFamily: 'IBM Plex Sans, sans-serif' }}
                >
                  Trade Type
                </Label>
                <select
                  id="trade-type"
                  value={tradeType}
                  onChange={(e) => setTradeType(e.target.value)}
                  disabled={loading}
                  className="flex h-9 w-full border border-[var(--concrete-200)] bg-white px-3 py-1 text-[13px] shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--machine)]"
                  style={{
                    borderRadius: 3,
                    fontFamily: 'IBM Plex Mono, monospace',
                    color: 'var(--concrete-800)',
                  }}
                >
                  {TRADE_TYPES.map((trade) => (
                    <option key={trade.value} value={trade.value}>
                      {trade.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label
                  htmlFor="phone"
                  className="text-[13px] font-medium"
                  style={{ color: 'var(--concrete-800)', fontFamily: 'IBM Plex Sans, sans-serif' }}
                >
                  Phone <span className="text-[11px]" style={{ color: 'var(--concrete-400)' }}>(optional)</span>
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder={jurisdictionCode === 'UK' ? '+44 7700 900000' : jurisdictionCode === 'AU' ? '+61 400 000 000' : jurisdictionCode === 'CA' ? '(555) 123-4567' : '(555) 123-4567'}
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  disabled={loading}
                  className="border-[var(--concrete-200)] font-mono text-[13px]"
                  style={{ borderRadius: 3, fontFamily: 'IBM Plex Mono, monospace' }}
                />
              </div>

              <div className="space-y-2">
                <Label
                  htmlFor="address"
                  className="text-[13px] font-medium"
                  style={{ color: 'var(--concrete-800)', fontFamily: 'IBM Plex Sans, sans-serif' }}
                >
                  Address <span className="text-[11px]" style={{ color: 'var(--concrete-400)' }}>(optional)</span>
                </Label>
                <Input
                  id="address"
                  type="text"
                  placeholder={jurisdictionCode === 'UK' ? '10 Downing St, London, SW1A 2AA' : jurisdictionCode === 'AU' ? '1 George St, Sydney, NSW 2000' : jurisdictionCode === 'CA' ? '123 Main St, Toronto, ON M5V 1A1' : '123 Main St, City, State'}
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  disabled={loading}
                  className="border-[var(--concrete-200)] font-mono text-[13px]"
                  style={{ borderRadius: 3, fontFamily: 'IBM Plex Mono, monospace' }}
                />
              </div>

              <Button
                type="submit"
                className="w-full text-[13px] font-semibold"
                disabled={loading}
                style={{
                  background: 'var(--machine)',
                  color: 'var(--black)',
                  borderRadius: 3,
                  fontFamily: 'IBM Plex Sans, sans-serif',
                }}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Setting up...
                  </>
                ) : (
                  'Complete Setup'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
