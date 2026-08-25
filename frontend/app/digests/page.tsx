import { apiFetch } from '@/lib/api';
import type { DigestsResponse } from '@/lib/types';
import DigestsTable from '@/components/DigestsTable';

export default async function DigestsPage() {
  const digests = await apiFetch<DigestsResponse>('/api/v1/digests').catch(() => null);

  return (
    <div className="content">
      <div className="content-head">
        <div>
          <h1 className="page-title display">Digests</h1>
          <div className="page-sub">Curated leads, delivered per brand, every pipeline run</div>
        </div>
      </div>
      <DigestsTable initialData={digests} />
    </div>
  );
}
