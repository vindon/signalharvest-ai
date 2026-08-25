'use client';

import type { RunsResponse, SignalsResponse } from '@/lib/types';
import { usePolling } from '@/lib/usePolling';

export default function OverviewStats({
  initialRuns,
  initialSignals,
}: {
  initialRuns: RunsResponse | null;
  initialSignals: SignalsResponse | null;
}) {
  const { data: runsData } = usePolling<RunsResponse>('/pipeline/runs?limit=5', 8000, initialRuns);
  const { data: signalsData } = usePolling<SignalsResponse>('/signals?hours=24', 15000, initialSignals);

  const runs = runsData?.runs ?? [];
  const signals = signalsData?.signals ?? [];
  const lastRun = runs[0];

  const hotCount = signals.filter((s) => s.tier === 'hot').length;
  const warmCount = signals.filter((s) => s.tier === 'warm').length;
  const completedRuns = runs.filter((r) => r.status === 'completed').length;

  return (
    <div className="stat-grid">
      <div className="stat-card">
        <div className="stat-label">Signals, 24h</div>
        <div className="stat-value">{signals.length}</div>
        <div className="stat-sub">{hotCount} hot · {warmCount} warm</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Last run status</div>
        <div className="stat-value" style={{ fontSize: 18, textTransform: 'capitalize' }}>
          {lastRun ? lastRun.status : 'No runs yet'}
        </div>
        <div className="stat-sub">
          {lastRun ? `${lastRun.leads_curated} leads curated` : 'Trigger one from Run pipeline'}
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Digests delivered</div>
        <div className="stat-value">{lastRun?.digests_delivered ?? 0}</div>
        <div className="stat-sub">most recent run</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Runs, last 5</div>
        <div className="stat-value">{completedRuns}/{runs.length || 0}</div>
        <div className="stat-sub">completed successfully</div>
      </div>
    </div>
  );
}
