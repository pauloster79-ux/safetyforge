import { useLocale } from '@/lib/i18n';
import { cn } from '@/lib/utils';

interface LocaleToggleProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LocaleToggle({ size = 'sm', className }: LocaleToggleProps) {
  const { locale, setLocale } = useLocale();

  const sizeClasses = {
    sm: 'h-8 text-xs',
    md: 'h-10 text-sm',
    lg: 'h-12 text-base',
  };

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-lg border border-border bg-muted p-0.5',
        className
      )}
    >
      <button
        type="button"
        onClick={() => setLocale('en')}
        className={cn(
          'flex items-center justify-center rounded-md px-3 font-medium transition-all',
          sizeClasses[size],
          locale === 'en'
            ? 'bg-white text-foreground shadow-sm'
            : 'text-muted-foreground hover:text-[var(--concrete-600)]'
        )}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLocale('es')}
        className={cn(
          'flex items-center justify-center rounded-md px-3 font-medium transition-all',
          sizeClasses[size],
          locale === 'es'
            ? 'bg-white text-foreground shadow-sm'
            : 'text-muted-foreground hover:text-[var(--concrete-600)]'
        )}
      >
        ES
      </button>
    </div>
  );
}
