import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../App';
import {
  Sparkles,
  ArrowRight,
  Brain,
  Users,
  Cpu,
  Check,
  ChevronLeft,
  ChevronRight,
  Compass,
  MapPin,
  UtensilsCrossed,
  DollarSign
} from 'lucide-react';

const CUISINE_OPTIONS = [
  { id: 'North Indian', label: 'North Indian', emoji: '🍛' },
  { id: 'South Indian', label: 'South Indian', emoji: '🥞' },
  { id: 'Chinese', label: 'Chinese', emoji: '🥢' },
  { id: 'Italian', label: 'Italian', emoji: '🍕' },
  { id: 'Continental', label: 'Continental', emoji: '🥗' },
  { id: 'Japanese', label: 'Japanese', emoji: '🍣' },
  { id: 'Mexican', label: 'Mexican', emoji: '🌮' },
  { id: 'Cafe', label: 'Cafe & Coffee', emoji: '☕' },
  { id: 'Desserts', label: 'Desserts & Bakery', emoji: '🍰' },
  { id: 'Fast Food', label: 'Burgers & Fries', emoji: '🍔' },
  { id: 'Asian', label: 'Pan-Asian', emoji: '🍜' },
  { id: 'Beverages', label: 'Cocktails & Brews', emoji: '🍹' },
];

const DIET_OPTIONS = [
  { id: 'Any', title: 'No Restrictions', desc: 'Open to all culinary adventures', icon: '🍽️' },
  { id: 'Vegetarian', title: 'Vegetarian', desc: '100% plant & dairy delights', icon: '🥦' },
  { id: 'Non-Vegetarian', title: 'Non-Vegetarian', desc: 'Poultry, seafood & meats', icon: '🍗' },
  { id: 'Vegan', title: 'Vegan', desc: 'Strictly plant-based goodness', icon: '🌱' },
];

const BUDGET_OPTIONS = [
  { id: 'Budget', title: 'Budget (₹)', desc: 'Pocket-friendly dining under ₹500 for two', icon: '🪙' },
  { id: 'Moderate', title: 'Moderate (₹₹)', desc: 'Casual dining between ₹500 - ₹1200', icon: '💳' },
  { id: 'Premium', title: 'Premium (₹₹₹)', desc: 'Upscale & fine dining ₹1200 - ₹2500+', icon: '💎' },
];

export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [showOnboarding, setShowOnboarding] = useState(false);
  const [step, setStep] = useState(1);

  // Onboarding Form State
  const [selectedCuisines, setSelectedCuisines] = useState(['North Indian', 'Italian']);
  const [selectedDiet, setSelectedDiet] = useState('Any');
  const [selectedBudget, setSelectedBudget] = useState('Moderate');
  const [area, setArea] = useState('');

  const toggleCuisine = (id) => {
    if (selectedCuisines.includes(id)) {
      setSelectedCuisines(selectedCuisines.filter((c) => c !== id));
    } else {
      setSelectedCuisines([...selectedCuisines, id]);
    }
  };

  const handleFinishOnboarding = () => {
    const prefs = {
      cuisines: selectedCuisines,
      diet: selectedDiet === 'Any' ? [] : [selectedDiet],
      budget: selectedBudget,
      location: area.trim(),
    };
    try {
      localStorage.setItem('tastify_onboarding_prefs', JSON.stringify(prefs));
    } catch (e) {
      console.warn(e);
    }

    if (user) {
      navigate('/discover', { state: { preferences: prefs } });
    } else {
      // Navigate to discover with preferences in state
      navigate('/discover', { state: { preferences: prefs } });
    }
  };

  return (
    <div style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Floating Background Emojis */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          zIndex: 0,
          opacity: 0.18,
        }}
      >
        <span className="animate-float" style={{ position: 'absolute', top: '10%', left: '8%', fontSize: '3rem', animationDelay: '0s' }}>🍕</span>
        <span className="animate-float" style={{ position: 'absolute', top: '22%', right: '12%', fontSize: '3.5rem', animationDelay: '1.2s' }}>🍣</span>
        <span className="animate-float" style={{ position: 'absolute', top: '55%', left: '4%', fontSize: '2.8rem', animationDelay: '2.5s' }}>🍜</span>
        <span className="animate-float" style={{ position: 'absolute', top: '70%', right: '8%', fontSize: '3.2rem', animationDelay: '0.8s' }}>🥑</span>
        <span className="animate-float" style={{ position: 'absolute', top: '85%', left: '45%', fontSize: '2.6rem', animationDelay: '1.8s' }}>🍔</span>
      </div>

      <div className="page-container" style={{ position: 'relative', zIndex: 1, paddingTop: '40px' }}>
        {/* Hero Section */}
        <div style={{ textAlign: 'center', maxWidth: '820px', margin: '0 auto 60px auto' }}>
          <div
            className="animate-fade-in"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}
          >
            <span className="badge badge-teal" style={{ padding: '6px 14px', fontSize: '0.82rem' }}>
              <Sparkles size={13} /> Next-Gen Hybrid AI Recommendation Engine
            </span>
          </div>

          <h1
            className="animate-slide-up"
            style={{
              fontSize: 'clamp(2.4rem, 5vw, 4rem)',
              fontWeight: '800',
              lineHeight: '1.15',
              letterSpacing: '-0.03em',
              marginBottom: '20px',
            }}
          >
            Discover Your{' '}
            <span
              style={{
                background: 'linear-gradient(135deg, #00d4aa 0%, #38bdf8 50%, #ffd166 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Perfect Restaurant
            </span>
          </h1>

          <p
            className="animate-slide-up"
            style={{
              fontSize: '1.15rem',
              color: 'var(--text-secondary)',
              lineHeight: '1.6',
              marginBottom: '36px',
            }}
          >
            Tastify harmonizes content-based taste profiling with collaborative crowd intelligence.
            No generic top-10 lists — just hyper-personalized culinary matches with tunable hybrid scoring.
          </p>

          {/* Call to Actions */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '16px',
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            {!showOnboarding ? (
              <>
                <button
                  type="button"
                  className="btn btn-primary btn-lg"
                  onClick={() => setShowOnboarding(true)}
                  style={{ gap: '10px' }}
                >
                  <Sparkles size={18} /> Get Started with Preferences
                </button>
                <Link to="/discover" className="btn btn-secondary btn-lg" style={{ gap: '10px' }}>
                  <Compass size={18} style={{ color: 'var(--accent-teal)' }} /> Explore All Restaurants
                </Link>
              </>
            ) : (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setShowOnboarding(false)}
              >
                Hide Taste Setup
              </button>
            )}
          </div>
        </div>

        {/* Interactive Onboarding Wizard */}
        {showOnboarding && (
          <div
            className="glass-card animate-slide-up"
            style={{
              maxWidth: '720px',
              margin: '0 auto 70px auto',
              padding: '36px',
              border: '1px solid var(--border-accent)',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6), var(--shadow-glow)',
            }}
          >
            {/* Step Progress Bar */}
            <div style={{ marginBottom: '28px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--accent-teal)' }}>
                  Step {step} of 4
                </span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {step === 1 && 'Favorite Cuisines'}
                  {step === 2 && 'Dietary Preferences'}
                  {step === 3 && 'Budget Tier'}
                  {step === 4 && 'Dining Location'}
                </span>
              </div>
              <div className="progress-bar-container" style={{ height: '6px' }}>
                <div
                  className="progress-bar-fill progress-teal"
                  style={{ width: `${(step / 4) * 100}%` }}
                />
              </div>
            </div>

            {/* Step 1: Cuisines */}
            {step === 1 && (
              <div className="animate-fade-in">
                <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '8px' }}>
                  What flavors make you crave? 🍽️
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
                  Select at least one cuisine to calibrate your initial taste vector.
                </p>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
                    gap: '10px',
                    marginBottom: '28px',
                  }}
                >
                  {CUISINE_OPTIONS.map((c) => {
                    const active = selectedCuisines.includes(c.id);
                    return (
                      <button
                        key={c.id}
                        type="button"
                        onClick={() => toggleCuisine(c.id)}
                        className={`chip-btn ${active ? 'active' : ''}`}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          padding: '10px 14px',
                          borderRadius: 'var(--radius-sm)',
                          justifyContent: 'flex-start',
                        }}
                      >
                        <span style={{ fontSize: '1.2rem' }}>{c.emoji}</span>
                        <span>{c.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Step 2: Diet */}
            {step === 2 && (
              <div className="animate-fade-in">
                <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '8px' }}>
                  Any dietary preferences or rules? 🥗
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
                  We will prioritize restaurants with certified options matching your lifestyle.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '28px' }}>
                  {DIET_OPTIONS.map((d) => {
                    const active = selectedDiet === d.id;
                    return (
                      <div
                        key={d.id}
                        onClick={() => setSelectedDiet(d.id)}
                        className={`glass-card-hover ${active ? 'active' : ''}`}
                        style={{
                          padding: '18px',
                          borderRadius: 'var(--radius-md)',
                          border: active ? '1px solid var(--accent-teal)' : '1px solid var(--border)',
                          background: active ? 'var(--accent-teal-dim)' : 'var(--bg-card)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '1.5rem' }}>{d.icon}</span>
                          {active && <Check size={18} style={{ color: 'var(--accent-teal)' }} />}
                        </div>
                        <h4 style={{ fontSize: '1rem', fontWeight: '700', color: active ? 'var(--accent-teal)' : 'var(--text-primary)' }}>
                          {d.title}
                        </h4>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                          {d.desc}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Step 3: Budget */}
            {step === 3 && (
              <div className="animate-fade-in">
                <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '8px' }}>
                  What's your typical spending comfort? 💳
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
                  Price tier filter for recommendations. You can adjust this anytime in the filters.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '28px' }}>
                  {BUDGET_OPTIONS.map((b) => {
                    const active = selectedBudget === b.id;
                    return (
                      <div
                        key={b.id}
                        onClick={() => setSelectedBudget(b.id)}
                        className="glass-card-hover"
                        style={{
                          padding: '16px 20px',
                          borderRadius: 'var(--radius-md)',
                          border: active ? '1px solid var(--accent-gold)' : '1px solid var(--border)',
                          background: active ? 'var(--accent-gold-dim)' : 'var(--bg-card)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                          <span style={{ fontSize: '1.4rem' }}>{b.icon}</span>
                          <div>
                            <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: active ? 'var(--accent-gold)' : 'var(--text-primary)' }}>
                              {b.title}
                            </h4>
                            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                              {b.desc}
                            </p>
                          </div>
                        </div>
                        {active && <Check size={18} style={{ color: 'var(--accent-gold)' }} />}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Step 4: Location Area */}
            {step === 4 && (
              <div className="animate-fade-in">
                <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '8px' }}>
                  Where do you dine most often? 📍
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
                  Enter your neighborhood or landmark to sort by proximity and local density.
                </p>

                <div className="form-group" style={{ marginBottom: '28px' }}>
                  <label className="form-label" htmlFor="onboarding-area">
                    Neighborhood / City Area
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input
                      id="onboarding-area"
                      type="text"
                      className="form-input"
                      style={{ paddingLeft: '38px' }}
                      placeholder="e.g. Indiranagar, Connaught Place, Bandra West"
                      value={area}
                      onChange={(e) => setArea(e.target.value)}
                    />
                    <MapPin
                      size={16}
                      style={{
                        position: 'absolute',
                        left: '12px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        color: 'var(--accent-teal)',
                      }}
                    />
                  </div>
                  <span className="form-helper">
                    Leave blank to show popular recommendations across the city.
                  </span>
                </div>
              </div>
            )}

            {/* Navigation buttons */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
              {step > 1 ? (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setStep(step - 1)}
                  style={{ gap: '6px' }}
                >
                  <ChevronLeft size={16} /> Back
                </button>
              ) : (
                <div />
              )}

              {step < 4 ? (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => setStep(step + 1)}
                  disabled={step === 1 && selectedCuisines.length === 0}
                  style={{ gap: '6px' }}
                >
                  Next Step <ChevronRight size={16} />
                </button>
              ) : (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleFinishOnboarding}
                  style={{ gap: '8px' }}
                >
                  <Sparkles size={16} /> Finish & See Matches
                </button>
              )}
            </div>
          </div>
        )}

        {/* 3 Core Architecture Features */}
        <div style={{ marginBottom: '80px' }}>
          <div style={{ textAlign: 'center', marginBottom: '36px' }}>
            <h2 style={{ fontSize: '1.8rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
              How Tastify's Hybrid Intelligence Works
            </h2>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              Engineered to conquer the cold start problem and avoid generic echo chambers.
            </p>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '24px',
            }}
          >
            {/* Feature 1 */}
            <div className="glass-card" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div
                style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--accent-teal-dim)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-teal)',
                }}
              >
                <Brain size={24} />
              </div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                Content-Based Profiling
              </h3>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                Analyzes high-dimensional feature vectors: cuisines, price tiers, dining ambience, specialties, and dietary certifications. Matches restaurants directly to your explicit tastes with cosine similarity.
              </p>
              <span className="badge badge-teal" style={{ alignSelf: 'flex-start', marginTop: 'auto' }}>
                Cold-Start Resilient
              </span>
            </div>

            {/* Feature 2 */}
            <div className="glass-card" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div
                style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--accent-blue-dim)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-blue)',
                }}
              >
                <Users size={24} />
              </div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                Collaborative Intelligence
              </h3>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                Builds an interaction matrix from rating histories. Discovers hidden culinary gems liked by foodies with taste patterns identical to yours, leading to delightful serendipity and exploration.
              </p>
              <span className="badge badge-blue" style={{ alignSelf: 'flex-start', marginTop: 'auto' }}>
                Crowd Wisdom
              </span>
            </div>

            {/* Feature 3 */}
            <div className="glass-card" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div
                style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--accent-gold-dim)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-gold)',
                }}
              >
                <Cpu size={24} />
              </div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                Tunable Hybrid Engine
              </h3>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                Merges models via Score = α · Content + (1 - α) · Collaborative. Our adaptive weighting adjusts α automatically as your rating history grows, or lets you tune the slider manually.
              </p>
              <span className="badge badge-gold" style={{ alignSelf: 'flex-start', marginTop: 'auto' }}>
                Configurable α Weighting
              </span>
            </div>
          </div>
        </div>

        {/* Bottom Banner */}
        <div
          className="glass-card"
          style={{
            padding: '40px 30px',
            textAlign: 'center',
            borderRadius: 'var(--radius-lg)',
            background: 'linear-gradient(135deg, rgba(0, 212, 170, 0.08) 0%, rgba(17, 24, 39, 0.8) 100%)',
            border: '1px solid var(--border-accent)',
          }}
        >
          <h2 style={{ fontSize: '1.7rem', fontWeight: '800', marginBottom: '10px' }}>
            Ready to find your next unforgettable meal?
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '580px', margin: '0 auto 24px auto' }}>
            Join thousands of food lovers using Tastify to discover restaurants that match their unique palate.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', flexWrap: 'wrap' }}>
            <Link to="/register" className="btn btn-primary btn-lg" style={{ gap: '8px' }}>
              Sign Up Free <ArrowRight size={16} />
            </Link>
            <Link to="/discover" className="btn btn-secondary btn-lg" style={{ gap: '8px' }}>
              Explore Live Recommendations
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
