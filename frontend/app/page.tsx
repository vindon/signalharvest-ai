import { apiFetch } from '@/lib/api';
import type { RunsResponse, SignalsResponse } from '@/lib/types';
import OverviewStats from '@/components/OverviewStats';
import SignalsTable from '@/components/SignalsTable';

export default async function OverviewPage() {
  const [runs, signals] = await Promise.all([
    apiFetch<RunsResponse>('/api/v1/pipeline/runs?limit=5').catch(() => null),
    apiFetch<SignalsResponse>('/api/v1/signals?hours=24').catch(() => null),
  ]);

  return (
    <div className="content">
      <div className="content-head">
        <div>
          <h1 className="page-title display">Overview</h1>
          <div className="page-sub">Live status of the SignalHarvest lead intelligence pipeline</div>
        </div>
      </div>

      <OverviewStats initialRuns={runs} initialSignals={signals} />

      <div className="panel-head" style={{ border: 'none', padding: '0 0 12px' }}>
        <div className="panel-title">Recent signals</div>
      </div>
      <SignalsTable hours={24} limit={8} initialData={signals} />
    </div>
  );
}
