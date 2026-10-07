import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation,
} from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './AuthContext';
import { Layout } from './Layout';
import { LoginPage } from '../features/auth/LoginPage';
import { OverviewPage } from '../features/brief/OverviewPage';
import { SignalsPage } from '../features/signals/SignalsPage';
import { InstrumentPage } from '../features/instruments/InstrumentPage';
import { NewsPage } from '../features/news/NewsPage';
import { AgentsPage } from '../features/agents/AgentsPage';
import { HistoryPage } from '../features/history/HistoryPage';
import { StatsPage } from '../features/stats/StatsPage';
import { SettingsPage } from '../features/settings/SettingsPage';
import { ForbiddenPage } from './ForbiddenPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5_000,
    },
  },
});

/** Route guard: requires authentication */
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) return null;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return <>{children}</>;
}

/** Route guard: OWNER only */
function RequireOwner({ children }: { children: React.ReactNode }) {
  const { isOwner, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) return null;
  if (!isOwner) return <Navigate to="/403" state={{ from: location }} replace />;
  return <>{children}</>;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/403" element={<ForbiddenPage />} />

            {/* Protected shell with nav */}
            <Route
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route index element={<OverviewPage />} />
              <Route path="/signals" element={<SignalsPage />} />
              <Route path="/instruments/:symbol" element={<InstrumentPage />} />
              <Route path="/news" element={<NewsPage />} />
              <Route path="/agents" element={<AgentsPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/stats" element={<StatsPage />} />
              <Route
                path="/settings"
                element={
                  <RequireOwner>
                    <SettingsPage />
                  </RequireOwner>
                }
              />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
