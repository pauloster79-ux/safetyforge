import { cn } from '@/lib/utils';

interface ComplianceRingProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

function getScoreColor(score: number): { stroke: string; text: string; bg: string } {
  if (score <= 40) return { stroke: 'stroke-[var(--fail)]', text: 'text-[var(--fail)]', bg: 'bg-[var(--fail-bg)]' };
  if (score <= 70) return { stroke: 'stroke-[var(--warn)]', text: 'text-[var(--warn)]', bg: 'bg-[var(--warn-bg)]' };
  return { stroke: 'stroke-[var(--pass)]', text: 'text-[var(--pass)]', bg: 'bg-[var(--pass-bg)]' };
}

const SIZES = {
  sm: { container: 'h-10 w-10', radius: 16, strokeWidth: 3, textClass: 'text-[10px] font-bold' },
  md: { container: 'h-16 w-16', radius: 26, strokeWidth: 4, textClass: 'text-sm font-bold' },
  lg: { container: 'h-24 w-24', radius: 40, strokeWidth: 5, textClass: 'text-xl font-bold' },
};

export function ComplianceRing({ score, size = 'md', className }: ComplianceRingProps) {
  const colors = getScoreColor(score);
  const config = SIZES[size];
  const circumference = 2 * Math.PI * config.radius;
  const dashOffset = circumference - (score / 100) * circumference;
  const viewBoxSize = (config.radius + config.strokeWidth) * 2;
  const center = viewBoxSize / 2;

  return (
    <div className={cn('relative inline-flex items-center justify-center', config.container, className)}>
      <svg
        className="rotate-[-90deg]"
        width="100%"
        height="100%"
        viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
      >
        <circle
          cx={center}
          cy={center}
          r={config.radius}
          fill="none"
          className="stroke-muted"
          strokeWidth={config.strokeWidth}
        />
        <circle
          cx={center}
          cy={center}
          r={config.radius}
          fill="none"
          className={colors.stroke}
          strokeWidth={config.strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
        />
      </svg>
      <span className={cn('absolute', config.textClass, colors.text)}>
        {score}
      </span>
    </div>
  );
}

export function getComplianceLabel(score: number): string {
  if (score <= 40) return 'Critical';
  if (score <= 70) return 'Needs Attention';
  return 'Good';
}
