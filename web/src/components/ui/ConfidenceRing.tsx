import { cn } from '../../lib/utils';

interface ConfidenceRingProps {
  value: number; // 0-1
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

const sizeConfig = {
  sm: { size: 32, strokeWidth: 3, fontSize: 'text-xs' },
  md: { size: 48, strokeWidth: 4, fontSize: 'text-sm' },
  lg: { size: 64, strokeWidth: 5, fontSize: 'text-base' },
};

const RADIUS = 16;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function ConfidenceRing({ value = 0, size = 'md', showLabel = true, className }: ConfidenceRingProps) {
  const { size: ringSize, strokeWidth, fontSize } = sizeConfig[size];
  const clampedValue = Math.max(0, Math.min(1, value));
  const offset = CIRCUMFERENCE * (1 - clampedValue);

  // Color based on confidence level
  let strokeColor = 'var(--sell)';
  if (clampedValue >= 0.7) strokeColor = 'var(--buy)';
  else if (clampedValue >= 0.4) strokeColor = 'var(--warn)';

  return (
    <div className={cn('inline-flex flex-col items-center gap-1', className)} style={{ width: ringSize, height: ringSize }}>
      <svg width={ringSize} height={ringSize} viewBox={`0 0 ${ringSize} ${ringSize}`} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={ringSize / 2}
          cy={ringSize / 2}
          r={RADIUS}
          fill="none"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={ringSize / 2}
          cy={ringSize / 2}
          r={RADIUS}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          style={{
            transition: 'stroke-dashoffset 500ms ease-out, stroke 300ms ease-out',
          }}
        />
      </svg>
      {showLabel && (
        <span className={cn(fontSize, 'font-medium font-mono', clampedValue >= 0.7 ? 'text-[var(--buy)]' : clampedValue >= 0.4 ? 'text-[var(--warn)]' : 'text-[var(--sell)]')}>
          {Math.round(clampedValue * 100)}%
        </span>
      )}
    </div>
  );
}