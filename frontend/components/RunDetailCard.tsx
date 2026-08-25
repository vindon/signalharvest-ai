'use client';

import type { PipelineRun, PipelineRunState } from '@/lib/types';
import { usePolling } from '@/lib/usePolling';
import { relativeTime } from '@/lib/format';
import { PipelineTrailExpanded } from './PipelineTrail';
import { Badge } from './Badge';

export default function RunDetailCard({ run }: { run: PipelineRun }) {
  const isRunning = run.status === 'running';
  // Only poll live per-stage state while the run is actually in progress —
  // a completed/failed run's own record already has the final counts, no
  // need to keep hitting a second endpoint for every historical run card.
  const { data: liveState } = usePolling<PipelineRunState>(
    `/pipeline/runs/${run.id}/state`,
    2000,
    null,
    isRunning
  );

  const counts = isRunning && liveState
    ? liveState
    : {
        signals_harvested: run.signals_harvested,
        signals_classified: run.signals_classified,
        signals_scored: run.signals_scored,
        leads_curated: run.leads_curated,
        digests_generated: run.digests_generated,
      };
  const lastCompletedStage = isRunning ? liveState?.last_completed_stage ?? null : 'publisher';

  const statusTone = run.status === 'completed' ? 'success' : run.status === 'failed' ? 'hot' : 'brand';

  return (
    <div className="panel" style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Badge tone={statusTone}>{run.status}</Badge>
            <span className="drawer-id mono">{run.id.slice(0, 8)}</span>
          </div>
          <div className="row-sub" style={{ marginTop: 6 }}>
            Started {relativeTime(run.started_at)}
            {run.completed_at ? ` · finished ${relativeTime(run.completed_at)}` : ''}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="stat-value" style={{ fontSize: 20 }}>{counts.leads_curated}</div>
          <div className="row-sub">leads curated</div>
        </div>
      </div>

      {run.error_message && (
        <div className="callout -error" style={{ marginBottom: 16 }}>{run.error_message}</div>
      )}

      <PipelineTrailExpanded status={run.status} lastCompletedStage={lastCompletedStage} counts={counts} />
    </div>
  );
}
