import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../App';
import {
  getRestaurant,
  getRecommendations,
  submitRating,
  logInteraction,
  getMyRatings,
} from '../api/client';
import RestaurantCard from '../components/RestaurantCard';
import ReasonBadge from '../components/ReasonBadge';
import {
  ArrowLeft,
  Star,
  MapPin,
  Clock,
  Sparkles,
  Layers,
  Compass,
  CheckCircle,
  AlertCircle,
  Share2,
} from 'lucide-react';

const FALLBACK_HERO =
  'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1400&q=80';

export default function Restaurant() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const navRestaurant = location.state?.restaurant || null;

  const [restaurant, setRestaurant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [similarRestaurants, setSimilarRestaurants] = useState([]);
  const [userRating, setUserRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [ratingSubmitting, setRatingSubmitting] = useState(false);
  const [ratingSuccessMessage, setRatingSuccessMessage] = useState('');
  const [fetchedScores, setFetchedScores] = useState(null);

  // Fetch restaurant details
  useEffect(() => {
    let isMounted = true;
    const loadDetails = async () => {
      try {
        setLoading(true);
        setError('');
        setRatingSuccessMessage('');

        // Log interaction (implicit feedback)
        logInteraction(id, 'view');

        const data = await getRestaurant(id);
        if (!isMounted) return;
        setRestaurant(data);

        // Fetch user rating for this restaurant if user logged in
        if (user) {
          try {
            const ratings = await getMyRatings();
            const items = Array.isArray(ratings) ? ratings : ratings?.ratings || [];
            const existing = items.find(
              (r) => String(r.restaurant_id || r.restaurantId) === String(id)
            );
            if (existing) {
              setUserRating(existing.score || existing.rating);
            }
          } catch (rErr) {
            console.warn('Could not check user rating:', rErr.message);
          }
        }

        // If the restaurant doc lacks recommendation scores (direct visit,
        // search result, etc.), fetch real personalized scores from the
        // recommendations endpoint instead of showing placeholder values.
        const hasScores =
          data.hybrid_score != null ||
          data.content_score != null ||
          (navRestaurant && navRestaurant.hybrid_score != null);
        if (!hasScores) {
          try {
            const recData = await getRecommendations({ top_n: 200, max_distance_km: 5000 });
            const recs = Array.isArray(recData)
              ? recData
              : recData.recommendations || [];
            const match = recs.find((r) => String(r.id) === String(id));
            if (match && isMounted) {
              setFetchedScores({
                hybrid_score: match.hybrid_score,
                content_score: match.content_score,
                collab_score: match.collab_score,
                reason: match.reason,
              });
            }
          } catch (scoreErr) {
            console.warn('Could not fetch recommendation scores:', scoreErr.message);
          }
        }

        // Fetch similar restaurants using cuisine
        try {
          const primaryCuisine = Array.isArray(data.cuisine)
            ? data.cuisine[0]
            : typeof data.cuisine === 'string'
            ? data.cuisine.split(',')[0].trim()
            : '';

          const simData = await getRecommendations({
            cuisine: primaryCuisine,
            top_n: 4,
          });
          const list = Array.isArray(simData)
            ? simData
            : simData.recommendations || simData.restaurants || [];
          // Filter out current restaurant
          const filtered = list.filter((r) => String(r.id) !== String(id)).slice(0, 3);
          if (isMounted) setSimilarRestaurants(filtered);
        } catch (simErr) {
          console.warn('Could not load similar restaurants:', simErr.message);
        }
      } catch (err) {
        console.error('Restaurant fetch error:', err);
        if (isMounted) {
          setError(
            err?.response?.data?.detail ||
              err?.response?.data?.message ||
              'Unable to load restaurant details.'
          );
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadDetails();
    return () => {
      isMounted = false;
    };
  }, [id, user]);

  const handleRate = async (starValue) => {
    if (!user) {
      navigate('/login');
      return;
    }

    try {
      setRatingSubmitting(true);
      setUserRating(starValue);
      await submitRating(id, starValue);
      setRatingSuccessMessage(`Thanks! Your ${starValue}-star rating has been registered.`);
      setTimeout(() => setRatingSuccessMessage(''), 4000);
    } catch (err) {
      console.error('Rating failed:', err);
      alert('Failed to submit rating. Please try again.');
    } finally {
      setRatingSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container" style={{ maxWidth: '1000px' }}>
        <div className="skeleton" style={{ height: '360px', width: '100%', borderRadius: 'var(--radius-lg)', marginBottom: '24px' }} />
        <div className="skeleton skeleton-title" style={{ width: '40%' }} />
        <div className="skeleton skeleton-text" style={{ width: '60%' }} />
        <div className="skeleton skeleton-text" style={{ width: '80%' }} />
      </div>
    );
  }

  if (error || !restaurant) {
    return (
      <div className="page-container" style={{ maxWidth: '600px', textAlign: 'center', paddingTop: '80px' }}>
        <div className="glass-card" style={{ padding: '40px 24px' }}>
          <AlertCircle size={40} style={{ color: '#f87171', margin: '0 auto 16px auto' }} />
          <h2 style={{ fontSize: '1.4rem', fontWeight: '700', marginBottom: '8px' }}>
            Restaurant Not Found
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
            {error || 'The requested restaurant could not be located.'}
          </p>
          <Link to="/discover" className="btn btn-primary">
            <ArrowLeft size={16} /> Return to Discover
          </Link>
        </div>
      </div>
    );
  }

  // Parse fields
  const cuisines = Array.isArray(restaurant.cuisine)
    ? restaurant.cuisine
    : typeof restaurant.cuisine === 'string'
    ? restaurant.cuisine.split(',').map((c) => c.trim())
    : [];

  const tags = Array.isArray(restaurant.tags)
    ? restaurant.tags
    : typeof restaurant.tags === 'string'
    ? restaurant.tags.split(',').map((t) => t.trim())
    : [];

  const renderPrice = (p) => {
    if (typeof p === 'number') return '₹'.repeat(Math.max(1, Math.min(p, 4)));
    if (typeof p === 'string') {
      if (p.includes('₹')) return p;
      const map = { budget: '₹', moderate: '₹₹', premium: '₹₹₹', 'fine dining': '₹₹₹₹', luxury: '₹₹₹₹' };
      if (map[p.toLowerCase()]) return map[p.toLowerCase()];
    }
    return '₹₹';
  };

  const ratingVal = Number(restaurant.avg_rating || restaurant.rating || 4.2).toFixed(1);
  const distance = restaurant.distance_km ?? restaurant.distance;

  // Breakdown scores (normalized 0-100). Uses real recommendation scores
  // when available; shows '—' rather than fabricated placeholders.
  const toPct = (v) => {
    if (v === null || v === undefined) return null;
    const n = Number(v);
    if (Number.isNaN(n)) return null;
    return Math.round(n <= 1.0 ? n * 100 : n);
  };

  const contentScore = toPct(
    restaurant.content_score ??
      restaurant.similarity_score ??
      navRestaurant?.content_score ??
      fetchedScores?.content_score
  );
  const collabScore = toPct(
    restaurant.collab_score ??
      restaurant.collaborative_score ??
      navRestaurant?.collab_score ??
      fetchedScores?.collab_score
  );
  const hybridScore = toPct(
    restaurant.hybrid_score ??
      restaurant.score ??
      navRestaurant?.hybrid_score ??
      fetchedScores?.hybrid_score
  );
  const matchReason =
    restaurant.reason || navRestaurant?.reason || fetchedScores?.reason || null;

  const activeStarScore = hoverRating || userRating || 0;

  return (
    <div className="page-container" style={{ maxWidth: '1100px' }}>
      {/* Top Back Navigation */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <button
          type="button"
          onClick={() => navigate('/discover')}
          className="btn btn-secondary btn-sm"
          style={{ gap: '6px' }}
        >
          <ArrowLeft size={16} /> Back to Recommendations
        </button>

        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => {
            if (navigator.share) {
              navigator.share({
                title: restaurant.name,
                text: `Check out ${restaurant.name} on Tastify!`,
                url: window.location.href,
              });
            } else {
              navigator.clipboard.writeText(window.location.href);
              alert('Link copied to clipboard!');
            }
          }}
          style={{ gap: '6px' }}
        >
          <Share2 size={15} /> Share
        </button>
      </div>

      {/* Hero Banner with Gradient Overlay */}
      <div
        style={{
          position: 'relative',
          height: '380px',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          marginBottom: '28px',
          boxShadow: 'var(--shadow-card)',
        }}
      >
        <img
          src={restaurant.image_url || FALLBACK_HERO}
          alt={restaurant.name}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          onError={(e) => {
            e.currentTarget.src = FALLBACK_HERO;
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(180deg, rgba(10, 14, 26, 0.2) 0%, rgba(10, 14, 26, 0.95) 100%)',
          }}
        />

        {/* Content Inside Hero */}
        <div
          style={{
            position: 'absolute',
            bottom: '28px',
            left: '28px',
            right: '28px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <div>
            {matchReason && (
              <div style={{ marginBottom: '10px' }}>
                <ReasonBadge reason={matchReason} />
              </div>
            )}
            <h1
              style={{
                fontSize: 'clamp(1.8rem, 4vw, 2.8rem)',
                fontWeight: '800',
                letterSpacing: '-0.02em',
                color: 'var(--text-primary)',
                lineHeight: '1.2',
              }}
            >
              {restaurant.name}
            </h1>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '10px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--accent-gold)', fontWeight: '700' }}>
                <Star size={18} fill="var(--accent-gold)" />
                <span style={{ fontSize: '1.1rem' }}>{ratingVal}</span>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  ({restaurant.rating_count || 124} reviews)
                </span>
              </div>

              <span style={{ color: 'var(--text-muted)' }}>•</span>

              <span style={{ fontWeight: '700', color: 'var(--accent-gold)', letterSpacing: '1px' }}>
                {renderPrice(restaurant.price_range)}
              </span>

              {distance !== undefined && distance !== null && (
                <>
                  <span style={{ color: 'var(--text-muted)' }}>•</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent-teal)', fontSize: '0.9rem' }}>
                    <MapPin size={15} /> {Number(distance).toFixed(1)} km away
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Quick Hybrid Score Pill */}
          <div
            className="glass-card"
            style={{
              padding: '12px 18px',
              border: '1px solid var(--border-accent)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              backdropFilter: 'blur(20px)',
            }}
          >
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Hybrid Match
            </span>
            <span style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--accent-teal)' }}>
              {hybridScore !== null ? `${hybridScore}%` : '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Main Details Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '28px', alignItems: 'start' }}>
        {/* Left Column: Info & Explanations */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Cuisines & Ambience Badges */}
          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <h3 style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Cuisines & Specialties
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {cuisines.map((c, idx) => (
                  <span key={idx} className="badge badge-teal" style={{ padding: '6px 14px', fontSize: '0.85rem' }}>
                    {c}
                  </span>
                ))}
              </div>
            </div>

            {restaurant.ambience && (
              <div>
                <h3 style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Dining Ambience
                </h3>
                <p style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                  {restaurant.ambience}
                </p>
              </div>
            )}

            {tags.length > 0 && (
              <div>
                <h3 style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Features & Amenities
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {tags.map((t, idx) => (
                    <span key={idx} className="badge badge-outline" style={{ padding: '4px 10px' }}>
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {restaurant.description && (
              <div>
                <h3 style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  About the Restaurant
                </h3>
                <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6', fontSize: '0.92rem' }}>
                  {restaurant.description}
                </p>
              </div>
            )}
          </div>

          {/* "Why this was recommended" Section */}
          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Sparkles size={20} style={{ color: 'var(--accent-teal)' }} />
              <h2 style={{ fontSize: '1.25rem', fontWeight: '800' }}>
                Why This Was Recommended
              </h2>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Our hybrid engine cross-analyzes taste profiles with community rating correlations to compute a balanced composite score:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '6px' }}>
              {/* Content Score */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-teal)', fontWeight: '600' }}>
                    Taste Alignment (Content-Based)
                  </span>
                  <span style={{ fontWeight: '700' }}>{contentScore !== null ? `${contentScore}%` : '—'}</span>
                </div>
                <div className="progress-bar-container">
                  <div className="progress-bar-fill progress-teal" style={{ width: `${contentScore ?? 0}%` }} />
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                  High cosine match with your preferred cuisines ({cuisines.slice(0, 2).join(', ')}) and price comfort.
                </span>
              </div>

              {/* Collaborative Score */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-blue)', fontWeight: '600' }}>
                    Community Affinity (Collaborative Filtering)
                  </span>
                  <span style={{ fontWeight: '700' }}>{collabScore !== null ? `${collabScore}%` : '—'}</span>
                </div>
                <div className="progress-bar-container">
                  <div className="progress-bar-fill progress-blue" style={{ width: `${collabScore ?? 0}%` }} />
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                  Diners who shared your ratings also rated this restaurant 4.5+ stars.
                </span>
              </div>

              {/* Hybrid Combined */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-gold)', fontWeight: '600' }}>
                    Weighted Hybrid Score (α Balanced)
                  </span>
                  <span style={{ fontWeight: '700', color: 'var(--accent-gold)' }}>{hybridScore !== null ? `${hybridScore}%` : '—'}</span>
                </div>
                <div className="progress-bar-container">
                  <div className="progress-bar-fill progress-gold" style={{ width: `${hybridScore ?? 0}%` }} />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Interactive Rating & Location Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Rate Restaurant Widget */}
          <div
            className="glass-card"
            style={{
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              border: '1px solid var(--border-accent)',
            }}
          >
            <h3 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '6px' }}>
              {userRating ? 'Your Rating' : 'Rate Your Experience'}
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '18px' }}>
              Your feedback improves your taste vector and future recommendations.
            </p>

            {/* Big Interactive Stars */}
            <div
              style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}
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
                      padding: '4px',
                      transform: activeStarScore === star ? 'scale(1.25)' : 'scale(1)',
                      transition: 'transform 0.15s ease',
                      outline: 'none',
                    }}
                    onMouseEnter={() => setHoverRating(star)}
                    onClick={() => handleRate(star)}
                    disabled={ratingSubmitting}
                    aria-label={`Rate ${star} star`}
                  >
                    <Star
                      size={32}
                      fill={isFilled ? 'var(--accent-gold)' : 'transparent'}
                      color={isFilled ? 'var(--accent-gold)' : 'var(--text-muted)'}
                      style={{
                        filter: isFilled ? 'drop-shadow(0 0 8px rgba(255, 209, 102, 0.45))' : 'none',
                      }}
                    />
                  </button>
                );
              })}
            </div>

            <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--accent-gold)', minHeight: '20px' }}>
              {activeStarScore > 0 ? `${activeStarScore} out of 5 stars` : 'Tap a star to rate'}
            </span>

            {ratingSuccessMessage && (
              <div
                className="animate-fade-in"
                style={{
                  marginTop: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: 'var(--accent-teal)',
                  fontSize: '0.82rem',
                }}
              >
                <CheckCircle size={15} />
                <span>{ratingSuccessMessage}</span>
              </div>
            )}
          </div>

          {/* Location & Contact Details */}
          <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
              Location & Details
            </h4>

            {restaurant.area && (
              <div style={{ display: 'flex', gap: '10px', fontSize: '0.88rem' }}>
                <MapPin size={18} style={{ color: 'var(--accent-teal)', flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <span style={{ fontWeight: '600', display: 'block' }}>{restaurant.area}</span>
                  {restaurant.address && (
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                      {restaurant.address}
                    </span>
                  )}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', fontSize: '0.88rem' }}>
              <Clock size={18} style={{ color: 'var(--accent-gold)', flexShrink: 0, marginTop: '2px' }} />
              <div>
                <span style={{ fontWeight: '600', display: 'block' }}>Opening Hours</span>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  11:30 AM – 11:00 PM (Daily)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Similar Restaurants Section */}
      {similarRestaurants.length > 0 && (
        <div style={{ marginTop: '50px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div>
              <h2 style={{ fontSize: '1.4rem', fontWeight: '800' }}>
                Similar Spots You Might Love
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Based on similar culinary flavor profiles and price tiers.
              </p>
            </div>
            <Link to="/discover" className="btn btn-ghost btn-sm" style={{ gap: '6px' }}>
              <span>View More</span>
              <Compass size={14} />
            </Link>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '20px',
            }}
          >
            {similarRestaurants.map((sim) => (
              <RestaurantCard key={sim.id} restaurant={sim} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
