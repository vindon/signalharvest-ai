'use client';

import { useState } from 'react';
import type { BrandsResponse, BrandSubscription } from '@/lib/types';
import { usePolling, requestRefresh } from '@/lib/usePolling';
import { categoryLabel } from '@/lib/format';
import { Badge, tierTone, tierLabel } from './Badge';
import { PlusIcon, TrashIcon, EmptyIcon } from './icons';
import BrandForm from './BrandForm';

export default function BrandsPanel({ initialData }: { initialData: BrandsResponse | null }) {
  const { data } = usePolling<BrandsResponse>('/brands', 10000, initialData);
  const [showForm, setShowForm] = useState(false);
  const brands = data?.brands ?? [];

  async function toggleActive(brand: BrandSubscription) {
    await fetch(`/api/proxy/brands/${brand.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: !brand.active }),
    });
    requestRefresh();
  }

  async function remove(brand: BrandSubscription) {
    if (!confirm(`Delete ${brand.name}? This can't be undone.`)) return;
    await fetch(`/api/proxy/brands/${brand.id}`, { method: 'DELETE' });
    requestRefresh();
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        {!showForm && (
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            <PlusIcon width={15} height={15} />
            New brand
          </button>
        )}
      </div>

      {showForm && (
        <div style={{ marginBottom: 20 }}>
          <BrandForm onDone={() => setShowForm(false)} />
        </div>
      )}

      {brands.length === 0 && !showForm && (
        <div className="panel">
          <div className="empty-state">
            <EmptyIcon width={32} height={32} style={{ margin: '0 auto 10px' }} />
            <div className="empty-state-title">No brand subscriptions yet</div>
            Create one to start receiving curated lead digests from every pipeline run.
          </div>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {brands.map((brand) => (
          <div className="panel" key={brand.id} style={{ padding: 18 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="row-title" style={{ fontSize: 14.5 }}>{brand.name}</span>
                  <Badge tone={brand.active ? 'success' : 'neutral'}>{brand.active ? 'Active' : 'Paused'}</Badge>
                  <Badge tone={tierTone(brand.min_tier)}>Min: {tierLabel(brand.min_tier)}</Badge>
                </div>
                <div className="row-sub" style={{ marginTop: 4 }}>{brand.contact_email} · {brand.digest_frequency}</div>
              </div>
              <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                <button className="btn btn-sm" onClick={() => toggleActive(brand)}>
                  {brand.active ? 'Pause' : 'Resume'}
                </button>
                <button className="btn btn-sm" onClick={() => remove(brand)} aria-label={`Delete ${brand.name}`}>
                  <TrashIcon width={14} height={14} />
                </button>
              </div>
            </div>
            <div className="drawer-badges" style={{ marginTop: 12 }}>
              {brand.categories.map((c) => (
                <span key={c} className="category-chip">{categoryLabel(c)}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
