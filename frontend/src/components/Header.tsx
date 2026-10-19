import React, { useEffect, useState } from 'react';
import { JalDrishtiLogo } from './JalDrishtiLogo';
import { Navigation } from './Navigation';
import { Icon } from './Icon';
import { AppRoute } from '../types';
import { checkBackendHealth } from '../services/api';

type BackendStatus = 'checking' | 'connected' | 'unreachable';

/** Polls GET /health and reports exactly what it observed. */
const useBackendStatus = (): { status: BackendStatus; version?: string } => {
  const [state, setState] = useState<{ status: BackendStatus; version?: string }>({ status: 'checking' });

  useEffect(() => {
    let cancelled = false;
    const probe = () =>
      checkBackendHealth()
        .then((res) => !cancelled && setState({ status: 'connected', version: res.version }))
        .catch(() => !cancelled && setState({ status: 'unreachable' }));

    probe();
    const id = window.setInterval(probe, 30000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  return state;
};

const BackendIndicator: React.FC = () => {
  const { status, version } = useBackendStatus();
  const label = { checking: 'Checking API', connected: 'API connected', unreachable: 'API unreachable' }[status];
  const dot = { checking: 'bg-ink-500', connected: 'bg-jade-500', unreachable: 'bg-danger-500' }[status];

  return (
    <span
      className="inline-flex items-center gap-2 font-mono text-[0.6875rem] uppercase tracking-[0.08em] text-ink-600"
      role="status"
      title={version ? `Backend version ${version}` : undefined}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} aria-hidden="true" />
      {label}
    </span>
  );
};

export interface HeaderProps {
  currentRoute: AppRoute;
  onRouteChange: (route: AppRoute) => void;
  hasSession: boolean;
}

export const Header: React.FC<HeaderProps> = ({ currentRoute, onRouteChange, hasSession }) => {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => setMenuOpen(false), [currentRoute]);

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (event: KeyboardEvent) => event.key === 'Escape' && setMenuOpen(false);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [menuOpen]);

  return (
    <header className="sticky top-0 z-nav border-b border-ink-900/10 bg-stone-50/95 backdrop-blur-sm print:hidden">
      <div className="gutter mx-auto flex h-16 max-w-wide items-center justify-between gap-6">
        <a
          href="/"
          onClick={(event) => {
            if (event.metaKey || event.ctrlKey) return;
            event.preventDefault();
            onRouteChange('/');
          }}
          className="shrink-0"
          aria-label="JalDrishti home"
        >
          <JalDrishtiLogo tone="dark" />
        </a>

        <nav aria-label="Application" className="hidden md:block">
          <Navigation currentRoute={currentRoute} onRouteChange={onRouteChange} hasSession={hasSession} />
        </nav>

        <div className="hidden lg:block">
          <BackendIndicator />
        </div>

        <button
          type="button"
          className="-mr-2 inline-flex h-10 w-10 items-center justify-center rounded-sm text-ink-900 md:hidden"
          aria-expanded={menuOpen}
          aria-controls="mobile-nav"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <Icon name={menuOpen ? 'close' : 'menu'} className="h-5 w-5" />
          <span className="sr-only">{menuOpen ? 'Close menu' : 'Open menu'}</span>
        </button>
      </div>

      {menuOpen && (
        <nav id="mobile-nav" aria-label="Application" className="gutter border-t border-ink-900/10 bg-stone-50 pb-6 md:hidden">
          <Navigation
            currentRoute={currentRoute}
            onRouteChange={onRouteChange}
            hasSession={hasSession}
            orientation="vertical"
          />
          <div className="mt-5">
            <BackendIndicator />
          </div>
        </nav>
      )}
    </header>
  );
};

export default Header;
