import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, MapPin, Zap } from 'lucide-react';
import ReasonBadge from './ReasonBadge';

// Curated high quality food fallbacks
const FALLBACK_IMAGES = [
  'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=700&q=80',
  'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=700&q=80',
  'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=700&q=80',
  'https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=700&q=80',
  'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=700&q=80'
];

export default function RestaurantCard({
  restaurant,
  userRating,
  onRate,
  skeleton = false,
}) {
  const navigate = useNavigate();
  const [imgError, setImgError] = useState(false);
  const [hoverRating, setHoverRating] = useState(0);

  if (skeleton) {
    return (
      <div className="restaurant-card skeleton-card">
        <div className="skeleton" style={{ height: '180px', width: '100%' }} />
        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div className="skeleton skeleton-title" style={{ width: '70%' }} />
          <div style={{ display: 'flex', gap: '8px' }}>
            <div className="skeleton" style={{ height: '22px', width: '60px', borderRadius: '12px' }} />
            <div className="skeleton" style={{ height: '22px', width: '75px', borderRadius: '12px' }} />
          </div>
          <div className="skeleton skeleton-text" style={{ width: '40%' }} />
          <div className="skeleton" style={{ height: '10px', width: '100%', marginTop: '12px', borderRadius: '4px' }} />
        </div>
      </div>
    );
  }

  if (!restaurant) return null;

  // Format cuisines
  const cuisines = Array.isArray(restaurant.cuisine)
    ? restaurant.cuisine
    : typeof restaurant.cuisine === 'string'
    ? restaurant.cuisine.split(',').map((c) => c.trim())
    : [];

  // Format price display
  const renderPrice = (price) => {
    if (typeof price === 'number') {
      return '₹'.repeat(Math.max(1, Math.min(price, 4)));
    }
    if (typeof price === 'string') {
      if (price.includes('₹')) return price;
      if (price.toLowerCase() === 'budget') return '₹';
      if (price.toLowerCase() === 'moderate') return '₹₹';
      if (price.toLowerCase() === 'premium') return '₹₹₹';
      if (price.toLowerCase() === 'fine dining' || price.toLowerCase() === 'luxury') return '₹₹₹₹';
    }
    return '₹₹';
  };

  // Format scores
  const rawScore = restaurant.hybrid_score ?? restaurant.score ?? restaurant.match_score;
  const matchPercentage =
    rawScore !== undefined && rawScore !== null
      ? Math.round(rawScore <= 1.0 ? rawScore * 100 : rawScore)
      : null;

  const ratingVal = Number(restaurant.avg_rating || restaurant.rating || 4.2).toFixed(1);
  const distance = restaurant.distance_km ?? restaurant.distance;

  // Image source with index-based fallback
  const fallbackImg = FALLBACK_IMAGES[(restaurant.id || 0) % FALLBACK_IMAGES.length];
  const imgSrc = imgError || !restaurant.image_url ? fallbackImg : restaurant.image_url;

  const handleCardClick = () => {
    navigate(`/restaurant/${restaurant.id}`, { state: { restaurant } });
  };

  const handleInlineRate = (e, star) => {
    e.stopPropagation();
    if (onRate) {
      onRate(restaurant.id, star);
    }
  };

  const activeStarScore = hoverRating || userRating || restaurant.my_rating || 0;

  return (
    <div
      className="restaurant-card glass-card-hover"
      onClick={handleCardClick}
      role="article"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleCardClick()}
    >
      {/* Image Banner */}
      <div className="restaurant-card-image-wrap">
        <img
          src={imgSrc}
          alt={restaurant.name}
          className="restaurant-card-img"
          onError={() => setImgError(true)}
          loading="lazy"
        />
        <div className="restaurant-card-overlay" />

        {/* Top Badges: Reason & Distance */}
        <div className="restaurant-card-top-badges">
          <div>
            {restaurant.reason && <ReasonBadge reason={restaurant.reason} />}
          </div>
          {distance !== undefined && distance !== null && (
            <span className="badge badge-outline" style={{ background: 'rgba(10, 14, 26, 0.75)', backdropFilter: 'blur(4px)' }}>
              <MapPin size={11} style={{ color: 'var(--accent-teal)' }} />
              {Number(distance).toFixed(1)} km
            </span>
          )}
        </div>
      </div>

      {/* Card Body */}
      <div className="restaurant-card-body">
        {/* Title and Rating */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
          <h3 className="restaurant-card-title">{restaurant.name}</h3>
          <div className="restaurant-card-rating">
            <Star size={15} fill="var(--accent-gold)" color="var(--accent-gold)" />
            <span>{ratingVal}</span>
          </div>
        </div>

        {/* Cuisines and Price */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
          <div className="restaurant-card-cuisines">
            {cuisines.slice(0, 3).map((cuisine, idx) => (
              <span key={idx} className="badge badge-outline" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>
                {cuisine}
              </span>
            ))}
            {cuisines.length > 3 && (
              <span className="badge badge-outline" style={{ fontSize: '0.7rem', padding: '2px 6px' }}>
                +{cuisines.length - 3}
              </span>
            )}
          </div>
          <span style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--accent-gold)', letterSpacing: '1px' }}>
            {renderPrice(restaurant.price_range)}
          </span>
        </div>

        {/* Area/Location */}
        {restaurant.area && (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <MapPin size={13} style={{ color: 'var(--text-muted)' }} />
            <span>{restaurant.area}</span>
          </div>
        )}

        {/* Hybrid Score Progress Bar */}
        {matchPercentage !== null && (
          <div className="restaurant-card-score">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
              <span style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Zap size={12} style={{ color: 'var(--accent-teal)' }} /> Hybrid Match
              </span>
              <span style={{ color: 'var(--accent-teal)', fontWeight: '700' }}>
                {matchPercentage}%
              </span>
            </div>
            <div className="progress-bar-container">
              <div
                className="progress-bar-fill progress-teal"
                style={{ width: `${Math.min(100, Math.max(5, matchPercentage))}%` }}
              />
            </div>
          </div>
        )}

        {/* Inline User Rating */}
        <div className="restaurant-card-inline-rating" onClick={(e) => e.stopPropagation()}>
          <span style={{ fontSize: '0.75rem', color: userRating ? 'var(--accent-gold)' : 'var(--text-muted)' }}>
            {userRating ? `Your rating: ${userRating}★` : 'Rate:'}
          </span>
          <div
            style={{ display: 'flex', gap: '4px' }}
            onMouseLeave={() => setHoverRating(0)}
          >
            {[1, 2, 3, 4, 5].map((star) => {
              const isFilled = star <= activeStarScore;
              return (
                <button
                  key={star}
                  type="button"
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '2px',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                  onMouseEnter={() => setHoverRating(star)}
                  onClick={(e) => handleInlineRate(e, star)}
                  title={`Rate ${star} star${star > 1 ? 's' : ''}`}
                >
                  <Star
                    size={15}
                    fill={isFilled ? 'var(--accent-gold)' : 'transparent'}
                    color={isFilled ? 'var(--accent-gold)' : 'var(--text-muted)'}
                  />
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
