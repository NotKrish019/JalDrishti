import React, { useCallback, useEffect, useState } from 'react';
import { AppShell } from './components/AppShell';
import { HomePage } from './pages/HomePage';
import { UploadPage } from './pages/UploadPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { KnowledgePage } from './pages/KnowledgePage';
import { ReportPage } from './pages/ReportPage';
import { AppRoute, InspectionSession } from './types';
import { getDevelopmentMockFixture } from './services/api';

const ROUTES: AppRoute[] = ['/', '/upload', '/analysis', '/knowledge', '/report'];

const routeFromLocation = (): AppRoute => {
  const path = window.location.pathname.replace(/\/+$/, '') || '/';
  return (ROUTES as string[]).includes(path) ? (path as AppRoute) : '/';
};

export const App: React.FC = () => {
  const [currentRoute, setCurrentRoute] = useState<AppRoute>(routeFromLocation);
  const [session, setSession] = useState<InspectionSession | null>(null);

  useEffect(() => {
    const handlePopState = () => setCurrentRoute(routeFromLocation());
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleNavigate = useCallback((route: AppRoute, hash?: string) => {
    const target = hash ? `${route}#${hash}` : route;
    if (route !== routeFromLocation() || hash) {
      window.history.pushState(null, '', target);
    }
    setCurrentRoute(route);
    if (!hash) {
      // Jump instantly: smooth-scrolling back through the 3D descent would replay it.
      window.scrollTo({ top: 0, behavior: 'auto' });
    }
  }, []);

  const handleInspectionComplete = useCallback(
    (next: InspectionSession) => {
      setSession(next);
      handleNavigate('/analysis');
    },
    [handleNavigate],
  );

  // Explicit, user-initiated only. The fixture is labelled everywhere it is shown.
  const handleLoadFixture = useCallback(async () => {
    const fixture = await getDevelopmentMockFixture();
    setSession({ result: fixture, provenance: 'fixture' });
    handleNavigate('/analysis');
  }, [handleNavigate]);

  if (currentRoute === '/') {
    return <HomePage onRouteChange={handleNavigate} />;
  }

  return (
    <AppShell currentRoute={currentRoute} onRouteChange={handleNavigate} session={session}>
      {currentRoute === '/upload' && (
        <UploadPage onComplete={handleInspectionComplete} onRouteChange={handleNavigate} />
      )}
      {currentRoute === '/analysis' && (
        <AnalysisPage session={session} onRouteChange={handleNavigate} onLoadFixture={handleLoadFixture} />
      )}
      {currentRoute === '/knowledge' && <KnowledgePage onRouteChange={handleNavigate} />}
      {currentRoute === '/report' && (
        <ReportPage session={session} onRouteChange={handleNavigate} onLoadFixture={handleLoadFixture} />
      )}
    </AppShell>
  );
};

export default App;
