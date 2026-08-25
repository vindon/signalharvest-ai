'use client';

import { useEffect, useState } from 'react';
import type { DigestDetail } from '@/lib/types';
import { relativeTime, categoryLabel, verticalColor } from '@/lib/format';
import { Badge, tierTone, tierLabel, digestStatusTone, digestStatusLabel } from './Badge';
import { CloseIcon, DownloadIcon } from './icons';

export default function DigestDrawer({ digestId, onClose }: { digestId: string; onClose: () => void }) {
  // Keyed on digestId (below in state) rather than a separate boolean:
  // resetting detail to null on digestId change is itself the loading
  // signal, so there's nothing to set synchronously in the effect body.
  const [state, setState] = useState<{ id: string; detail: DigestDetail | null }>({
    id: digestId,
    detail: null,
  });
  const loading = state.id !== digestId || state.detail === null;
  const detail = state.id === digestId ? state.detail : null;

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/proxy/digests/${digestId}`)
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled) setState({ id: digestId, detail: data as DigestDetail });
      });
    return () => {
      cancelled = true;
    };
  }, [digestId]);

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer" role="dialog" aria-label="Digest detail">
        <div className="drawer-head">
          <div>
            <div className="page-title display" style={{ fontSize: 16 }}>
              {detail?.brand_name || 'Digest'}
            </div>
            <div className="drawer-id mono">{digestId.slice(0, 8)}</div>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close">
            <CloseIcon width={16} height={16} />
          </button>
        </div>

        <div className="drawer-body">
          {loading && <div className="drawer-empty">Loading…</div>}
          {!loading && detail && (
            <>
              <div className="drawer-section">
                <div className="drawer-badges">
                  <Badge tone={digestStatusTone(detail.status)}>{digestStatusLabel(detail.status)}</Badge>
                  <Badge tone="neutral">{detail.lead_count} lead{detail.lead_count === 1 ? '' : 's'}</Badge>
                </div>
              </div>

              <div className="drawer-section">
                <div className="drawer-section-label">Leads</div>
                {detail.leads.length === 0 && <div className="drawer-empty">No leads in this digest.</div>}
                {detail.leads.map((lead) => (
                  <div key={lead.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', gap: 6, marginBottom: 6, flexWrap: 'wrap' }}>
                      <Badge tone={tierTone(lead.tier)}>{tierLabel(lead.tier)} · {lead.score}</Badge>
                      <span className="category-chip">
                        <span className="category-dot" style={{ background: verticalColor(lead.category) }} />
                        {categoryLabel(lead.category)}
                      </span>
                    </div>
                    <div className="row-title" style={{ fontSize: 13 }}>{lead.title || lead.text.slice(0, 80)}</div>
                    <div className="row-sub" style={{ marginTop: 4, whiteSpace: 'normal' }}>{lead.match_reason}</div>
                    <div style={{ fontSize: 11, color: 'var(--grey-soft)', marginTop: 4 }}>
                      {relativeTime(lead.harvested_at)}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="drawer-footer">
          <a href={`/api/proxy/digests/${digestId}/download`} className="btn btn-primary" download>
            <DownloadIcon width={15} height={15} />
            Download CSV
          </a>
        </div>
      </div>
    </>
  );
}
