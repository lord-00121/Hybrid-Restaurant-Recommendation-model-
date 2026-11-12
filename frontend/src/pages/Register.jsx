import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { updatePreferences } from '../api/client';
import PreferenceQuiz from '../components/PreferenceQuiz';
import { UserPlus, User, Mail, Lock, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [diet, setDiet] = useState('Any');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizPrefs, setQuizPrefs] = useState({});

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email || !password) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password.length < 6) {
      setError('Password should be at least 6 characters.');
      return;
    }

    try {
      setLoading(true);
      setError('');

      // Check if user went through onboarding previously
      let savedPreferences = {};
      try {
        const stored = localStorage.getItem('tastify_onboarding_prefs');
        if (stored) {
          savedPreferences = JSON.parse(stored);
        }
      } catch (err) {
        console.warn('Error reading saved preferences:', err);
      }

      // Merge diet selection (backend expects diet as a list)
      const savedDiet = Array.isArray(savedPreferences.diet)
        ? savedPreferences.diet
        : savedPreferences.diet && savedPreferences.diet !== 'Any'
        ? [savedPreferences.diet]
        : [];
      const finalPreferences = {
        ...savedPreferences,
        diet: diet !== 'Any' ? [diet === 'Non-Veg' ? 'Non-Vegetarian' : diet] : savedDiet,
      };

      await register(name, email, password, finalPreferences);
      // Clean up temporary onboarding storage
      localStorage.removeItem('tastify_onboarding_prefs');
      // Show preference questionnaire to solve cold-start
      setQuizPrefs(finalPreferences);
      setShowQuiz(true);
    } catch (err) {
      console.error('Registration error:', err);
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        'Failed to create account. That email may already be registered.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleQuizComplete = async (prefs) => {
    try {
      await updatePreferences(prefs);
    } catch (err) {
      console.warn('Failed to save quiz preferences:', err);
    }
    navigate('/discover', { state: { preferences: prefs } });
  };

  const handleQuizSkip = () => {
    navigate('/discover');
  };

  if (showQuiz) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px 16px',
          background: 'radial-gradient(circle at 50% 20%, rgba(255, 209, 102, 0.08) 0%, transparent 60%), #0a0e1a',
        }}
      >
        <PreferenceQuiz
          initialPrefs={quizPrefs}
          onComplete={handleQuizComplete}
          onSkip={handleQuizSkip}
        />
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 16px',
        background: 'radial-gradient(circle at 50% 20%, rgba(255, 209, 102, 0.08) 0%, transparent 60%), #0a0e1a',
      }}
    >
      <div
        className="glass-card animate-slide-up"
        style={{
          width: '100%',
          maxWidth: '480px',
          padding: '36px 32px',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6), 0 0 25px rgba(255, 209, 102, 0.12)',
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <span
              className="animate-float"
              style={{
                fontSize: '2.5rem',
                display: 'inline-block',
                filter: 'drop-shadow(0 0 15px rgba(255, 209, 102, 0.4))',
              }}
            >
              🍽️
            </span>
          </Link>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Join <span style={{ color: 'var(--accent-teal)' }}>Tastify</span>
          </h1>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
            Get started with AI-driven hybrid dining recommendations.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            className="animate-fade-in"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              color: '#f87171',
              padding: '12px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.85rem',
              marginBottom: '20px',
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Register Form */}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="register-name">
              Full Name
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="register-name"
                type="text"
                className="form-input"
                style={{ paddingLeft: '38px' }}
                placeholder="Ekagra Ramola"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
                required
              />
              <User
                size={16}
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                }}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="register-email">
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="register-email"
                type="email"
                className="form-input"
                style={{ paddingLeft: '38px' }}
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
              <Mail
                size={16}
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                }}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="register-password">
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="register-password"
                type="password"
                className="form-input"
                style={{ paddingLeft: '38px' }}
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
              <Lock
                size={16}
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                }}
              />
            </div>
          </div>

          {/* Quick Dietary Preference */}
          <div className="form-group">
            <label className="form-label">Dietary Preference</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
              {['Any', 'Vegetarian', 'Non-Veg', 'Vegan'].map((d) => {
                const active = diet === d;
                return (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDiet(d)}
                    className={`btn ${active ? 'btn-primary' : 'btn-secondary'} btn-sm`}
                    style={{ fontSize: '0.78rem', padding: '6px 4px' }}
                  >
                    {d}
                  </button>
                );
              })}
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '10px', padding: '12px' }}
            disabled={loading}
          >
            {loading ? (
              'Creating Account...'
            ) : (
              <>
                <UserPlus size={16} /> Sign Up
              </>
            )}
          </button>
        </form>

        {/* Benefits list */}
        <div style={{ marginTop: '22px', borderTop: '1px solid var(--border)', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={14} style={{ color: 'var(--accent-teal)' }} />
            <span>Smart hybrid recommendations that adapt with every rating</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={14} style={{ color: 'var(--accent-teal)' }} />
            <span>Interactive α tuning between personal taste and crowd wisdom</span>
          </div>
        </div>

        {/* Footer */}
        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
          Already have an account?{' '}
          <Link
            to="/login"
            style={{ color: 'var(--accent-teal)', fontWeight: '600', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
          >
            Sign in here <ArrowRight size={13} />
          </Link>
        </div>
      </div>
    </div>
  );
}
