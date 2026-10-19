import React from 'react';
import { Header } from './Header';
import { AppRoute, InspectionSession } from '../types';

export interface AppShellProps {
  currentRoute: AppRoute;
  onRouteChange: (route: AppRoute, hash?: string) => void;
  session: InspectionSession | null;
  children: React.ReactNode;
}

/** Frame for the operational application: header, main landmark, footer. */
export const AppShell: React.FC<AppShellProps> = ({ currentRoute, onRouteChange, session, children }) => (
  <div className="grain flex min-h-screen flex-col bg-stone-50 text-ink-900">
    <a
      href="#main"
      className="sr-only-focusable fixed left-4 top-3 z-overlay rounded-sm bg-ink-900 px-4 py-2 text-sm text-stone-50"
    >
      Skip to content
    </a>

    <Header currentRoute={currentRoute} onRouteChange={onRouteChange} hasSession={session !== null} />

    <main id="main" tabIndex={-1} className="flex-1 focus:outline-none">
      {children}
    </main>

    <footer className="border-t border-ink-900/10 print:hidden">
      <div className="gutter mx-auto flex max-w-wide flex-col gap-2 py-6 text-xs text-ink-500 sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="font-medium text-ink-700">JalDrishti</span> · Team NeuralX
        </p>
        <p className="max-w-xl">
          Outputs support, and do not replace, assessment by qualified conservation engineers. No result here certifies
          structural safety.
        </p>
      </div>
    </footer>
  </div>
);

export default AppShell;
