'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { RunsResponse } from '@/lib/types';
import { usePolling } from '@/lib/usePolling';
import {
  OverviewIcon,
  SignalWaveIcon,
  BrandIcon,
  DigestIcon,
  PlayIcon,
  SearchIcon,
  BellIcon,
  RadarIcon,
} from './icons';

const NAV_ITEMS = [
  { href: '/', label: 'Overview', icon: OverviewIcon },
  { href: '/signals', label: 'Signal feed', icon: SignalWaveIcon },
  { href: '/brands', label: 'Brands', icon: BrandIcon },
  { href: '/digests', label: 'Digests', icon: DigestIcon },
  { href: '/run', label: 'Run pipeline', icon: PlayIcon, badgeKey: 'running' as const },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data } = usePolling<RunsResponse>('/pipeline/runs?limit=1', 8000);
  const latestRun = data?.runs?.[0];
  const isRunning = latestRun?.status === 'running';

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">
            <RadarIcon width={18} height={18} />
          </div>
          <div>
            <div className="sidebar-brand-name">SignalHarvest</div>
            <div className="sidebar-brand-tag">Lead intelligence</div>
          </div>
        </div>

        <nav aria-label="Primary">
          <div className="nav-section-label">Workspace</div>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} className={`nav-item${active ? ' active' : ''}`}>
                <Icon />
                <span className="nav-label">{item.label}</span>
                {item.badgeKey === 'running' && isRunning && (
                  <span className="nav-badge" style={{ background: 'var(--brand-tint)', color: 'var(--brand-deep)' }}>
                    live
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar">VN</div>
            <div>
              <div className="user-name">Vinoth N.</div>
              <div className="user-role">Growth Ops</div>
            </div>
          </div>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="search" role="search">
            <SearchIcon />
            Search signals, brands, digests…
          </div>
          <div className="topbar-actions">
            <div className="icon-btn">
              <BellIcon />
              {isRunning && <span className="dot-alert" />}
            </div>
          </div>
        </header>

        <main>{children}</main>
      </div>
    </div>
  );
}
