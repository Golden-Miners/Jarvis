export function SettingsPage() {
  return (
    <div className="p-4 pb-20 md:pb-4 space-y-4">
      <h1 className="font-heading font-semibold text-xl">Settings</h1>
      <div className="glass rounded-[16px] p-8 text-center">
        <p className="text-[var(--muted)]">Settings — Instrument configuration, thresholds, users &amp; audit log</p>
        <p className="text-xs text-[var(--muted)] mt-2">Available to OWNER role only.</p>
      </div>
    </div>
  );
}