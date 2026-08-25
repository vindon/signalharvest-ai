'use client';

import { useState } from 'react';
import type { RunsResponse } from '@/lib/types';
import { usePolling, requestRefresh } from '@/lib/usePolling';
import { PlayIcon } from './icons';
import RunDetailCard from './RunDetailCard';

export default function RunPipelinePanel({ initialData }: { initialData: RunsResponse | null }) {
  const { data } = usePolling<RunsResponse>('/pipeline/runs?limit=10', 4000, initialData);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runs = data?.runs ?? [];
  const anyRunning = runs.some((r) => r.status === 'running');

  async function trigger() {
    setError(null);
    setTriggering(true);
    try {
      const res = await fetch('/api/proxy/pipeline/run', { method: 'POST' });
      if (res.status === 409) {
        setError('A pipeline run is already in progress.');
      } else if (!res.ok) {
        throw new Error(`${res.status} ${res.statusText}`);
      }
      requestRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start run');
    } finally {
      setTriggering(false);
    }
  }

  return (
    <div>
      <div className="form-card" style={{ marginBottom: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 14 }}>Run the full pipeline now</div>
          <div className="field-hint" style={{ marginTop: 4 }}>
            Harvests fresh signals, classifies, scores, curates against active brands, and
            publishes digests — takes about a minute.
          </div>
        </div>
        <button className="btn btn-primary" onClick={trigger} disabled={triggering || anyRunning}>
          <PlayIcon width={15} height={15} />
          {anyRunning ? 'Running…' : triggering ? 'Starting…' : 'Run pipeline'}
        </button>
      </div>

      {error && <div className="callout -error" style={{ marginBottom: 20 }}>{error}</div>}

      <div className="panel-title" style={{ marginBottom: 12 }}>Run history</div>
      {runs.length === 0 && (
        <div className="panel">
          <div className="empty-state">No runs yet — trigger the first one above.</div>
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {runs.map((run) => (
          <RunDetailCard key={run.id} run={run} />
        ))}
      </div>
    </div>
  );
}
