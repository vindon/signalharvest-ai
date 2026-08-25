import { apiFetch } from '@/lib/api';
import type { BrandsResponse } from '@/lib/types';
import BrandsPanel from '@/components/BrandsPanel';

export default async function BrandsPage() {
  const brands = await apiFetch<BrandsResponse>('/api/v1/brands').catch(() => null);

  return (
    <div className="content">
      <div className="content-head">
        <div>
          <h1 className="page-title display">Brands</h1>
          <div className="page-sub">Subscriptions that determine which signals become curated leads</div>
        </div>
      </div>
      <BrandsPanel initialData={brands} />
    </div>
  );
}
