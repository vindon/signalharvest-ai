import type { PipelineRunStatus } from '@/lib/types';
import { CheckIcon, AlertTriangleIcon } from './icons';

const STAGES = [
  { key: 'sentinel', label: 'Harvest', desc: 'Pull signals from Reddit, Trends, CFPB, RSS' },
  { key: 'classifier', label: 'Classify', desc: 'Taxonomy category + intent via Claude' },
  { key: 'scorer', label: 'Score', desc: 'Velocity + intent + engagement, 0–100' },
  { key: 'curator', label: 'Curate', desc: 'Match scored signals to brand subscriptions' },
  { key: 'publisher', label: 'Publish', desc: 'Render + deliver per-brand digests' },
] as const;

type StageState = 'done' | 'active' | 'pending' | 'error';

function deriveStates(status: PipelineRunStatus, lastCompletedStage: string | null): StageState[] {
  const idx = STAGES.findIndex((s) => s.key === lastCompletedStage);
  return STAGES.map((stage, i) => {
    if (status === 'completed') return 'done';
    if (status === 'failed') {
      if (i < idx) return 'done';
      if (i === idx) return 'error';
      return 'pending';
    }
    // running
    if (i <= idx) return 'done';
    if (i === idx + 1) return 'active';
    return 'pending';
  });
}

export function PipelineTrailCompact({
  status,
  lastCompletedStage,
}: {
  status: PipelineRunStatus;
  lastCompletedStage: string | null;
}) {
  const states = deriveStates(status, lastCompletedStage);
  return (
    <div className="pipeline-trail" aria-label={`Pipeline ${status}`}>
      {STAGES.map((stage, i) => (
        <span key={stage.key} style={{ display: 'contents' }}>
          <span className={`pipeline-node -${states[i]}`} title={stage.label}>
            {states[i] === 'done' && <CheckIcon width={12} height={12} />}
            {states[i] === 'error' && <AlertTriangleIcon width={12} height={12} />}
            {states[i] !== 'done' && states[i] !== 'error' && i + 1}
          </span>
          {i < STAGES.length - 1 && (
            <span className={`pipeline-connector${states[i] === 'done' ? ' -done' : ''}`} />
          )}
        </span>
      ))}
    </div>
  );
}

export function PipelineTrailExpanded({
  status,
  lastCompletedStage,
  counts,
}: {
  status: PipelineRunStatus;
  lastCompletedStage: string | null;
  counts: {
    signals_harvested: number;
    signals_classified: number;
    signals_scored: number;
    leads_curated: number;
    digests_generated: number;
  };
}) {
  const states = deriveStates(status, lastCompletedStage);
  const countFor = (key: (typeof STAGES)[number]['key']): number | null => {
    switch (key) {
      case 'sentinel':
        return counts.signals_harvested;
      case 'classifier':
        return counts.signals_classified;
      case 'scorer':
        return counts.signals_scored;
      case 'curator':
        return counts.leads_curated;
      case 'publisher':
        return counts.digests_generated;
    }
  };
  return (
    <div className="pipeline-trail-labeled">
      {STAGES.map((stage, i) => (
        <div className="pipeline-step" key={stage.key}>
          <div className="pipeline-step-line">
            <span className={`pipeline-node -${states[i]}`}>
              {states[i] === 'done' && <CheckIcon width={12} height={12} />}
              {states[i] === 'error' && <AlertTriangleIcon width={12} height={12} />}
              {states[i] !== 'done' && states[i] !== 'error' && i + 1}
            </span>
            {i < STAGES.length - 1 && (
              <span className={`pipeline-step-connector${states[i] === 'done' ? ' -done' : ''}`} />
            )}
          </div>
          <div className="pipeline-step-body">
            <div className="pipeline-step-title">{stage.label}</div>
            <div className="pipeline-step-desc">
              {stage.desc}
              {(states[i] === 'done' || states[i] === 'active') && countFor(stage.key) !== null && (
                <> — {countFor(stage.key)}</>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
