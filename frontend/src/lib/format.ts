/**
 * Format integer cents as a dollar string.
 * e.g. 15000 → "$150.00", 180000 → "$1,800.00"
 */
export function formatCents(cents: number): string {
  const dollars = cents / 100;
  return dollars.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
