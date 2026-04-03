import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { useCompany } from '@/hooks/useCompany';

export interface JurisdictionLocale {
  languages: string[];
  dateFormat: string;
  temperatureUnit: string;
  measurementSystem: string;
  currency: string;
  currencySymbol: string;
  phoneFormat: string;
  addressFormat: string;
  taxType: string | null;
  taxRate: number;
}

export interface CertificationType {
  id: string;
  name: string;
  expires: boolean;
}

export interface DocumentType {
  id: string;
  name: string;
  abbreviation: string;
  required: boolean;
}

export interface TradeType {
  id: string;
  name: string;
}

export interface JurisdictionConfig {
  code: string;
  region: string | null;
  name: string;
  regulatoryBody: string;
  primaryLegislation: string;
  constructionLegislation: string;
  locale: JurisdictionLocale;
  safetyMetrics: {
    incidentRateName: string;
    incidentRateFullName: string;
    incidentRateMultiplier: number;
    secondaryRateName?: string;
    reportingBody: string;
  };
  recordKeeping: {
    name: string;
    featureKey: string;
    fullName: string;
  };
  complianceAudit: {
    name: string;
  };
  certificationTypes: CertificationType[];
  documentTypes: DocumentType[];
  tradeTypes: TradeType[];
}

const US_DEFAULT: JurisdictionConfig = {
  code: 'US',
  region: null,
  name: 'United States',
  regulatoryBody: 'Occupational Safety and Health Administration (OSHA)',
  primaryLegislation: 'Occupational Safety and Health Act of 1970',
  constructionLegislation: 'OSHA Standards for the Construction Industry (29 CFR 1926)',
  locale: {
    languages: ['en-US', 'es-US'],
    dateFormat: 'MM/DD/YYYY',
    temperatureUnit: 'fahrenheit',
    measurementSystem: 'imperial',
    currency: 'USD',
    currencySymbol: '$',
    phoneFormat: '(XXX) XXX-XXXX',
    addressFormat: '{line1}, {city}, {state} {zip}',
    taxType: null,
    taxRate: 0,
  },
  safetyMetrics: {
    incidentRateName: 'TRIR',
    incidentRateFullName: 'Total Recordable Incident Rate',
    incidentRateMultiplier: 200000,
    secondaryRateName: 'DART',
    reportingBody: 'OSHA',
  },
  recordKeeping: {
    name: 'OSHA 300 Log',
    featureKey: 'osha_log',
    fullName: 'OSHA Form 300 - Log of Work-Related Injuries and Illnesses',
  },
  complianceAudit: {
    name: 'Mock OSHA Inspection',
  },
  certificationTypes: [
    { id: 'osha_10', name: 'OSHA 10-Hour', expires: false },
    { id: 'osha_30', name: 'OSHA 30-Hour', expires: false },
    { id: 'fall_protection', name: 'Fall Protection Competent Person', expires: true },
    { id: 'scaffold_competent', name: 'Scaffold Competent Person', expires: true },
    { id: 'confined_space', name: 'Confined Space Entry', expires: true },
    { id: 'crane_operator_nccco', name: 'NCCCO Crane Operator', expires: true },
    { id: 'first_aid_cpr', name: 'First Aid/CPR', expires: true },
    { id: 'other', name: 'Other', expires: true },
  ],
  documentTypes: [
    { id: 'sssp', name: 'Site-Specific Safety Plan', abbreviation: 'SSSP', required: true },
    { id: 'jha', name: 'Job Hazard Analysis', abbreviation: 'JHA', required: true },
    { id: 'toolbox_talk', name: 'Toolbox Talk', abbreviation: 'TBT', required: false },
    { id: 'incident_report', name: 'Incident Report', abbreviation: 'IR', required: true },
    { id: 'fall_protection', name: 'Fall Protection Plan', abbreviation: 'FPP', required: true },
  ],
  tradeTypes: [
    { id: 'general', name: 'General Contractor' },
    { id: 'electrical', name: 'Electrical' },
    { id: 'plumbing', name: 'Plumbing' },
    { id: 'hvac', name: 'HVAC' },
    { id: 'roofing', name: 'Roofing' },
    { id: 'concrete', name: 'Concrete' },
    { id: 'steel', name: 'Structural Steel' },
    { id: 'demolition', name: 'Demolition' },
    { id: 'excavation', name: 'Excavation' },
    { id: 'other', name: 'Other' },
  ],
};

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const JurisdictionCtx = createContext<JurisdictionConfig>(US_DEFAULT);

function mapApiResponse(data: Record<string, unknown>): JurisdictionConfig {
  const locale = data.locale as Record<string, unknown> || {};
  const metrics = data.safety_metrics as Record<string, unknown> || {};
  const rk = data.record_keeping as Record<string, unknown> || {};
  const ca = data.compliance_audit as Record<string, unknown> || {};

  return {
    code: (data.code as string) || 'US',
    region: (data.region as string) || null,
    name: (data.name as string) || 'United States',
    regulatoryBody: (data.regulatory_body as string) || '',
    primaryLegislation: (data.primary_legislation as string) || '',
    constructionLegislation: (data.construction_legislation as string) || '',
    locale: {
      languages: (locale.languages as string[]) || ['en-US'],
      dateFormat: (locale.date_format as string) || 'MM/DD/YYYY',
      temperatureUnit: (locale.temperature_unit as string) || 'fahrenheit',
      measurementSystem: (locale.measurement_system as string) || 'imperial',
      currency: (locale.currency as string) || 'USD',
      currencySymbol: (locale.currency_symbol as string) || '$',
      phoneFormat: (locale.phone_format as string) || '(XXX) XXX-XXXX',
      addressFormat: (locale.address_format as string) || '{line1}, {city}, {state} {zip}',
      taxType: (locale.tax_type as string) || null,
      taxRate: (locale.tax_rate as number) || 0,
    },
    safetyMetrics: {
      incidentRateName: (metrics.incident_rate_name as string) || 'TRIR',
      incidentRateFullName: (metrics.incident_rate_full_name as string) || 'Total Recordable Incident Rate',
      incidentRateMultiplier: (metrics.incident_rate_multiplier as number) || 200000,
      secondaryRateName: (metrics.secondary_rate_name as string) || undefined,
      reportingBody: (metrics.reporting_body as string) || 'OSHA',
    },
    recordKeeping: {
      name: (rk.name as string) || 'OSHA 300 Log',
      featureKey: (rk.feature_key as string) || 'osha_log',
      fullName: (rk.full_name as string) || '',
    },
    complianceAudit: {
      name: (ca.name as string) || 'Mock OSHA Inspection',
    },
    certificationTypes: (data.certification_types as CertificationType[]) || US_DEFAULT.certificationTypes,
    documentTypes: (data.document_types as DocumentType[]) || US_DEFAULT.documentTypes,
    tradeTypes: (data.trade_types as TradeType[]) || US_DEFAULT.tradeTypes,
  };
}

export function JurisdictionProvider({ children }: { children: ReactNode }) {
  const companyQuery = useCompany();
  const company = companyQuery.data;
  const [config, setConfig] = useState<JurisdictionConfig>(US_DEFAULT);

  useEffect(() => {
    const code = (company as Record<string, unknown>)?.jurisdiction_code as string | undefined;
    const region = (company as Record<string, unknown>)?.jurisdiction_region as string | undefined;

    if (!code || code === 'US') {
      setConfig(US_DEFAULT);
      return;
    }

    const url = `${BASE_URL}/jurisdictions/${code}${region ? `?region=${region}` : ''}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load jurisdiction config');
        return res.json();
      })
      .then((data) => setConfig(mapApiResponse(data)))
      .catch(() => setConfig(US_DEFAULT));
  }, [(company as Record<string, unknown>)?.jurisdiction_code, (company as Record<string, unknown>)?.jurisdiction_region]);

  return (
    <JurisdictionCtx.Provider value={config}>
      {children}
    </JurisdictionCtx.Provider>
  );
}

export function useJurisdiction(): JurisdictionConfig {
  return useContext(JurisdictionCtx);
}
