/**
 * Jurisdiction-aware formatting utilities.
 *
 * All formatting of dates, currencies, temperatures, heights, and phone
 * numbers goes through these helpers so the UI adapts to the company's
 * jurisdiction automatically.
 */

import type { JurisdictionConfig } from '@/contexts/JurisdictionContext';

/**
 * Format a date string or Date object according to the jurisdiction's locale.
 */
export function formatDate(
  date: string | Date | null | undefined,
  jurisdiction: JurisdictionConfig,
): string {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return String(date);

  const lang = jurisdiction.locale.languages[0] || 'en-US';
  return d.toLocaleDateString(lang, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

/**
 * Format a date with time according to the jurisdiction's locale.
 */
export function formatDateTime(
  date: string | Date | null | undefined,
  jurisdiction: JurisdictionConfig,
): string {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return String(date);

  const lang = jurisdiction.locale.languages[0] || 'en-US';
  return d.toLocaleString(lang, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format a currency amount according to the jurisdiction's locale.
 */
export function formatCurrency(
  amount: number,
  jurisdiction: JurisdictionConfig,
): string {
  const lang = jurisdiction.locale.languages[0] || 'en-US';
  return new Intl.NumberFormat(lang, {
    style: 'currency',
    currency: jurisdiction.locale.currency,
  }).format(amount);
}

/**
 * Format a temperature value. Internal storage is always Celsius.
 * Converts to Fahrenheit if the jurisdiction uses imperial.
 */
export function formatTemperature(
  celsius: number,
  jurisdiction: JurisdictionConfig,
): string {
  if (jurisdiction.locale.temperatureUnit === 'fahrenheit') {
    const f = Math.round(celsius * 9 / 5 + 32);
    return `${f}\u00B0F`;
  }
  return `${Math.round(celsius)}\u00B0C`;
}

/**
 * Format a height value. Internal storage is always metres.
 * Converts to feet if the jurisdiction uses imperial.
 */
export function formatHeight(
  metres: number,
  jurisdiction: JurisdictionConfig,
): string {
  if (jurisdiction.locale.measurementSystem === 'imperial') {
    const ft = Math.round(metres * 3.281);
    return `${ft} ft`;
  }
  return `${metres} m`;
}

/**
 * Format a distance value. Internal storage is always metres.
 */
export function formatDistance(
  metres: number,
  jurisdiction: JurisdictionConfig,
): string {
  if (jurisdiction.locale.measurementSystem === 'imperial') {
    if (metres >= 1609) {
      return `${(metres / 1609.344).toFixed(1)} mi`;
    }
    return `${Math.round(metres * 3.281)} ft`;
  }
  if (metres >= 1000) {
    return `${(metres / 1000).toFixed(1)} km`;
  }
  return `${Math.round(metres)} m`;
}

/**
 * Get the phone number placeholder for the jurisdiction.
 */
export function getPhonePlaceholder(jurisdiction: JurisdictionConfig): string {
  return jurisdiction.locale.phoneFormat;
}

/**
 * Get the address format description for the jurisdiction.
 */
export function getAddressPlaceholder(jurisdiction: JurisdictionConfig): string {
  const fmt = jurisdiction.locale.addressFormat;
  // Convert template vars to human-readable hints
  return fmt
    .replace('{line1}', '123 Main St')
    .replace('{line2}', '')
    .replace('{city}', 'City')
    .replace('{state}', jurisdiction.code === 'UK' ? 'County' : 'State/Province')
    .replace('{zip}', jurisdiction.code === 'UK' ? 'Postcode' : 'Postal Code')
    .replace('{postcode}', 'Postcode')
    .replace('{county}', 'County')
    .replace(', ,', ',')
    .replace(',,', ',');
}

/**
 * Get the label for the tax ID field based on jurisdiction.
 */
export function getTaxIdLabel(jurisdiction: JurisdictionConfig): string {
  switch (jurisdiction.code) {
    case 'US': return 'EIN (Employer Identification Number)';
    case 'UK': return 'UTR (Unique Taxpayer Reference)';
    case 'AU': return 'ABN (Australian Business Number)';
    case 'CA': return 'Business Number (BN)';
    default: return 'Tax ID';
  }
}

/**
 * Get the tax ID placeholder based on jurisdiction.
 */
export function getTaxIdPlaceholder(jurisdiction: JurisdictionConfig): string {
  switch (jurisdiction.code) {
    case 'US': return '12-3456789';
    case 'UK': return '1234567890';
    case 'AU': return '12 345 678 901';
    case 'CA': return '123456789';
    default: return '';
  }
}

/**
 * Get the license number label based on jurisdiction.
 */
export function getLicenseLabel(jurisdiction: JurisdictionConfig): string {
  switch (jurisdiction.code) {
    case 'US': return 'Contractor License Number';
    case 'UK': return 'Company Registration Number';
    case 'AU': return 'Builder Licence Number';
    case 'CA': return 'Business Licence Number';
    default: return 'License/Registration Number';
  }
}
