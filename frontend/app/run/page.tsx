import { apiFetch } from '@/lib/api';
import type { RunsResponse } from '@/lib/types';
import RunPipelinePanel from '@/components/RunPipelinePanel';

export default async function RunPage() {
  const runs = await apiFetch<RunsResponse>('/api/v1/pipeline/runs?limit=10').catch(() => null);

  return (
    <div className="content">
      <div className="content-head">
        <div>
          <h1 className="page-title display">Run pipeline</h1>
          <div className="page-sub">Trigger a fresh harvest → classify → score → curate → publish cycle</div>
        </div>
      </div>
      <RunPipelinePanel initialData={runs} />
    </div>
  );
}
