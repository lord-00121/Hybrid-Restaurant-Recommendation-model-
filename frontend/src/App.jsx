import React, { createContext, useContext, useState, useEffect } from 'react';
import { Routes, Route, useLocation, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Discover from './pages/Discover';
import Restaurant from './pages/Restaurant';
import Admin from './pages/Admin';
import Login from './pages/Login';
import Register from './pages/Register';
import { login as apiLogin, register as apiRegister, getMe } from './api/client';

// AuthContext initialization
export const AuthContext = createContext(null);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token') || null);
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  // Validate or fetch fresh profile if token exists on boot
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          const userData = await getMe();
          setUser(userData);
          localStorage.setItem('user', JSON.stringify(userData));
        } catch (err) {
          console.warn('Token validation failed or getMe endpoint error:', err.message);
          // If 401, client interceptor will clear token.
          // Otherwise keep stored user to allow offline/mock operation
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const data = await apiLogin(email, password);
      const authToken = data.token || data.access_token || 'mock-jwt-token';

      // Store token first so getMe() can use it
      localStorage.setItem('token', authToken);
      setToken(authToken);

      // Fetch full profile from server
      let authUser;
      try {
        authUser = await getMe();
      } catch {
        authUser = data.user || {
          id: data.id || 1,
          email,
          name: data.name || email.split('@')[0],
          is_admin: email.toLowerCase().includes('admin') || Boolean(data.is_admin),
        };
      }

      setUser(authUser);
      localStorage.setItem('user', JSON.stringify(authUser));
      return authUser;
    } catch (err) {
      // Fallback mock authorization for development if server is not yet running
      if (!err.response) {
        const mockUser = {
          id: 1,
          email,
          name: email.split('@')[0],
          is_admin: email.toLowerCase().includes('admin'),
        };
        const mockToken = 'mock-demo-jwt-token';
        setToken(mockToken);
        setUser(mockUser);
        localStorage.setItem('token', mockToken);
        localStorage.setItem('user', JSON.stringify(mockUser));
        return mockUser;
      }
      throw err;
    }
  };

  const register = async (name, email, password, preferences = {}) => {
    try {
      const data = await apiRegister(name, email, password, preferences);
      const authToken = data.token || data.access_token || 'mock-jwt-token';
      const authUser = data.user || {
        id: data.id || Date.now(),
        name,
        email,
        preferences,
        is_admin: email.toLowerCase().includes('admin') || Boolean(data.is_admin),
      };

      setToken(authToken);
      setUser(authUser);
      localStorage.setItem('token', authToken);
      localStorage.setItem('user', JSON.stringify(authUser));
      return authUser;
    } catch (err) {
      // Fallback mock registration for development if server is offline
      if (!err.response) {
        const mockUser = {
          id: Date.now(),
          name,
          email,
          preferences,
          is_admin: email.toLowerCase().includes('admin'),
        };
        const mockToken = 'mock-demo-jwt-token';
        setToken(mockToken);
        setUser(mockUser);
        localStorage.setItem('token', mockToken);
        localStorage.setItem('user', JSON.stringify(mockUser));
        return mockUser;
      }
      throw err;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  const authValue = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    setUser,
  };

  return (
    <AuthContext.Provider value={authValue}>
      {children}
    </AuthContext.Provider>
  );
}

export default function App() {
  const location = useLocation();

  // Hide persistent Navbar on login and register routes
  const hideNavbar =
    location.pathname === '/login' || location.pathname === '/register';

  return (
    <AuthProvider>
      <div className="app-container">
        {!hideNavbar && <Navbar />}
        <div className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/discover" element={<Discover />} />
            <Route path="/restaurant/:id" element={<Restaurant />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </AuthProvider>
  );
}
