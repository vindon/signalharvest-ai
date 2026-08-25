'use client';

import type { ScoredSignal } from '@/lib/types';
import { relativeTime, sourceLabel, intentLabel, categoryLabel, verticalColor } from '@/lib/format';
import { Badge, tierTone, tierLabel } from './Badge';
import { CloseIcon } from './icons';

export default function SignalDrawer({
  signal,
  onClose,
}: {
  signal: ScoredSignal;
  onClose: () => void;
}) {
  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer" role="dialog" aria-label="Signal detail">
        <div className="drawer-head">
          <div>
            <div className="page-title display" style={{ fontSize: 16 }}>
              {signal.title || categoryLabel(signal.category)}
            </div>
            <div className="drawer-id mono">{signal.id.slice(0, 8)}</div>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close">
            <CloseIcon width={16} height={16} />
          </button>
        </div>

        <div className="drawer-body">
          <div className="drawer-section">
            <div className="drawer-badges">
              <Badge tone={tierTone(signal.tier)}>{tierLabel(signal.tier)} · {signal.score}</Badge>
              <span className="category-chip">
                <span className="category-dot" style={{ background: verticalColor(signal.category) }} />
                {categoryLabel(signal.category)}
              </span>
              <Badge tone="neutral">{intentLabel(signal.intent_type)}</Badge>
            </div>
          </div>

          <div className="drawer-section">
            <div className="drawer-section-label">Content</div>
            <div className="drawer-text">{signal.text}</div>
          </div>

          {signal.keywords.length > 0 && (
            <div className="drawer-section">
              <div className="drawer-section-label">Keywords</div>
              <div className="drawer-badges">
                {signal.keywords.map((k) => (
                  <Badge key={k} tone="neutral">{k}</Badge>
                ))}
              </div>
            </div>
          )}

          {signal.competitor_mentions.length > 0 && (
            <div className="drawer-section">
              <div className="drawer-section-label">Competitor mentions</div>
              <div className="drawer-badges">
                {signal.competitor_mentions.map((c) => (
                  <Badge key={c} tone="warm">{c}</Badge>
                ))}
              </div>
            </div>
          )}

          <div className="drawer-section">
            <div className="drawer-section-label">Scoring</div>
            <div className="drawer-text" style={{ fontSize: 12.5 }}>
              Velocity 24h: {signal.velocity_delta_24h > 0 ? '+' : ''}{signal.velocity_delta_24h.toFixed(0)}%
              <br />
              Velocity 7d: {signal.velocity_delta_7d > 0 ? '+' : ''}{signal.velocity_delta_7d.toFixed(0)}%
              <br />
              Engagement: {(signal.engagement_score * 100).toFixed(0)}%
              <br />
              Classification confidence: {(signal.classification_confidence * 100).toFixed(0)}%
            </div>
          </div>

          <div className="drawer-section">
            <div className="drawer-section-label">Source</div>
            <div className="drawer-text" style={{ fontSize: 12.5 }}>
              {sourceLabel(signal.source)}
              {signal.geography ? ` · ${signal.geography}` : ''}
              <br />
              Harvested {relativeTime(signal.harvested_at)}
            </div>
          </div>
        </div>

        {signal.url && (
          <div className="drawer-footer">
            <a href={signal.url} target="_blank" rel="noreferrer" className="btn btn-primary">
              View original
            </a>
          </div>
        )}
      </div>
    </>
  );
}
