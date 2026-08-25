import type { SignalTier, DigestStatus } from '@/lib/types';

export function Badge({
  tone,
  children,
}: {
  tone: 'hot' | 'warm' | 'watch' | 'success' | 'neutral' | 'brand';
  children: React.ReactNode;
}) {
  return (
    <span className={`badge -${tone}`}>
      <span className="badge-dot" />
      {children}
    </span>
  );
}

export function tierTone(tier: SignalTier): 'hot' | 'warm' | 'watch' {
  if (tier === 'hot') return 'hot';
  if (tier === 'warm') return 'warm';
  return 'watch';
}

export function tierLabel(tier: SignalTier): string {
  if (tier === 'hot') return 'Hot';
  if (tier === 'warm') return 'Warm';
  return 'Watch';
}

export function digestStatusTone(status: DigestStatus): 'success' | 'warm' | 'hot' | 'neutral' {
  if (status === 'delivered') return 'success';
  if (status === 'pending') return 'warm';
  if (status === 'failed') return 'hot';
  return 'neutral';
}

export function digestStatusLabel(status: DigestStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
