import { useEffect, useState, lazy, Suspense } from 'react';
import { HomePage } from './pages/HomePage';
import { telegram } from './lib/telegram';

const MaterialPage = lazy(() => import('./pages/MaterialPage').then(m => ({ default: m.MaterialPage })));
const GroupResultsPage = lazy(() => import('./pages/GroupResultsPage').then(m => ({ default: m.GroupResultsPage })));
const OnboardingPage = lazy(() => import('./pages/OnboardingPage').then(m => ({ default: m.OnboardingPage })));
const InsightsPage = lazy(() => import('./pages/InsightsPage').then(m => ({ default: m.InsightsPage })));
const ProPage = lazy(() => import('./pages/ProPage').then(m => ({ default: m.ProPage })));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function Router() {
  const [route, setRoute] = useState(window.location.hash || '#/');

  useEffect(() => {
    const handleHashChange = () => {
      setRoute(window.location.hash || '#/');
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Onboarding check
  useEffect(() => {
    const isOnboardingCompleted = localStorage.getItem('lecto_onboarding_completed');
    if (!isOnboardingCompleted && !route.startsWith('#/onboarding')) {
      window.location.hash = '#/onboarding';
    }
  }, [route]);

  if (route.startsWith('#/onboarding')) {
    return (
      <Suspense fallback={<LoadingFallback />}>
        <OnboardingPage />
      </Suspense>
    );
  }

  if (route.startsWith('#/insights')) {
    return (
      <Suspense fallback={<LoadingFallback />}>
        <InsightsPage />
      </Suspense>
    );
  }

  if (route.startsWith('#/pro')) {
    return (
      <Suspense fallback={<LoadingFallback />}>
        <ProPage />
      </Suspense>
    );
  }

  if (route.startsWith('#/group/') && route.endsWith('/results')) {
    const groupId = route.replace('#/group/', '').replace('/results', '');
    return (
      <Suspense fallback={<LoadingFallback />}>
        <GroupResultsPage groupId={groupId} />
      </Suspense>
    );
  }

  if (route.startsWith('#/material/')) {
    const materialId = route.replace('#/material/', '');
    return (
      <Suspense fallback={<LoadingFallback />}>
        <MaterialPage materialId={materialId} />
      </Suspense>
    );
  }

  return <HomePage />;
}

function App() {
  useEffect(() => {
    telegram.init();
  }, []);

  return <Router />;
}

export default App;
