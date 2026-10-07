import { cn } from '../../lib/utils';

interface StatusRingProps {
  active?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  ariaLabel?: string;
}

const sizeClasses = {
  sm: 'w-6 h-6',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

export function StatusRing({ active = false, size = 'md', className, ariaLabel }: StatusRingProps) {
  return (
    <span
      className={cn(
        'relative inline-flex items-center justify-center rounded-full border-2 transition-all duration-300',
        sizeClasses[size],
        active
          ? 'border-[var(--arc)] bg-[var(--arc)]/15 status-ring-active'
          : 'border-[var(--border)] bg-[var(--surface)]',
        className
      )}
      role="status"
      aria-label={ariaLabel || (active ? 'System active' : 'System idle')}
    >
      <span
        className={cn(
          'absolute inset-0 rounded-full',
          active ? 'bg-[var(--arc)]/30' : 'bg-transparent'
        )}
        aria-hidden="true"
      />
      <span className="relative z-10" aria-hidden="true">
        {active ? (
          <svg className="w-full h-full text-[var(--arc)]" fill="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="6" />
          </svg>
        ) : (
          <svg className="w-1/2 h-1/2 text-[var(--muted)]" fill="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="4" />
          </svg>
        )}
      </span>
    </span>
  );
}