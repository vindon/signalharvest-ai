'use client';

import { useState } from 'react';
import { ALL_CATEGORIES } from '@/lib/categories';
import { categoryLabel } from '@/lib/format';
import { requestRefresh } from '@/lib/usePolling';
import type { SignalTier } from '@/lib/types';

const TIERS: SignalTier[] = ['watch', 'warm', 'hot'];

export default function BrandForm({ onDone }: { onDone: () => void }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const [minTier, setMinTier] = useState<SignalTier>('watch');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleCategory(cat: string) {
    setCategories((prev) => (prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim() || !email.trim() || categories.length === 0) {
      setError('Name, contact email, and at least one category are required.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch('/api/proxy/brands', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          contact_email: email.trim(),
          categories,
          min_tier: minTier,
        }),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      requestRefresh();
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create brand');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="form-card" onSubmit={submit}>
      <div className="field">
        <label className="field-label" htmlFor="brand-name">Brand name</label>
        <input id="brand-name" type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Acme Mobile" />
      </div>
      <div className="field">
        <label className="field-label" htmlFor="brand-email">Contact email</label>
        <input id="brand-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="leads@acme.com" />
      </div>
      <div className="field">
        <span className="field-label">Minimum tier to include</span>
        <div className="chip-select">
          {TIERS.map((t) => (
            <button
              type="button"
              key={t}
              className={`chip-toggle${minTier === t ? ' -active' : ''}`}
              onClick={() => setMinTier(t)}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="field-hint">Watch includes everything; Hot only sends the highest-urgency signals.</div>
      </div>
      <div className="field">
        <span className="field-label">Categories ({categories.length} selected)</span>
        <div className="chip-select">
          {ALL_CATEGORIES.map((cat) => (
            <button
              type="button"
              key={cat}
              className={`chip-toggle${categories.includes(cat) ? ' -active' : ''}`}
              onClick={() => toggleCategory(cat)}
            >
              {categoryLabel(cat)}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="callout -error" style={{ marginBottom: 14 }}>{error}</div>}

      <div style={{ display: 'flex', gap: 10 }}>
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Creating…' : 'Create brand'}
        </button>
        <button type="button" className="btn" onClick={onDone} disabled={submitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
