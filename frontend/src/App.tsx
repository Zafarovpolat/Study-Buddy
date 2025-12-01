import { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HomePage } from './pages/HomePage';
import { MaterialPage } from './pages/MaterialPage';
import { telegram } from './lib/telegram';

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