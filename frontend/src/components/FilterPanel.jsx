import React, { useState } from 'react';
import { Filter, RotateCcw, ChevronDown, ChevronUp, Star, MapPin, DollarSign, Utensils, Armchair } from 'lucide-react';

const POPULAR_CUISINES = [
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
];

const AMBIENCE_OPTIONS = [
  'Casual',
  'Family',
  'Romantic',
  'Trendy',
  'Rooftop',
  'Fine Dining',
];

const PRICE_OPTIONS = [
  { label: '₹', title: 'Budget', value: 'Budget' },
  { label: '₹₹', title: 'Moderate', value: 'Moderate' },
  { label: '₹₹₹', title: 'Premium', value: 'Premium' },
  { label: '₹₹₹₹', title: 'Fine Dining', value: 'Fine Dining' },
];

export default function FilterPanel({
  filters = {
    cuisines: [],
    priceRanges: [],
    maxDistance: 50,
    minRating: 0,
  },
  onChange,
}) {
  const [mobileExpanded, setMobileExpanded] = useState(false);

  const activeCuisines = filters.cuisines || [];
  const activePrices = filters.priceRanges || [];
  const activeAmbiences = filters.ambiences || [];
  const maxDistance = filters.maxDistance ?? 50;
  const minRating = filters.minRating ?? 0;

  // Count active filters
  const activeFilterCount =
    activeCuisines.length +
    activePrices.length +
    activeAmbiences.length +
    (maxDistance < 50 ? 1 : 0) +
    (minRating > 0 ? 1 : 0);

  const toggleCuisine = (cuisine) => {
    let next;
    if (activeCuisines.includes(cuisine)) {
      next = activeCuisines.filter((c) => c !== cuisine);
    } else {
      next = [...activeCuisines, cuisine];
    }
    onChange({ ...filters, cuisines: next });
  };

  const togglePrice = (val) => {
    let next;
    if (activePrices.includes(val)) {
      next = activePrices.filter((p) => p !== val);
    } else {
      next = [...activePrices, val];
    }
    onChange({ ...filters, priceRanges: next });
  };

  const toggleAmbience = (amb) => {
    let next;
    if (activeAmbiences.includes(amb)) {
      next = activeAmbiences.filter((a) => a !== amb);
    } else {
      next = [...activeAmbiences, amb];
    }
    onChange({ ...filters, ambiences: next });
  };

  const handleDistanceChange = (e) => {
    onChange({ ...filters, maxDistance: Number(e.target.value) });
  };

  const handleRatingChange = (e) => {
    onChange({ ...filters, minRating: Number(e.target.value) });
  };

  const handleReset = () => {
    onChange({
      cuisines: [],
      priceRanges: [],
      ambiences: [],
      maxDistance: 50,
      minRating: 0,
    });
  };

  return (
    <div className="glass-card filter-panel">
      {/* Header with Mobile Accordion Toggle */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={18} style={{ color: 'var(--accent-teal)' }} />
          <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            Filters
          </h4>
          {activeFilterCount > 0 && (
            <span className="badge badge-teal" style={{ padding: '2px 8px', fontSize: '0.72rem' }}>
              {activeFilterCount} active
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {activeFilterCount > 0 && (
            <button
              type="button"
              onClick={handleReset}
              className="btn btn-ghost btn-sm"
              style={{ fontSize: '0.75rem', padding: '4px 8px', gap: '4px' }}
              title="Clear all filters"
            >
              <RotateCcw size={12} /> Clear
            </button>
          )}

          {/* Mobile Collapse Toggle Button */}
          <button
            type="button"
            className="btn btn-ghost btn-icon"
            onClick={() => setMobileExpanded(!mobileExpanded)}
            style={{ display: 'none' }}
            id="mobile-filter-toggle"
            aria-label="Toggle filter view"
          >
            {mobileExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>
      </div>

      {/* Filter Body (Always visible on desktop, toggleable on mobile via CSS/state) */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '22px',
        }}
      >
        {/* Cuisine Section */}
        <div className="filter-section">
          <div className="filter-title">
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Utensils size={14} style={{ color: 'var(--accent-teal)' }} /> Cuisines
            </span>
            {activeCuisines.length > 0 && (
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                {activeCuisines.length} selected
              </span>
            )}
          </div>
          <div className="chip-grid">
            {POPULAR_CUISINES.map((c) => {
              const active = activeCuisines.includes(c);
              return (
                <button
                  key={c}
                  type="button"
                  onClick={() => toggleCuisine(c)}
                  className={`chip-btn ${active ? 'active' : ''}`}
                >
                  {c}
                </button>
              );
            })}
          </div>
        </div>

        {/* Price Range Section */}
        <div className="filter-section">
          <div className="filter-title">
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <DollarSign size={14} style={{ color: 'var(--accent-gold)' }} /> Price Tier
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
            {PRICE_OPTIONS.map((opt) => {
              const active = activePrices.includes(opt.value);
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => togglePrice(opt.value)}
                  className={`btn ${active ? 'btn-gold' : 'btn-secondary'} btn-sm`}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    padding: '8px 4px',
                    gap: '2px',
                    fontSize: '0.85rem',
                  }}
                  title={opt.title}
                >
                  <span style={{ fontWeight: '800' }}>{opt.label}</span>
                  <span style={{ fontSize: '0.65rem', opacity: active ? 0.9 : 0.6 }}>{opt.title}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Ambience Section */}
        <div className="filter-section">
          <div className="filter-title">
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Armchair size={14} style={{ color: 'var(--accent-blue)' }} /> Ambience
            </span>
            {activeAmbiences.length > 0 && (
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                {activeAmbiences.length} selected
              </span>
            )}
          </div>
          <div className="chip-grid">
            {AMBIENCE_OPTIONS.map((a) => {
              const active = activeAmbiences.includes(a);
              return (
                <button
                  key={a}
                  type="button"
                  onClick={() => toggleAmbience(a)}
                  className={`chip-btn ${active ? 'active' : ''}`}
                >
                  {a}
                </button>
              );
            })}
          </div>
        </div>

        {/* Max Distance Section */}
        <div className="filter-section">
          <div className="filter-title">
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <MapPin size={14} style={{ color: 'var(--accent-teal)' }} /> Max Distance
            </span>
            <span style={{ fontSize: '0.82rem', fontWeight: '700', color: 'var(--accent-teal)' }}>
              {maxDistance} km
            </span>
          </div>
          <div>
            <input
              type="range"
              min="5"
              max="100"
              step="5"
              value={maxDistance}
              onChange={handleDistanceChange}
              aria-label="Max Distance"
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            <span>5 km</span>
            <span>25 km</span>
            <span>50 km</span>
            <span>100 km</span>
          </div>
        </div>

        {/* Min Rating Section */}
        <div className="filter-section">
          <div className="filter-title">
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Star size={14} style={{ color: 'var(--accent-gold)' }} /> Minimum Rating
            </span>
            <span style={{ fontSize: '0.82rem', fontWeight: '700', color: 'var(--accent-gold)' }}>
              {minRating > 0 ? `${minRating.toFixed(1)} ★` : 'Any'}
            </span>
          </div>
          <div>
            <input
              type="range"
              min="0"
              max="5"
              step="0.5"
              value={minRating}
              onChange={handleRatingChange}
              aria-label="Minimum Rating"
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            <span>Any</span>
            <span>3.0 ★</span>
            <span>4.0 ★</span>
            <span>5.0 ★</span>
          </div>
        </div>
      </div>
    </div>
  );
}
