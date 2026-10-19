import React from 'react';
import { AppRoute } from '../types';

export interface NavItem {
  route: AppRoute;
  label: string;
  index: string;
}

export const APP_NAV_ITEMS: NavItem[] = [
  { route: '/upload', label: 'Inspect', index: '01' },
  { route: '/analysis', label: 'Findings', index: '02' },
  { route: '/report', label: 'Report', index: '03' },
  { route: '/knowledge', label: 'Knowledge', index: '04' },
];

export interface NavigationProps {
  currentRoute: AppRoute;
  onRouteChange: (route: AppRoute) => void;
  hasSession: boolean;
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}

/** Route links. Real anchors so they can be opened in a new tab; client-side navigation otherwise. */
export const Navigation: React.FC<NavigationProps> = ({
  currentRoute,
  onRouteChange,
  hasSession,
  orientation = 'horizontal',
  className = '',
}) => {
  const vertical = orientation === 'vertical';

  return (
    <ul className={`${vertical ? 'flex flex-col' : 'flex items-center gap-1'} ${className}`}>
      {APP_NAV_ITEMS.map((item) => {
        const active = currentRoute === item.route;
        const showSessionDot = hasSession && (item.route === '/analysis' || item.route === '/report');
        return (
          <li key={item.route}>
            <a
              href={item.route}
              aria-current={active ? 'page' : undefined}
              onClick={(event) => {
                if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
                event.preventDefault();
                onRouteChange(item.route);
              }}
              className={
                vertical
                  ? `flex items-baseline gap-4 border-b border-ink-900/10 py-4 text-2xl font-display ${
                      active ? 'text-ink-900' : 'text-ink-600'
                    }`
                  : `relative flex h-10 items-center gap-2 rounded-sm px-3 text-sm transition-colors duration-fast ${
                      active ? 'text-ink-900' : 'text-ink-600 hover:text-ink-900'
                    }`
              }
            >
              <span className={`font-mono text-[0.625rem] tabular-nums ${active ? 'text-laterite-500' : 'text-ink-500'}`}>
                {item.index}
              </span>
              <span>{item.label}</span>
              {showSessionDot && (
                <span className="h-1.5 w-1.5 rounded-full bg-jade-500" aria-label="(inspection loaded)" />
              )}
              {active && !vertical && (
                <span className="absolute inset-x-3 -bottom-[13px] h-px bg-ink-900" aria-hidden="true" />
              )}
            </a>
          </li>
        );
      })}
    </ul>
  );
};

export default Navigation;
