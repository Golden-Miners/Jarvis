import { Link } from 'react-router-dom';
import { ShieldX } from 'lucide-react';

export function ForbiddenPage() {
  return (
    <div className="min-h-screen bg-[var(--bg)] flex items-center justify-center p-4">
      <div className="text-center max-w-sm">
        <div className="w-16 h-16 rounded-full bg-[color-mix(in_oklch,var(--sell)_15%,transparent)] border border-[var(--sell)] flex items-center justify-center mx-auto mb-6">
          <ShieldX className="w-8 h-8 text-[var(--sell)]" aria-hidden="true" />
        </div>
        <h1 className="font-heading font-semibold text-2xl mb-2">Access denied</h1>
        <p className="text-[var(--muted)] mb-6">
          You don't have permission to access this page. Contact your administrator.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-[10px] bg-[var(--arc)] text-[var(--bg)] font-medium text-sm hover:opacity-90 transition-opacity"
        >
          Back to overview
        </Link>
      </div>
    </div>
  );
}
