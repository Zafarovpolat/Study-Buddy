// frontend/src/App.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HomePage } from './pages/HomePage';
import { MaterialPage } from './pages/MaterialPage';
import { GroupResultsPage } from './pages/GroupResultsPage';
import { telegram } from './lib/telegram';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30000,
    },
  },
});

import { OnboardingPage } from './pages/OnboardingPage';

import { InsightsPage } from './pages/InsightsPage';
import { ProPage } from './pages/ProPage';

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
    return <OnboardingPage />;
  }

  if (route.startsWith('#/insights')) {
    return <InsightsPage />;
  }

  if (route.startsWith('#/pro')) {
    return <ProPage />;
  }

  // Parse route - результаты группы (проверяем ПЕРЕД material)
  if (route.startsWith('#/group/') && route.endsWith('/results')) {
    const groupId = route.replace('#/group/', '').replace('/results', '');
    return <GroupResultsPage groupId={groupId} />;
  }

  // Страница материала
  if (route.startsWith('#/material/')) {
    const materialId = route.replace('#/material/', '');
    return <MaterialPage materialId={materialId} />;
  }

  // Главная страница
  return <HomePage />;
}

function App() {
  useEffect(() => {
    telegram.init();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <Router />
    </QueryClientProvider>
  );
}

export default App;