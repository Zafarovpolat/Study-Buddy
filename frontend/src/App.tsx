import { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HomePage } from './pages/HomePage';
import { MaterialPage } from './pages/MaterialPage';
import { telegram } from './lib/telegram';
import { GroupResultsPage } from './pages/GroupResultsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30000,
    },
  },
});

function Router() {
  const [route, setRoute] = useState(window.location.hash || '#/');

  useEffect(() => {
    const handleHashChange = () => {
      setRoute(window.location.hash || '#/');
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Parse route
  if (route.startsWith('#/material/')) {
    const materialId = route.replace('#/material/', '');
    return <MaterialPage materialId={materialId} />;
  }

  if (hash.startsWith('#/group/') && hash.endsWith('/results')) {
    const groupId = hash.replace('#/group/', '').replace('/results', '');
    return <GroupResultsPage groupId={groupId} />;
  }

  return <HomePage />;
}

function App() {
  useEffect(() => {
    // Initialize Telegram WebApp
    telegram.init();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <Router />
    </QueryClientProvider>
  );
}

export default App;