import { cn } from '@/lib/utils';

interface ContentRendererProps {
  data: unknown;
  sectionKey?: string;
  depth?: number;
}

/** Well-known acronyms that should stay uppercase. */
const ACRONYMS: Record<string, string> = {
  ppe: 'PPE',
  osha: 'OSHA',
  jha: 'JHA',
  sssp: 'SSSP',
  cfr: 'CFR',
  ghs: 'GHS',
  sds: 'SDS',
  epa: 'EPA',
  dot: 'DOT',
  emr: 'EMR',
  cpr: 'CPR',
  aed: 'AED',
};

/** Format a snake_case or camelCase key into a readable heading. */
function formatKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .split(' ')
    .map((word) => ACRONYMS[word.toLowerCase()] ?? word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/** Risk level color mapping. */
function riskBadge(level: string) {
  const upper = level.toUpperCase();
  const colors: Record<string, string> = {
    HIGH: 'bg-[var(--fail-bg)] text-[var(--fail)] border-[var(--fail)]',
    MEDIUM: 'bg-[var(--warn-bg)] text-[var(--warn)] border-[var(--warn)]',
    LOW: 'bg-[var(--pass-bg)] text-[var(--pass)] border-[var(--pass)]',
  };
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
        colors[upper] || 'bg-muted text-[var(--concrete-600)] border-border'
      )}
    >
      {level}
    </span>
  );
}

/** Render OSHA references as orange badges. */
function oshaRef(value: string) {
  return (
    <span className="inline-flex items-center rounded-full border border-primary bg-[var(--machine-wash)] px-2 py-0.5 text-xs font-medium text-primary">
      {value}
    </span>
  );
}

/** Check if a value looks like an OSHA standard reference. */
function isOshaReference(key: string, _value: string): boolean {
  const oshaKeys = ['osha_standard', 'osha_reference'];
  return oshaKeys.includes(key.toLowerCase());
}

/** Check if a value is a risk level. */
function isRiskLevel(key: string, _value: string): boolean {
  return key.toLowerCase() === 'risk_level';
}

/** Render a string value, splitting on newlines. */
function StringContent({ value }: { value: string }) {
  const lines = value.split('\n');
  if (lines.length <= 1) {
    return <p className="text-sm leading-relaxed text-muted-foreground">{value}</p>;
  }
  return (
    <div className="space-y-2">
      {lines.map((line, i) => (
        <p key={i} className={cn('text-sm leading-relaxed text-muted-foreground', !line.trim() && 'h-3')}>
          {line}
        </p>
      ))}
    </div>
  );
}

/** Render an array of strings as a bullet list. */
function StringListContent({ items }: { items: string[] }) {
  return (
    <ul className="space-y-1.5 pl-1">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

/** Render an array of objects as a table. */
function ObjectTableContent({ items }: { items: Record<string, unknown>[] }) {
  if (items.length === 0) return null;

  const columns = Object.keys(items[0]);

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted">
            {columns.map((col) => (
              <th
                key={col}
                className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
              >
                {formatKey(col)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {items.map((row, rowIdx) => (
            <tr key={rowIdx} className="hover:bg-muted/50">
              {columns.map((col) => {
                const cellValue = row[col];
                const stringValue = String(cellValue ?? '');

                return (
                  <td key={col} className="px-3 py-2 text-muted-foreground">
                    {isRiskLevel(col, stringValue) ? (
                      riskBadge(stringValue)
                    ) : isOshaReference(col, stringValue) ? (
                      oshaRef(stringValue)
                    ) : (
                      stringValue
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Render a plain object (like emergency_procedures) as key-value pairs. */
function ObjectContent({ data, depth }: { data: Record<string, unknown>; depth: number }) {
  return (
    <div className="space-y-3">
      {Object.entries(data).map(([key, value]) => (
        <div key={key}>
          <h4 className="mb-1 text-sm font-semibold text-[var(--concrete-600)]">
            {formatKey(key)}
          </h4>
          <ContentRenderer data={value} sectionKey={key} depth={depth + 1} />
        </div>
      ))}
    </div>
  );
}

/**
 * Recursive content renderer that handles the structured JSON output
 * from the SafetyForge backend generation service.
 *
 * Supports:
 * - string: paragraphs (split on \n)
 * - string[]: bullet list
 * - object[]: table with column headers from object keys
 * - object with known keys: section headings with recursive content
 * - nested objects: recurse
 */
export function ContentRenderer({ data, sectionKey, depth = 0 }: ContentRendererProps) {
  // Null / undefined
  if (data === null || data === undefined) {
    return <p className="text-sm italic text-muted-foreground">No content</p>;
  }

  // String
  if (typeof data === 'string') {
    if (sectionKey && isOshaReference(sectionKey, data)) {
      return oshaRef(data);
    }
    if (sectionKey && isRiskLevel(sectionKey, data)) {
      return riskBadge(data);
    }
    return <StringContent value={data} />;
  }

  // Number / boolean
  if (typeof data === 'number' || typeof data === 'boolean') {
    return <p className="text-sm text-muted-foreground">{String(data)}</p>;
  }

  // Array
  if (Array.isArray(data)) {
    if (data.length === 0) {
      return <p className="text-sm italic text-muted-foreground">Empty</p>;
    }

    // Array of strings
    if (typeof data[0] === 'string') {
      return <StringListContent items={data as string[]} />;
    }

    // Array of objects
    if (typeof data[0] === 'object' && data[0] !== null) {
      return <ObjectTableContent items={data as Record<string, unknown>[]} />;
    }

    // Fallback: render each item
    return (
      <div className="space-y-2">
        {data.map((item, i) => (
          <ContentRenderer key={i} data={item} depth={depth + 1} />
        ))}
      </div>
    );
  }

  // Object
  if (typeof data === 'object') {
    return <ObjectContent data={data as Record<string, unknown>} depth={depth} />;
  }

  return <p className="text-sm text-muted-foreground">{String(data)}</p>;
}
