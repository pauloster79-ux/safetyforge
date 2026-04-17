import { useCallback, useEffect, useRef, useState } from 'react';
import { Pencil, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { formatCents } from '@/lib/format';
import { cn } from '@/lib/utils';

interface EditableCellProps {
  value: string | number | null;
  onSave: (newValue: string | number) => Promise<void>;
  type?: 'text' | 'number' | 'currency' | 'percent';
  formatDisplay?: (v: unknown) => string;
  className?: string;
  disabled?: boolean;
}

function defaultFormat(value: unknown, type: string): string {
  if (value === null || value === undefined || value === '') return '--';
  if (type === 'currency') return formatCents(Number(value));
  if (type === 'percent') return `${value}%`;
  return String(value);
}

/**
 * Inline-editable cell component.
 *
 * Display mode: shows formatted value with a subtle pencil icon on hover.
 * Edit mode: an Input field; Enter/blur saves, Escape cancels.
 */
export function EditableCell({
  value,
  onSave,
  type = 'text',
  formatDisplay,
  className,
  disabled = false,
}: EditableCellProps) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editValue, setEditValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // When entering edit mode, populate the input with the raw editable value
  const enterEdit = useCallback(() => {
    if (disabled || saving) return;
    let raw: string;
    if (type === 'currency') {
      // Convert cents to dollars for editing
      raw = value != null ? String(Number(value) / 100) : '';
    } else {
      raw = value != null ? String(value) : '';
    }
    setEditValue(raw);
    setEditing(true);
  }, [disabled, saving, type, value]);

  // Auto-focus and select text when editing starts
  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const cancel = useCallback(() => {
    setEditing(false);
  }, []);

  const save = useCallback(async () => {
    const trimmed = editValue.trim();

    // Determine the value to save
    let saveValue: string | number;
    if (type === 'number' || type === 'currency' || type === 'percent') {
      const num = Number(trimmed);
      if (trimmed === '' || isNaN(num)) {
        // Revert on invalid number
        setEditing(false);
        return;
      }
      saveValue = type === 'currency' ? Math.round(num * 100) : num;
    } else {
      saveValue = trimmed;
    }

    // Skip save if value hasn't changed
    if (saveValue === value) {
      setEditing(false);
      return;
    }

    setSaving(true);
    try {
      await onSave(saveValue);
    } finally {
      setSaving(false);
      setEditing(false);
    }
  }, [editValue, type, value, onSave]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        save();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        cancel();
      }
    },
    [save, cancel],
  );

  if (editing) {
    return (
      <div className={cn('flex items-center gap-1', className)}>
        <Input
          ref={inputRef}
          type={type === 'text' ? 'text' : 'number'}
          step={type === 'currency' ? '0.01' : type === 'percent' ? '1' : 'any'}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={save}
          onKeyDown={handleKeyDown}
          className="h-7 w-full min-w-[60px] px-1.5 text-sm"
          disabled={saving}
        />
        {saving && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />}
      </div>
    );
  }

  const display = formatDisplay
    ? formatDisplay(value)
    : defaultFormat(value, type);

  return (
    <span
      className={cn(
        'group/cell inline-flex cursor-pointer items-center gap-1 rounded px-1 -mx-1 transition-colors hover:bg-muted/60',
        disabled && 'cursor-default hover:bg-transparent',
        className,
      )}
      onClick={enterEdit}
    >
      <span className="truncate">{display}</span>
      {!disabled && (
        <Pencil className="h-3 w-3 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover/cell:opacity-100" />
      )}
    </span>
  );
}
