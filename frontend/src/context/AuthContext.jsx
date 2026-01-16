// src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';
import jwtDecode from 'jwt-decode';
import api from '../api/axios';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load user from stored token on mount
  useEffect(() => {
    const loadUser = () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const decoded = jwtDecode(token);
          // Check expiration
          if (decoded.exp * 1000 < Date.now()) {
            localStorage.removeItem('token');
            setUser(null);
          } else {
            setUser({
              id: decoded._id || decoded.sub,
              email: decoded.email,
              full_name: decoded.full_name || null,
            });
            api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          }
        } catch (err) {
          console.error('Invalid token:', err);
          localStorage.removeItem('token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    loadUser();
  }, []);

  // Login with email/password
  const login = async (email, password) => {
    setError(null);
    try {
      const res = await api.post('/auth/login', new URLSearchParams({
        username: email,
        password,
      }));

      const { access_token } = res.data;
      localStorage.setItem('token', access_token);

      const decoded = jwtDecode(access_token);
      const userData = {
        id: decoded._id || decoded.sub,
        email: decoded.email,
        full_name: decoded.full_name || null,
      };

      setUser(userData);
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      return userData;
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed. Please check your email and password.';
      setError(message);
      throw new Error(message);
    }
  };

  // Register new user
  const register = async (email, password, full_name) => {
    setError(null);
    try {
      // Step 1: Register
      const registerRes = await api.post('/auth/register', {
        email,
        password,
        full_name,
      });

      // Step 2: Auto-login immediately after success
      await login(email, password);

      return registerRes.data; // optional: return user data from register
    } catch (err) {
      // Handle common backend validation errors
      let message = 'Registration failed. Please try again.';
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          message = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          // Pydantic validation error array
          message = err.response.data.detail
            .map(d => d.msg || d.loc?.join('.') + ': ' + d.msg)
            .join('; ');
        }
      }
      setError(message);
      throw new Error(message);
    }
  };

  // Logout
  const logout = () => {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
    setError(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};