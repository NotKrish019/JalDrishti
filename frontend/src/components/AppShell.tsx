import React from 'react';
import { Header } from './Header';
import { AppRoute, InspectionSession } from '../types';

export interface AppShellProps {
  currentRoute: AppRoute;
  onRouteChange: (route: AppRoute, hash?: string) => void;
  session: InspectionSession | null;
  children: React.ReactNode;
}

/**
 * Frame for the operational application: header, main landmark, footer, on the
 * stone ground of the workspace theme (`.ws`, index.css). The landing page does
 * not use AppShell, so the theme never reaches it.
 */
export const AppShell: React.FC<AppShellProps> = ({ currentRoute, onRouteChange, session, children }) => (
  <div className="ws flex min-h-screen flex-col">
    <a
      href="#main"
      className="sr-only-focusable fixed left-4 top-3 z-overlay rounded-md bg-ws-text px-4 py-2 text-sm text-ws-stone"
    >
      Skip to content
    </a>

    <Header currentRoute={currentRoute} onRouteChange={onRouteChange} hasSession={session !== null} />

    <main id="main" tabIndex={-1} className="flex-1 focus:outline-none">
      {children}
    </main>

    <footer className="ws-dark border-t border-[var(--ws-line-dark)] print:hidden">
      <div className="gutter mx-auto flex max-w-wide flex-col gap-2 py-7 text-[0.8125rem] text-ws-faint sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="font-medium text-ws-muted">JalDrishti</span> · Team NeuralX
        </p>
        <p className="max-w-xl leading-relaxed">
          Outputs support, and do not replace, assessment by qualified conservation engineers. No result here certifies
          structural safety.
        </p>
      </div>
    </footer>
  </div>
);

export default AppShell;
