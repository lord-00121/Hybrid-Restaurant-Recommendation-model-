import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../App';
import api, {
  getRestaurants,
  createRestaurant,
  updateRestaurant,
  deleteRestaurant,
} from '../api/client';
import {
  ShieldAlert,
  Plus,
  Edit2,
  Trash2,
  Search,
  Building,
  Star,
  Users,
  Utensils,
  X,
  Check,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';

const INITIAL_FORM_STATE = {
  name: '',
  cuisine: '',
  price_range: 'Moderate',
  avg_rating: 4.2,
  area: '',
  lat: 12.9716,
  lng: 77.5946,
  ambience: '',
  tags: '',
  description: '',
  image_url: '',
};

export default function Admin() {
  const { user } = useAuth();

  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState('');
  const [stats, setStats] = useState({ total_restaurants: 0, total_ratings: 0, total_users: 0 });

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState(INITIAL_FORM_STATE);
  const [formErrors, setFormErrors] = useState({});
  const [modalSubmitting, setModalSubmitting] = useState(false);

  // Delete confirmation state
  const [deletingId, setDeletingId] = useState(null);

  const isAdmin = user && (user.is_admin || user.role === 'admin');

  // Load restaurants and live stats
  const fetchAll = async () => {
    try {
      setLoading(true);
      setError('');
      const [dataResult, statsResult] = await Promise.allSettled([
        getRestaurants({ limit: 200 }),
        api.get('/stats').then((r) => r.data),
      ]);
      if (dataResult.status === 'fulfilled') {
        const items = Array.isArray(dataResult.value)
          ? dataResult.value
          : dataResult.value?.restaurants || dataResult.value?.items || [];
        setRestaurants(items);
      }
      if (statsResult.status === 'fulfilled') {
        setStats(statsResult.value);
      }
    } catch (err) {
      console.error('Failed to load admin data:', err);
      setError('Failed to fetch restaurants. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      fetchAll();
    }
  }, [isAdmin]);

  // Access Denied Screen
  if (!isAdmin) {
    return (
      <div className="page-container" style={{ maxWidth: '600px', textAlign: 'center', paddingTop: '80px' }}>
        <div className="glass-card" style={{ padding: '48px 24px', border: '1px solid rgba(239, 68, 68, 0.4)' }}>
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 18px auto',
              color: '#f87171',
            }}
          >
            <ShieldAlert size={34} />
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '8px' }}>
            Access Denied
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '24px' }}>
            The Admin Panel requires administrator privileges. Please log in with an administrator account to continue.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
            <Link to="/discover" className="btn btn-secondary">
              Go to Discover
            </Link>
            <Link to="/admin-login" className="btn btn-primary">
              Log In as Admin
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Open modal for new restaurant
  const handleOpenAddModal = () => {
    setEditingId(null);
    setFormData(INITIAL_FORM_STATE);
    setFormErrors({});
    setIsModalOpen(true);
  };

  // Open modal to edit existing restaurant
  const handleOpenEditModal = (r) => {
    setEditingId(r.id);
    setFormData({
      name: r.name || '',
      cuisine: Array.isArray(r.cuisine) ? r.cuisine.join(', ') : r.cuisine || '',
      price_range: r.price_range || 'Moderate',
      avg_rating: Number(r.avg_rating || r.rating || 4.2),
      area: r.location?.area || r.area || '',
      lat: r.location?.lat || r.lat || 12.9716,
      lng: r.location?.lng || r.lng || 77.5946,
      ambience: r.ambience || '',
      tags: Array.isArray(r.tags) ? r.tags.join(', ') : r.tags || '',
      description: r.description || '',
      image_url: r.image_url || '',
    });
    setFormErrors({});
    setIsModalOpen(true);
  };

  const validateForm = () => {
    const errors = {};
    if (!formData.name.trim()) errors.name = 'Restaurant name is required';
    if (!formData.cuisine.trim()) errors.cuisine = 'At least one cuisine is required';
    if (!formData.area.trim()) errors.area = 'Neighborhood / area is required';
    return errors;
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    try {
      setModalSubmitting(true);
      const payload = {
        name: formData.name.trim(),
        cuisine: formData.cuisine.split(',').map((c) => c.trim()).filter(Boolean),
        price_range: formData.price_range,
        avg_rating: parseFloat(formData.avg_rating),
        location: {
          area: formData.area.trim(),
          lat: parseFloat(formData.lat),
          lng: parseFloat(formData.lng),
        },
        ambience: formData.ambience.trim() || 'Casual',
        tags: formData.tags.split(',').map((t) => t.trim()).filter(Boolean),
        description: formData.description.trim(),
        image_url: formData.image_url.trim() || null,
      };

      if (editingId) {
        await updateRestaurant(editingId, payload);
      } else {
        await createRestaurant(payload);
      }

      setIsModalOpen(false);
      fetchAll();
    } catch (err) {
      console.error('Save restaurant error:', err);
      alert(
        err?.response?.data?.detail ||
          err?.response?.data?.message ||
          'Failed to save restaurant. Please check the fields and try again.'
      );
    } finally {
      setModalSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this restaurant? This action cannot be undone.')) {
      try {
        setDeletingId(id);
        await deleteRestaurant(id);
        setRestaurants((prev) => prev.filter((r) => r.id !== id));
      } catch (err) {
        console.error('Delete error:', err);
        alert('Failed to delete restaurant.');
      } finally {
        setDeletingId(null);
      }
    }
  };

  // Filter restaurants by search query
  const filteredRestaurants = restaurants.filter((r) => {
    const q = searchQuery.toLowerCase();
    const nameMatch = r.name?.toLowerCase().includes(q);
    const cuisineMatch = (Array.isArray(r.cuisine) ? r.cuisine.join(' ') : r.cuisine || '')
      .toLowerCase()
      .includes(q);
    const areaMatch = r.area?.toLowerCase().includes(q);
    return nameMatch || cuisineMatch || areaMatch;
  });

  return (
    <div className="page-container">
      {/* Admin Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <span className="badge badge-gold" style={{ marginBottom: '6px' }}>
            System Administrator
          </span>
          <h1 style={{ fontSize: '1.8rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Restaurant Management Console
          </h1>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
            Curate restaurants, manage feature vectors, and monitor hybrid recommendation data.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            type="button"
            onClick={fetchAll}
            className="btn btn-secondary btn-sm"
            style={{ gap: '6px' }}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <button
            type="button"
            onClick={handleOpenAddModal}
            className="btn btn-primary"
            style={{ gap: '8px' }}
          >
            <Plus size={16} /> Add Restaurant
          </button>
        </div>
      </div>

      {/* Summary Stats Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '18px',
          marginBottom: '32px',
        }}
      >
        <div className="glass-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
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
            <Building size={22} />
          </div>
          <div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Total Restaurants
            </span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: '800' }}>
              {stats.total_restaurants}
            </h3>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
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
            <Star size={22} />
          </div>
          <div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Ratings Recorded
            </span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: '800' }}>
              {stats.total_ratings.toLocaleString()}
            </h3>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
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
            <Users size={22} />
          </div>
          <div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Registered Users
            </span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: '800' }}>
              {stats.total_users}
            </h3>
          </div>
        </div>
      </div>

      {/* Search and Table Filter */}
      <div className="glass-card" style={{ padding: '16px 20px', marginBottom: '20px' }}>
        <div style={{ position: 'relative', maxWidth: '420px' }}>
          <input
            type="text"
            className="form-input"
            style={{ paddingLeft: '38px' }}
            placeholder="Search by restaurant name, cuisine, or neighborhood..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <Search
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

      {/* Restaurants Table */}
      <div className="glass-card table-container">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Restaurant</th>
              <th>Cuisine</th>
              <th>Price</th>
              <th>Rating</th>
              <th>Area</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '36px' }}>
                  <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 8px auto', color: 'var(--accent-teal)' }} />
                  <p style={{ color: 'var(--text-secondary)' }}>Loading catalog...</p>
                </td>
              </tr>
            ) : filteredRestaurants.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-secondary)' }}>
                  No restaurants found matching "{searchQuery}"
                </td>
              </tr>
            ) : (
              filteredRestaurants.map((r) => {
                const cuisineList = Array.isArray(r.cuisine)
                  ? r.cuisine.join(', ')
                  : r.cuisine || '-';
                const priceTier = (() => {
                  const p = String(r.price_range || '');
                  const map = { budget: '₹', moderate: '₹₹', premium: '₹₹₹', 'fine dining': '₹₹₹₹' };
                  if (map[p.toLowerCase()]) return map[p.toLowerCase()];
                  if (/^\d+$/.test(p)) return '₹'.repeat(Math.max(1, Math.min(Number(p), 4)));
                  return p || '₹₹';
                })();

                return (
                  <tr key={r.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <img
                          src={r.image_url || 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=100&q=80'}
                          alt={r.name}
                          style={{ width: '42px', height: '42px', borderRadius: '6px', objectFit: 'cover' }}
                          onError={(e) => {
                            e.currentTarget.src = 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=100&q=80';
                          }}
                        />
                        <span style={{ fontWeight: '600' }}>{r.name}</span>
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {cuisineList}
                      </span>
                    </td>
                    <td>
                      <span style={{ color: 'var(--accent-gold)', fontWeight: '700' }}>
                        {priceTier}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent-gold)' }}>
                        <Star size={14} fill="var(--accent-gold)" />
                        <span>{Number(r.avg_rating || r.rating || 4.2).toFixed(1)}</span>
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.85rem' }}>{r.location?.area || r.area || '-'}</span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '6px' }}>
                        <button
                          type="button"
                          onClick={() => handleOpenEditModal(r)}
                          className="btn btn-ghost btn-sm"
                          style={{ padding: '6px 8px' }}
                          title="Edit restaurant"
                        >
                          <Edit2 size={15} style={{ color: 'var(--accent-teal)' }} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(r.id)}
                          className="btn btn-ghost btn-sm"
                          style={{ padding: '6px 8px' }}
                          disabled={deletingId === r.id}
                          title="Delete restaurant"
                        >
                          <Trash2 size={15} style={{ color: '#f87171' }} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Add / Edit Restaurant Modal */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div
            className="modal-content"
            style={{ maxWidth: '640px' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '22px' }}>
              <div>
                <h3 style={{ fontSize: '1.35rem', fontWeight: '800' }}>
                  {editingId ? 'Edit Restaurant' : 'Add New Restaurant'}
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Enter restaurant metadata used for content-based similarity calculation.
                </p>
              </div>
              <button
                type="button"
                className="btn btn-ghost btn-icon"
                onClick={() => setIsModalOpen(false)}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleFormSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                {/* Name */}
                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label" htmlFor="m-name">
                    Restaurant Name *
                  </label>
                  <input
                    id="m-name"
                    type="text"
                    className="form-input"
                    placeholder="e.g. The Olive Grove"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                  {formErrors.name && <span className="form-error">{formErrors.name}</span>}
                </div>

                {/* Cuisine */}
                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label" htmlFor="m-cuisine">
                    Cuisines (comma-separated) *
                  </label>
                  <input
                    id="m-cuisine"
                    type="text"
                    className="form-input"
                    placeholder="e.g. Italian, Continental, Cafe"
                    value={formData.cuisine}
                    onChange={(e) => setFormData({ ...formData, cuisine: e.target.value })}
                  />
                  {formErrors.cuisine && <span className="form-error">{formErrors.cuisine}</span>}
                </div>

                {/* Price Range */}
                <div className="form-group">
                  <label className="form-label" htmlFor="m-price">
                    Price Range Tier
                  </label>
                  <select
                    id="m-price"
                    className="form-select"
                    value={formData.price_range}
                    onChange={(e) => setFormData({ ...formData, price_range: e.target.value })}
                  >
                    <option value="Budget">₹ — Budget (under ₹500)</option>
                    <option value="Moderate">₹₹ — Moderate (₹500 - ₹1200)</option>
                    <option value="Premium">₹₹₹ — Premium (₹1200 - ₹2500)</option>
                    <option value="Fine Dining">₹₹₹₹ — Fine Dining (₹2500+)</option>
                  </select>
                </div>

                {/* Average Rating */}
                <div className="form-group">
                  <label className="form-label" htmlFor="m-rating">
                    Initial Rating (1.0 - 5.0)
                  </label>
                  <input
                    id="m-rating"
                    type="number"
                    step="0.1"
                    min="1"
                    max="5"
                    className="form-input"
                    value={formData.avg_rating}
                    onChange={(e) => setFormData({ ...formData, avg_rating: e.target.value })}
                  />
                </div>

                {/* Area / Neighborhood */}
                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label" htmlFor="m-area">
                    Area / Neighborhood *
                  </label>
                  <input
                    id="m-area"
                    type="text"
                    className="form-input"
                    placeholder="e.g. Indiranagar, Bangalore"
                    value={formData.area}
                    onChange={(e) => setFormData({ ...formData, area: e.target.value })}
                  />
                  {formErrors.area && <span className="form-error">{formErrors.area}</span>}
                </div>

                {/* Coordinates: Lat & Lng */}
                <div className="form-group">
                  <label className="form-label" htmlFor="m-lat">Latitude</label>
                  <input
                    id="m-lat"
                    type="number"
                    step="0.0001"
                    className="form-input"
                    value={formData.lat}
                    onChange={(e) => setFormData({ ...formData, lat: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="m-lng">Longitude</label>
                  <input
                    id="m-lng"
                    type="number"
                    step="0.0001"
                    className="form-input"
                    value={formData.lng}
                    onChange={(e) => setFormData({ ...formData, lng: e.target.value })}
                  />
                </div>

                {/* Ambience */}
                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label" htmlFor="m-ambience">
                    Ambience & Atmosphere
                  </label>
                  <input
                    id="m-ambience"
                    type="text"
                    className="form-input"
                    placeholder="e.g. Dimly lit romantic rooftop, lively music"
                    value={formData.ambience}
                    onChange={(e) => setFormData({ ...formData, ambience: e.target.value })}
                  />
                </div>

                {/* Tags */}
                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label" htmlFor="m-tags">
                    Tags & Amenities (comma-separated)
                  </label>
                  <input
                    id="m-tags"
                    type="text"
                    className="form-input"
                    placeholder="e.g. Outdoor Seating, Valet Parking, Pet Friendly, Craft Beer"
                    value={formData.tags}
                    onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  />
                </div>

                {/* Image URL */}
                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label" htmlFor="m-img">
                    Image URL
                  </label>
                  <input
                    id="m-img"
                    type="url"
                    className="form-input"
                    placeholder="https://images.unsplash.com/..."
                    value={formData.image_url}
                    onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                  />
                </div>

                {/* Description */}
                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label" htmlFor="m-desc">
                    Description
                  </label>
                  <textarea
                    id="m-desc"
                    rows={3}
                    className="form-textarea"
                    placeholder="Brief description of culinary highlights and signature dishes..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
              </div>

              {/* Modal Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsModalOpen(false)}
                  disabled={modalSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={modalSubmitting}
                  style={{ gap: '6px' }}
                >
                  <Check size={16} />
                  {modalSubmitting ? 'Saving...' : editingId ? 'Update Restaurant' : 'Create Restaurant'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
