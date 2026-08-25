export function relativeTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const diffSec = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.round(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  return `${diffDay}d ago`;
}

const SOURCE_LABELS: Record<string, string> = {
  reddit: 'Reddit',
  google_trends: 'Google Trends',
  cfpb: 'CFPB',
  rss: 'RSS',
};

export function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source;
}

const INTENT_LABELS: Record<string, string> = {
  complaint: 'Complaint',
  comparison: 'Comparison shopping',
  purchase_ready: 'Purchase-ready',
  churn_risk: 'Churn risk',
  information: 'Information seeking',
  unknown: 'Unclassified',
};

export function intentLabel(intent: string): string {
  return INTENT_LABELS[intent] ?? intent;
}

// Categories are snake_case like "telecom_mobile" or "fintech_credit_card" —
// split on the first underscore into a vertical (small caps in the UI) and
// the specific segment, title-cased.
export function categoryParts(category: string): { vertical: string; segment: string } {
  const idx = category.indexOf('_');
  if (idx === -1) return { vertical: category, segment: '' };
  const vertical = category.slice(0, idx);
  const segment = category
    .slice(idx + 1)
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
  return { vertical, segment };
}

export function categoryLabel(category: string): string {
  const { vertical, segment } = categoryParts(category);
  const v = vertical.charAt(0).toUpperCase() + vertical.slice(1);
  return segment ? `${v} · ${segment}` : v;
}

const VERTICAL_COLORS: Record<string, string> = {
  telecom: '#4F46E5',
  fintech: '#059669',
  home: '#D97706',
  dtc: '#DB2777',
  saas: '#0891B2',
  health: '#DC2626',
  auto: '#7C3AED',
  travel: '#EA580C',
  edu: '#2563EB',
  energy: '#65A30D',
  realestate: '#9333EA',
};

export function verticalColor(category: string): string {
  const { vertical } = categoryParts(category);
  return VERTICAL_COLORS[vertical] ?? '#6B7280';
}
