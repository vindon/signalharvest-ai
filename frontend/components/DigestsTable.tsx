'use client';

import { useState } from 'react';
import type { DigestsResponse } from '@/lib/types';
import { usePolling } from '@/lib/usePolling';
import { relativeTime } from '@/lib/format';
import { Badge, digestStatusTone, digestStatusLabel } from './Badge';
import { ChevronRightIcon, EmptyIcon } from './icons';
import DigestDrawer from './DigestDrawer';

export default function DigestsTable({ initialData }: { initialData: DigestsResponse | null }) {
  const { data, loading } = usePolling<DigestsResponse>('/digests', 10000, initialData);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const digests = data?.digests ?? [];

  return (
    <div className="panel">
      <div className="table-head" style={{ gridTemplateColumns: '1.4fr 110px 100px 100px 18px' }}>
        <div>Brand</div>
        <div>Status</div>
        <div style={{ textAlign: 'right' }}>Leads</div>
        <div style={{ textAlign: 'right' }}>Generated</div>
        <div></div>
      </div>

      {loading && digests.length === 0 && <div className="empty-state">Loading digests…</div>}

      {!loading && digests.length === 0 && (
        <div className="empty-state">
          <EmptyIcon width={32} height={32} style={{ margin: '0 auto 10px' }} />
          <div className="empty-state-title">No digests yet</div>
          Digests appear here after a pipeline run curates leads for at least one active brand.
        </div>
      )}

      {digests.map((d) => (
        <button
          key={d.id}
          className={`table-row${selectedId === d.id ? ' -selected' : ''}`}
          style={{ gridTemplateColumns: '1.4fr 110px 100px 100px 18px' }}
          onClick={() => setSelectedId(d.id)}
        >
          <div>
            <div className="row-title">{d.brand_name}</div>
            <div className="row-sub">
              {d.summary.hot_count} hot · {d.summary.warm_count} warm · {d.summary.watch_count} watch
            </div>
          </div>
          <div>
            <Badge tone={digestStatusTone(d.status)}>{digestStatusLabel(d.status)}</Badge>
          </div>
          <div className="score-cell">{d.lead_count}</div>
          <div className="time-cell">{relativeTime(d.generated_at)}</div>
          <div className="chev">
            <ChevronRightIcon width={16} height={16} />
          </div>
        </button>
      ))}

      {selectedId && <DigestDrawer digestId={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  );
}
