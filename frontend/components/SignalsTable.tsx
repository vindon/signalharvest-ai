'use client';

import { useState } from 'react';
import type { ScoredSignal, SignalsResponse } from '@/lib/types';
import { usePolling } from '@/lib/usePolling';
import { relativeTime, sourceLabel, categoryLabel, verticalColor } from '@/lib/format';
import { Badge, tierTone, tierLabel } from './Badge';
import { ChevronRightIcon, EmptyIcon } from './icons';
import SignalDrawer from './SignalDrawer';

const SOURCES = ['reddit', 'google_trends', 'cfpb', 'rss'];
const TIERS: Array<ScoredSignal['tier']> = ['hot', 'warm', 'watch'];

export default function SignalsTable({
  hours = 24,
  limit,
  showFilters = false,
  initialData = null,
}: {
  hours?: number;
  limit?: number;
  showFilters?: boolean;
  initialData?: SignalsResponse | null;
}) {
  const [source, setSource] = useState<string | null>(null);
  const [tier, setTier] = useState<string | null>(null);
  const [selected, setSelected] = useState<ScoredSignal | null>(null);

  const params = new URLSearchParams({ hours: String(hours) });
  if (source) params.set('source', source);
  if (tier) params.set('tier', tier);
  const path = `/signals?${params.toString()}`;

  const { data, error, loading } = usePolling<SignalsResponse>(
    path,
    6000,
    source === null && tier === null ? initialData : null
  );

  let signals = data?.signals ?? [];
  if (limit) signals = signals.slice(0, limit);

  return (
    <div className="panel">
      {showFilters && (
        <div style={{ padding: '14px 18px 0' }}>
          <div className="filter-row">
            <button className={`filter-pill${source === null ? ' -active' : ''}`} onClick={() => setSource(null)}>
              All sources
            </button>
            {SOURCES.map((s) => (
              <button
                key={s}
                className={`filter-pill${source === s ? ' -active' : ''}`}
                onClick={() => setSource(s === source ? null : s)}
              >
                {sourceLabel(s)}
              </button>
            ))}
            <span style={{ width: 1, background: 'var(--border)', margin: '0 4px' }} />
            <button className={`filter-pill${tier === null ? ' -active' : ''}`} onClick={() => setTier(null)}>
              All tiers
            </button>
            {TIERS.map((t) => (
              <button
                key={t}
                className={`filter-pill${tier === t ? ' -active' : ''}`}
                onClick={() => setTier(t === tier ? null : t)}
              >
                {tierLabel(t)}
              </button>
            ))}
          </div>
        </div>
      )}

      <div
        className="table-head"
        style={{ gridTemplateColumns: '1.5fr 175px 120px 90px 70px 18px' }}
      >
        <div>Signal</div>
        <div>Category</div>
        <div>Source</div>
        <div>Tier</div>
        <div style={{ textAlign: 'right' }}>Score</div>
        <div></div>
      </div>

      {loading && signals.length === 0 && (
        <div className="empty-state">Loading signals…</div>
      )}

      {!loading && error && signals.length === 0 && (
        <div className="empty-state">
          <EmptyIcon width={32} height={32} style={{ margin: '0 auto 10px' }} />
          <div className="empty-state-title">Couldn&apos;t load signals</div>
          {error}
        </div>
      )}

      {!loading && !error && signals.length === 0 && (
        <div className="empty-state">
          <EmptyIcon width={32} height={32} style={{ margin: '0 auto 10px' }} />
          <div className="empty-state-title">No signals in this window</div>
          Trigger a pipeline run from the Run pipeline page to harvest fresh signals.
        </div>
      )}

      {signals.map((s) => (
        <button
          key={s.id}
          className={`table-row${selected?.id === s.id ? ' -selected' : ''}`}
          style={{ gridTemplateColumns: '1.5fr 175px 120px 90px 70px 18px' }}
          onClick={() => setSelected(s)}
        >
          <div>
            <div className="row-title">{s.title || s.text.slice(0, 80)}</div>
            <div className="row-sub">{s.text.slice(0, 90)}</div>
          </div>
          <div>
            <span className="category-chip">
              <span className="category-dot" style={{ background: verticalColor(s.category) }} />
              {categoryLabel(s.category)}
            </span>
          </div>
          <div style={{ fontSize: 12.5, color: 'var(--grey-soft)' }}>{sourceLabel(s.source)}</div>
          <div>
            <Badge tone={tierTone(s.tier)}>{tierLabel(s.tier)}</Badge>
          </div>
          <div className="score-cell">{s.score}</div>
          <div className="chev">
            <ChevronRightIcon width={16} height={16} />
          </div>
        </button>
      ))}

      {selected && <SignalDrawer signal={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
