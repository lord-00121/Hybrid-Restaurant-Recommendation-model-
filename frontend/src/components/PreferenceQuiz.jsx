import React, { useState } from 'react';
import {
  UtensilsCrossed,
  Leaf,
  Wallet,
  Armchair,
  MapPin,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  Check,
  X,
} from 'lucide-react';

const CUISINE_OPTIONS = [
  'North Indian',
  'South Indian',
  'Chinese',
  'Italian',
  'Continental',
  'Cafe',
  'Asian',
  'Mexican',
  'Biryani',
  'Desserts',
  'Fast Food',
  'Japanese',
  'Mughlai',
  'Thai',
  'Pizza',
];

const DIET_OPTIONS = [
  { id: 'Any', label: 'No Restrictions', desc: 'Open to everything' },
  { id: 'Vegetarian', label: 'Vegetarian', desc: 'Plant & dairy dishes' },
  { id: 'Non-Vegetarian', label: 'Non-Vegetarian', desc: 'Meat, seafood & poultry' },
  { id: 'Vegan', label: 'Vegan', desc: 'Fully plant-based' },
];

const BUDGET_OPTIONS = [
  { id: 'Budget', label: 'Budget', desc: 'Under ₹500', symbol: '₹' },
  { id: 'Moderate', label: 'Moderate', desc: '₹500 – ₹1200', symbol: '₹₹' },
  { id: 'Premium', label: 'Premium', desc: '₹1200 – ₹2500', symbol: '₹₹₹' },
  { id: 'Fine Dining', label: 'Fine Dining', desc: '₹2500+', symbol: '₹₹₹₹' },
];

const AMBIENCE_OPTIONS = [
  'Casual',
  'Family',
  'Romantic',
  'Trendy',
  'Rooftop',
  'Fine Dining',
];

const CITY_OPTIONS = [
  'Delhi',
  'Mumbai',
  'Bangalore',
  'Hyderabad',
  'Chennai',
  'Pune',
  'Kolkata',
];

const TOTAL_STEPS = 5;

export default function PreferenceQuiz({ initialPrefs = {}, onComplete, onSkip }) {
  const [step, setStep] = useState(1);
  const [answers, setAnswers] = useState({
    cuisines: initialPrefs.cuisines || [],
    diet: Array.isArray(initialPrefs.diet) && initialPrefs.diet.length > 0
      ? initialPrefs.diet[0]
      : initialPrefs.diet || 'Any',
    budget: initialPrefs.budget || 'Moderate',
    ambience: initialPrefs.ambience || [],
    location: initialPrefs.location || '',
  });

  const toggleInList = (list, value) =>
    list.includes(value) ? list.filter((v) => v !== value) : [...list, value];

  const canProceed = () => {
    switch (step) {
      case 2:
        return answers.cuisines.length > 0;
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (step < TOTAL_STEPS) {
      setStep(step + 1);
    } else {
      onComplete({
        cuisines: answers.cuisines,
        diet: answers.diet === 'Any' ? [] : [answers.diet],
        budget: answers.budget,
        ambience: answers.ambience,
        location: answers.location,
      });
    }
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const progressPct = (step / TOTAL_STEPS) * 100;

  return (
    <div
      style={{
        width: '100%',
        maxWidth: '560px',
        margin: '0 auto',
        background: 'rgba(17, 24, 39, 0.75)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: '32px',
        boxShadow: 'var(--shadow-lg)',
      }}
    >
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
          }}
        >
          <Sparkles size={18} style={{ color: 'var(--accent-gold)' }} />
          <span className="badge badge-gold">Personalization Quiz</span>
        </div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '6px' }}>
          {step === 1 ? 'Welcome aboard! 🎉' : `Question ${step - 1} of ${TOTAL_STEPS - 1}`}
        </h2>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
          {step === 1
            ? 'Answer a few quick questions so we can personalize your restaurant recommendations from day one.'
            : step === 2
            ? 'Which cuisines do you enjoy? (pick at least one)'
            : step === 3
            ? 'Any dietary preferences we should respect?'
            : step === 4
            ? 'What kind of budget and vibe are you looking for?'
            : 'Where are you based? This helps us find restaurants near you.'}
        </p>
      </div>

      {/* Progress Bar */}
      <div
        style={{
          height: '6px',
          background: 'rgba(255,255,255,0.06)',
          borderRadius: '3px',
          marginBottom: '28px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progressPct}%`,
            background: 'linear-gradient(90deg, var(--accent-teal), var(--accent-gold))',
            borderRadius: '3px',
            transition: 'width 0.3s ease',
          }}
        />
      </div>

      {/* Step Content */}
      <div style={{ minHeight: '220px' }}>
        {/* Step 1: Welcome */}
        {step === 1 && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🍽️✨</div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: '1.6' }}>
              Our hybrid engine combines <strong style={{ color: 'var(--accent-teal)' }}>content-based</strong> matching
              (your stated tastes) with <strong style={{ color: 'var(--accent-gold)' }}>collaborative</strong> wisdom
              (what similar food lovers enjoy). This quiz solves the cold-start problem so your very first
              recommendations are already spot-on.
            </p>
          </div>
        )}

        {/* Step 2: Cuisines */}
        {step === 2 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <UtensilsCrossed size={18} style={{ color: 'var(--accent-teal)' }} />
              <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>Favorite Cuisines</span>
              {answers.cuisines.length > 0 && (
                <span className="badge badge-teal" style={{ marginLeft: 'auto' }}>
                  {answers.cuisines.length} selected
                </span>
              )}
            </div>
            <div className="chip-grid" style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
              {CUISINE_OPTIONS.map((c) => {
                const active = answers.cuisines.includes(c);
                return (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setAnswers({ ...answers, cuisines: toggleInList(answers.cuisines, c) })}
                    className={`chip-btn ${active ? 'active' : ''}`}
                    style={{ padding: '8px 16px', fontSize: '0.85rem' }}
                  >
                    {active && <Check size={13} style={{ marginRight: '4px' }} />}
                    {c}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Step 3: Diet */}
        {step === 3 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <Leaf size={18} style={{ color: 'var(--accent-teal)' }} />
              <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>Dietary Preference</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {DIET_OPTIONS.map((d) => {
                const active = answers.diet === d.id;
                return (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => setAnswers({ ...answers, diet: d.id })}
                    className={`btn ${active ? 'btn-primary' : 'btn-secondary'}`}
                    style={{
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      padding: '14px 16px',
                      textAlign: 'left',
                      gap: '4px',
                    }}
                  >
                    <span style={{ fontWeight: '700', fontSize: '0.9rem' }}>{d.label}</span>
                    <span style={{ fontSize: '0.75rem', opacity: 0.75 }}>{d.desc}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Step 4: Budget + Ambience */}
        {step === 4 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Wallet size={18} style={{ color: 'var(--accent-gold)' }} />
                <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>Budget Range</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {BUDGET_OPTIONS.map((b) => {
                  const active = answers.budget === b.id;
                  return (
                    <button
                      key={b.id}
                      type="button"
                      onClick={() => setAnswers({ ...answers, budget: b.id })}
                      className={`btn ${active ? 'btn-gold' : 'btn-secondary'}`}
                      style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px 14px', gap: '2px' }}
                    >
                      <span style={{ fontWeight: '800', fontSize: '0.95rem' }}>{b.symbol} {b.label}</span>
                      <span style={{ fontSize: '0.72rem', opacity: 0.75 }}>{b.desc}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Armchair size={18} style={{ color: 'var(--accent-blue)' }} />
                <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>Preferred Ambience</span>
                {answers.ambience.length > 0 && (
                  <span className="badge badge-teal" style={{ marginLeft: 'auto' }}>
                    {answers.ambience.length} selected
                  </span>
                )}
              </div>
              <div className="chip-grid" style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                {AMBIENCE_OPTIONS.map((a) => {
                  const active = answers.ambience.includes(a);
                  return (
                    <button
                      key={a}
                      type="button"
                      onClick={() => setAnswers({ ...answers, ambience: toggleInList(answers.ambience, a) })}
                      className={`chip-btn ${active ? 'active' : ''}`}
                      style={{ padding: '8px 16px', fontSize: '0.85rem' }}
                    >
                      {a}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Step 5: Location */}
        {step === 5 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <MapPin size={18} style={{ color: 'var(--accent-teal)' }} />
              <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>Your City</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '16px' }}>
              {CITY_OPTIONS.map((city) => {
                const active = answers.location === city;
                return (
                  <button
                    key={city}
                    type="button"
                    onClick={() => setAnswers({ ...answers, location: city })}
                    className={`chip-btn ${active ? 'active' : ''}`}
                    style={{ padding: '8px 18px', fontSize: '0.88rem' }}
                  >
                    {city}
                  </button>
                );
              })}
            </div>
            <input
              type="text"
              className="form-input"
              placeholder="Or type your city / area..."
              value={answers.location}
              onChange={(e) => setAnswers({ ...answers, location: e.target.value })}
              style={{ width: '100%' }}
            />
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '10px' }}>
              💡 You can also use the "Near Me" button on the Discover page for precise GPS-based distance filtering.
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '28px' }}>
        <div>
          {step > 1 && (
            <button type="button" className="btn btn-ghost btn-sm" onClick={handleBack} style={{ gap: '6px' }}>
              <ChevronLeft size={16} /> Back
            </button>
          )}
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {onSkip && step < TOTAL_STEPS && (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={onSkip}
              style={{ fontSize: '0.78rem' }}
            >
              <X size={14} /> Skip
            </button>
          )}
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleNext}
            disabled={!canProceed()}
            style={{ gap: '6px' }}
          >
            {step === TOTAL_STEPS ? (
              <>
                <Check size={16} /> Finish & Get Recommendations
              </>
            ) : (
              <>
                Next <ChevronRight size={16} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
