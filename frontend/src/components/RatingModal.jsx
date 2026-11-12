import React, { useState, useEffect } from 'react';
import { Star, X, Check } from 'lucide-react';

export default function RatingModal({
  isOpen,
  restaurant,
  initialRating = 0,
  onClose,
  onSubmitRating,
}) {
  const [rating, setRating] = useState(initialRating);
  const [hoverRating, setHoverRating] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setRating(initialRating || 0);
      setHoverRating(0);
      setError('');
    }
  }, [isOpen, initialRating]);

  if (!isOpen || !restaurant) return null;

  const scoreLabels = {
    1: 'Needs Improvement 😕',
    2: 'Fair Experience 😐',
    3: 'Good Food & Ambience 🙂',
    4: 'Very Good, Recommended! 😋',
    5: 'Exceptional, Absolute Favorite! 🌟',
  };

  const activeScore = hoverRating || rating;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!rating || rating < 1) {
      setError('Please select at least 1 star');
      return;
    }

    try {
      setSubmitting(true);
      setError('');
      await onSubmitRating(restaurant.id, rating);
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || err?.response?.data?.message || 'Failed to submit rating. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <span className="badge badge-teal" style={{ marginBottom: '6px' }}>Rate Experience</span>
            <h3 style={{ fontSize: '1.35rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              {restaurant.name}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Your rating refines future hybrid recommendations for you and the community.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-ghost btn-icon"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: '#f87171',
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            marginBottom: '16px'
          }}>
            {error}
          </div>
        )}

        {/* Star Rating Area */}
        <form onSubmit={handleSubmit}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px 10px',
            background: 'rgba(255, 255, 255, 0.02)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border)',
            marginBottom: '24px'
          }}>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '14px' }}>
              {[1, 2, 3, 4, 5].map((starVal) => {
                const isFilled = starVal <= activeScore;
                return (
                  <button
                    key={starVal}
                    type="button"
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '4px',
                      transform: activeScore === starVal ? 'scale(1.2)' : 'scale(1)',
                      transition: 'transform 0.15s ease',
                      outline: 'none',
                    }}
                    onMouseEnter={() => setHoverRating(starVal)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={() => setRating(starVal)}
                    aria-label={`Rate ${starVal} out of 5 stars`}
                  >
                    <Star
                      size={36}
                      fill={isFilled ? 'var(--accent-gold)' : 'transparent'}
                      color={isFilled ? 'var(--accent-gold)' : 'var(--text-muted)'}
                      style={{
                        filter: isFilled ? 'drop-shadow(0 0 8px rgba(255, 209, 102, 0.5))' : 'none',
                        transition: 'filter 0.2s ease, fill 0.2s ease',
                      }}
                    />
                  </button>
                );
              })}
            </div>

            <div style={{ height: '24px', textAlign: 'center' }}>
              <span style={{
                fontSize: '0.9rem',
                fontWeight: '600',
                color: activeScore ? 'var(--accent-gold)' : 'var(--text-muted)',
                transition: 'color 0.2s ease'
              }}>
                {activeScore ? scoreLabels[activeScore] : 'Click stars to score'}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || rating === 0}
            >
              {submitting ? 'Submitting...' : (
                <>
                  <Check size={16} /> Submit Rating
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
