import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import { Compass, ShieldCheck, LogOut, LogIn, UserPlus, Search } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const q = new URLSearchParams(location.search).get('q') || '';
    setSearchTerm(q);
  }, [location.search]);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 15) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleSearch = (e) => {
    if (e) e.preventDefault();
    const query = searchTerm.trim();
    if (query) {
      navigate(`/discover?q=${encodeURIComponent(query)}`);
    } else {
      navigate('/discover');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const homeDestination = user ? '/discover' : '/';
  const isAdmin = user?.is_admin || user?.role === 'admin';

  return (
    <nav className={`navbar ${scrolled ? 'navbar-scrolled' : ''}`}>
      <div className="navbar-inner">
        {/* Logo */}
        <Link to={homeDestination} className="navbar-logo">
          <span style={{ fontSize: '1.5rem', filter: 'drop-shadow(0 0 10px rgba(0,212,170,0.3))' }}>🍽️</span>
          <span className="gradient-text">Tastify</span>
        </Link>

        {/* Search Bar */}
        <form
          onSubmit={handleSearch}
          className="navbar-search"
          style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            flex: '1',
            maxWidth: '380px',
            margin: '0 20px',
          }}
        >
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '14px',
              color: 'var(--text-secondary)',
              pointerEvents: 'none',
            }}
          />
          <input
            type="text"
            className="form-input"
            placeholder="Search restaurants, cuisines..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch(e);
              }
            }}
            style={{
              width: '100%',
              paddingLeft: '38px',
              paddingRight: '14px',
              paddingTop: '8px',
              paddingBottom: '8px',
              fontSize: '0.88rem',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              border: '1px solid var(--border)',
            }}
          />
        </form>

        {/* Right Navigation */}
        <div className="navbar-links">
          {user ? (
            <>
              {/* Discover Link */}
              <Link
                to="/discover"
                className={`btn ${location.pathname === '/discover' ? 'btn-secondary' : 'btn-ghost'} btn-sm`}
                style={{ gap: '6px' }}
              >
                <Compass size={15} style={{ color: 'var(--accent-teal)' }} />
                <span>Discover</span>
              </Link>

              {/* Admin Link if admin */}
              {isAdmin && (
                <Link
                  to="/admin"
                  className={`btn ${location.pathname === '/admin' ? 'btn-secondary' : 'btn-ghost'} btn-sm`}
                  style={{ gap: '6px' }}
                >
                  <ShieldCheck size={15} style={{ color: 'var(--accent-gold)' }} />
                  <span>Admin</span>
                </Link>
              )}

              {/* User Avatar & Name */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '9px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  padding: '4px 12px 4px 6px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid var(--border)',
                }}
              >
                <div className="user-avatar-badge" title={user.name || user.email}>
                  {getInitials(user.name || user.email)}
                </div>
                <span
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    maxWidth: '120px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    color: 'var(--text-primary)',
                  }}
                >
                  {user.name || user.email.split('@')[0]}
                </span>
              </div>

              {/* Logout Button */}
              <button
                type="button"
                onClick={handleLogout}
                className="btn btn-ghost btn-sm"
                style={{ gap: '6px' }}
                title="Log out of Tastify"
              >
                <LogOut size={15} />
                <span>Logout</span>
              </button>
            </>
          ) : (
            <>
              <Link to="/discover" className="btn btn-ghost btn-sm" style={{ gap: '6px' }}>
                <Compass size={15} />
                <span>Explore</span>
              </Link>
              <Link to="/login" className="btn btn-ghost btn-sm" style={{ gap: '6px' }}>
                <LogIn size={15} />
                <span>Log In</span>
              </Link>
              <Link to="/register" className="btn btn-primary btn-sm" style={{ gap: '6px' }}>
                <UserPlus size={15} />
                <span>Sign Up</span>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
