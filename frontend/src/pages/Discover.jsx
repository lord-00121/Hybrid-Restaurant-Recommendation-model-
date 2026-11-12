import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useAuth } from '../App';
import {
  getRecommendations,
  getRestaurants,
  searchRestaurants,
  submitRating,
  getMyRatings,
} from '../api/client';
import RestaurantCard from '../components/RestaurantCard';
import FilterPanel from '../components/FilterPanel';
import AlphaSlider from '../components/AlphaSlider';
import RatingModal from '../components/RatingModal';
import {
  Sparkles,
  Info,
  LogIn,
  RefreshCw,
  SearchX,
  Layers,
  ChevronDown,
  MapPin,
  Navigation,
} from 'lucide-react';

export default function Discover() {
  const { user } = useAuth();
  const location = useLocation();

  // Read search query from URL (?q=...)
  const searchParams = new URLSearchParams(location.search);
  const searchQuery = searchParams.get('q') || '';

  // State from location (e.g. onboarding)
  const locationPrefs = location.state?.preferences;

  // Filter state
  const [filters, setFilters] = useState({
    cuisines: locationPrefs?.cuisines || [],
    priceRanges: locationPrefs?.budget ? [locationPrefs.budget] : [],
    ambiences: [],
    maxDistance: 50,
    minRating: 0,
  });

  // User geolocation state (null = not set)
  const [userCoords, setUserCoords] = useState(() => {
    try {
      const saved = localStorage.getItem('tastify_user_coords');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [locating, setLocating] = useState(false);
  const [locationError, setLocationError] = useState('');

  // Alpha slider state (undefined = auto)
  const [alpha, setAlpha] = useState(undefined);

  // Data states
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [alphaUsed, setAlphaUsed] = useState(0.5);
  const [ratingCount, setRatingCount] = useState(0);
  const [userRatings, setUserRatings] = useState({});
  const [displayCount, setDisplayCount] = useState(12);

  // Rating Modal state
  const [selectedRestaurantForRating, setSelectedRestaurantForRating] = useState(null);

  // Fetch user ratings on mount
  useEffect(() => {
    let isMounted = true;
    const fetchUserRatings = async () => {
      if (!user) return;
      try {
        const ratingsData = await getMyRatings();
        if (isMounted && ratingsData) {
          const map = {};
          const items = Array.isArray(ratingsData) ? ratingsData : ratingsData.ratings || [];
          items.forEach((r) => {
            const restId = r.restaurant_id || r.restaurantId;
            map[restId] = r.score || r.rating;
          });
          setUserRatings(map);
          setRatingCount(items.length);
        }
      } catch (err) {
        console.warn('Could not fetch user ratings:', err.message);
      }
    };
    fetchUserRatings();
    return () => { isMounted = false; };
  }, [user]);

  // Debounced fetch for recommendations
  const debounceTimerRef = useRef(null);

  const fetchRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      const params = {
        top_n: 30,
        max_distance_km: filters.maxDistance,
      };

      if (filters.cuisines.length > 0) {
        params.cuisine = filters.cuisines.join(',');
      }
      if (filters.priceRanges.length > 0) {
        params.price_range = filters.priceRanges.join(',');
      }
      if (filters.ambiences && filters.ambiences.length > 0) {
        params.ambience = filters.ambiences.join(',');
      }
      if (userCoords) {
        params.user_lat = userCoords.lat;
        params.user_lng = userCoords.lng;
      }
      if (alpha !== undefined && alpha !== null) {
        params.alpha = alpha;
      }

      let data;
      try {
        if (searchQuery.trim()) {
          // Use search API when a query is present from the Navbar
          data = await searchRestaurants(searchQuery.trim());
        } else {
          data = await getRecommendations(params);
        }
      } catch (apiErr) {
        console.warn('getRecommendations/search failed, falling back to getRestaurants:', apiErr.message);
        data = await getRestaurants(params);
      }

      let items = [];
      let usedA = 0.5;
      let countR = ratingCount;

      if (Array.isArray(data)) {
        items = data;
      } else if (data && typeof data === 'object') {
        items = data.recommendations || data.restaurants || data.items || [];
        if (data.alpha_used !== undefined) usedA = data.alpha_used;
        if (data.user_rating_count !== undefined) countR = data.user_rating_count;
      }

      // Filter by minRating client-side if specified
      if (filters.minRating > 0) {
        items = items.filter(
          (r) => Number(r.avg_rating || r.rating || 0) >= filters.minRating
        );
      }

      setRestaurants(items);
      setAlphaUsed(usedA);
      setRatingCount(countR);
    } catch (err) {
      console.error('Fetch error:', err);
      setError('Unable to load recommendations. Please check your connection or try again.');
    } finally {
      setLoading(false);
    }
  }, [filters, alpha, ratingCount, searchQuery, userCoords]);

  // Request browser geolocation
  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser.');
      return;
    }
    setLocating(true);
    setLocationError('');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords = {
          lat: Number(pos.coords.latitude.toFixed(6)),
          lng: Number(pos.coords.longitude.toFixed(6)),
        };
        setUserCoords(coords);
        try {
          localStorage.setItem('tastify_user_coords', JSON.stringify(coords));
        } catch (e) {
          console.warn(e);
        }
        setLocating(false);
      },
      (err) => {
        setLocating(false);
        setLocationError(
          err.code === err.PERMISSION_DENIED
            ? 'Location permission denied. Please allow location access.'
            : 'Unable to determine your location. Please try again.'
        );
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 600000 }
    );
  };

  const handleClearLocation = () => {
    setUserCoords(null);
    setLocationError('');
    try {
      localStorage.removeItem('tastify_user_coords');
    } catch (e) {
      console.warn(e);
    }
  };

  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = setTimeout(() => {
      fetchRecommendations();
    }, 280);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [fetchRecommendations]);

  // Handle inline star rating or modal trigger
  const handleRate = async (restaurantId, score) => {
    if (!user) {
      // Find restaurant to show in modal or redirect to login
      const r = restaurants.find((item) => item.id === restaurantId);
      if (r) {
        setSelectedRestaurantForRating(r);
      }
      return;
    }

    try {
      // Optimistic update
      setUserRatings((prev) => ({
        ...prev,
        [restaurantId]: score,
      }));
      setRatingCount((prev) => prev + 1);

      await submitRating(restaurantId, score);
    } catch (err) {
      console.error('Error submitting rating:', err);
      // Revert if error
      setUserRatings((prev) => {
        const next = { ...prev };
        delete next[restaurantId];
        return next;
      });
    }
  };

  const handleModalSubmitRating = async (restaurantId, score) => {
    await handleRate(restaurantId, score);
  };

  const currentAlphaDisplay = alpha !== undefined && alpha !== null ? alpha : alphaUsed;
  const contentPct = Math.round(currentAlphaDisplay * 100);
  const collabPct = 100 - contentPct;

  const visibleRestaurants = restaurants.slice(0, displayCount);

  return (
    <div className="page-container">
      {/* Non-logged in banner */}
      {!user && (
        <div
          className="glass-card animate-fade-in"
          style={{
            padding: '16px 20px',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
            flexWrap: 'wrap',
            border: '1px solid var(--border-accent)',
            background: 'linear-gradient(90deg, rgba(0,212,170,0.1) 0%, rgba(17,24,39,0.7) 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '1.4rem' }}>✨</span>
            <div>
              <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                Exploring in Guest Mode
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                Sign in to save ratings, personalize your taste vector, and activate collaborative crowd filtering.
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <Link to="/login" className="btn btn-secondary btn-sm" style={{ gap: '6px' }}>
              <LogIn size={14} /> Log In
            </Link>
            <Link to="/register" className="btn btn-primary btn-sm">
              Sign Up Free
            </Link>
          </div>
        </div>
      )}

      {/* Main Discover Layout: Sidebar + Grid */}
      <div className="discover-layout">
        {/* Left Sidebar */}
        <aside className="discover-sidebar">
          {/* Alpha Tuning Slider */}
          <AlphaSlider value={alpha} onChange={setAlpha} />

          {/* Filters Panel */}
          <FilterPanel filters={filters} onChange={setFilters} />
        </aside>

        {/* Right Main Content */}
        <main className="discover-content">
          {/* Header Bar */}
          <div
            className="glass-card"
            style={{
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <h1 style={{ fontSize: '1.5rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                  {searchQuery
                    ? `Search Results for "${searchQuery}"`
                    : user
                      ? `Top Picks for ${user.name || 'You'}`
                      : 'Top Recommended Restaurants'}
                </h1>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {loading
                    ? (searchQuery ? 'Searching...' : 'Recalculating hybrid vectors...')
                    : `${restaurants.length} ${searchQuery ? 'results' : 'curated restaurants'} found`}
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                {userCoords ? (
                  <>
                    <span
                      className="badge badge-teal"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '6px 12px' }}
                      title={`Lat ${userCoords.lat}, Lng ${userCoords.lng}`}
                    >
                      <Navigation size={12} /> Near me ({userCoords.lat.toFixed(2)}, {userCoords.lng.toFixed(2)})
                    </span>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={handleClearLocation}
                      style={{ fontSize: '0.75rem' }}
                    >
                      Clear
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleUseMyLocation}
                    disabled={locating}
                    style={{ gap: '6px' }}
                    title="Use your current location to find nearby restaurants"
                  >
                    <MapPin size={14} style={{ color: 'var(--accent-teal)' }} />
                    {locating ? 'Locating...' : 'Near Me'}
                  </button>
                )}
                <button
                  type="button"
                  onClick={fetchRecommendations}
                  className="btn btn-secondary btn-sm"
                  style={{ gap: '6px' }}
                  title="Refresh recommendations"
                  disabled={loading}
                >
                  <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                  <span>Refresh</span>
                </button>
              </div>
            </div>

            {/* Recommendation Explanation & Meta */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                background: 'rgba(255, 255, 255, 0.02)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)',
                flexWrap: 'wrap',
                fontSize: '0.82rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-teal)' }}>
                <Info size={15} />
                <span style={{ fontWeight: '600' }}>Hybrid Weighting:</span>
              </div>
              <span style={{ color: 'var(--text-primary)' }}>
                We're blending <strong>{contentPct}%</strong> your taste profile with <strong>{collabPct}%</strong> community favorites.
              </span>
              <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
                <span className="badge badge-outline">
                  <Layers size={11} /> α = {Number(currentAlphaDisplay).toFixed(2)}
                </span>
                {user && (
                  <span className="badge badge-teal">
                    ★ {ratingCount} ratings recorded
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Location Error Notice */}
          {locationError && (
            <div
              className="glass-card"
              style={{
                padding: '12px 16px',
                marginBottom: '16px',
                background: 'rgba(245, 158, 11, 0.1)',
                borderColor: 'rgba(245, 158, 11, 0.3)',
                color: '#fbbf24',
                fontSize: '0.85rem',
              }}
            >
              {locationError}
            </div>
          )}

          {/* Error Notice */}
          {error && (
            <div
              className="glass-card"
              style={{
                padding: '16px',
                background: 'rgba(239, 68, 68, 0.1)',
                borderColor: 'rgba(239, 68, 68, 0.3)',
                color: '#f87171',
                fontSize: '0.88rem',
              }}
            >
              {error}
            </div>
          )}

          {/* Loading Skeletons */}
          {loading && restaurants.length === 0 ? (
            <div className="discover-grid">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <RestaurantCard key={i} skeleton={true} />
              ))}
            </div>
          ) : visibleRestaurants.length > 0 ? (
            <>
              {/* Restaurant Cards Grid */}
              <div className="discover-grid">
                {visibleRestaurants.map((restaurant) => (
                  <RestaurantCard
                    key={restaurant.id}
                    restaurant={restaurant}
                    userRating={userRatings[restaurant.id]}
                    onRate={handleRate}
                  />
                ))}
              </div>

              {/* Load More Button */}
              {displayCount < restaurants.length && (
                <div style={{ textAlign: 'center', marginTop: '16px' }}>
                  <button
                    type="button"
                    onClick={() => setDisplayCount((prev) => prev + 12)}
                    className="btn btn-secondary"
                    style={{ gap: '8px' }}
                  >
                    <span>Load More Restaurants ({restaurants.length - displayCount} remaining)</span>
                    <ChevronDown size={16} />
                  </button>
                </div>
              )}
            </>
          ) : (
            /* Empty State */
            <div
              className="glass-card"
              style={{
                textAlign: 'center',
                padding: '60px 20px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '16px',
              }}
            >
              <div
                style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  background: 'rgba(255, 255, 255, 0.04)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--text-muted)',
                }}
              >
                <SearchX size={32} />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '700' }}>
                No restaurants match your active criteria
              </h3>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', maxWidth: '420px' }}>
                Try widening your distance limit, clearing cuisine filters, or adjusting your minimum star rating.
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() =>
                  setFilters({
                    cuisines: [],
                    priceRanges: [],
                    ambiences: [],
                    maxDistance: 50,
                    minRating: 0,
                  })
                }
                style={{ marginTop: '8px' }}
              >
                Reset All Filters
              </button>
            </div>
          )}
        </main>
      </div>

      {/* Rating Modal */}
      <RatingModal
        isOpen={Boolean(selectedRestaurantForRating)}
        restaurant={selectedRestaurantForRating}
        initialRating={selectedRestaurantForRating ? userRatings[selectedRestaurantForRating.id] || 0 : 0}
        onClose={() => setSelectedRestaurantForRating(null)}
        onSubmitRating={handleModalSubmitRating}
      />
    </div>
  );
}
