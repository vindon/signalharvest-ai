import { apiFetch } from '@/lib/api';
import type { SignalsResponse } from '@/lib/types';
import SignalsTable from '@/components/SignalsTable';

export default async function SignalsPage() {
  const signals = await apiFetch<SignalsResponse>('/api/v1/signals?hours=24').catch(() => null);

  return (
    <div className="content">
      <div className="content-head">
        <div>
          <h1 className="page-title display">Signal feed</h1>
          <div className="page-sub">Every harvested signal, classified and scored, last 24h</div>
        </div>
      </div>
      <SignalsTable hours={24} showFilters initialData={signals} />
    </div>
  );
}
