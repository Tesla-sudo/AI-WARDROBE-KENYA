// src/App.jsx
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext.jsx';     // ← .jsx
import { QueryClient, QueryClientProvider } from 'react-query';
import Login from './pages/Login.jsx';                         // ← .jsx
import Wardrobe from './pages/Wardrobe.jsx';                   // ← .jsx
import VisualSearch from './pages/VisualSearch.jsx';           // ← .jsx
import { useAuth } from './context/AuthContext.jsx';           // ← .jsx

const queryClient = new QueryClient();

function Protected({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div style={{ minHeight: '100vh', background: '#fafafa' }}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/wardrobe" element={<Protected><Wardrobe /></Protected>} />
              <Route path="/visual-search" element={<Protected><VisualSearch /></Protected>} />
              <Route path="/" element={<Navigate to="/wardrobe" />} />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}