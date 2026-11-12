import axios from 'axios';

// Base API client: uses VITE_API_URL in production, /api proxy in dev
const rawApiUrl = import.meta.env.VITE_API_URL || '';
const normalizedApiUrl = rawApiUrl && !/^https?:\/\//i.test(rawApiUrl)
  ? `https://${rawApiUrl}`
  : rawApiUrl;
const API_BASE = normalizedApiUrl ? `${normalizedApiUrl}/api` : '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request interceptor: attach JWT bearer token if present
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      const currentPath = window.location.pathname;
      if (
        !currentPath.includes('/login') &&
        !currentPath.includes('/register') &&
        currentPath !== '/'
      ) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const login = async (email, password) => {
  const response = await api.post('/auth/login', {
    email,
    password,
    username: email,
  });
  return response.data;
};

export const register = async (name, email, password, preferences = {}) => {
  const response = await api.post('/auth/register', {
    name,
    email,
    password,
    preferences,
  });
  return response.data;
};

export const getMe = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

// Restaurant endpoints
export const getRestaurants = async (params = {}) => {
  const response = await api.get('/restaurants', { params });
  return response.data;
};

export const getRestaurant = async (id) => {
  const response = await api.get(`/restaurants/${id}`);
  return response.data;
};

export const createRestaurant = async (data) => {
  const response = await api.post('/restaurants', data);
  return response.data;
};

export const updateRestaurant = async (id, data) => {
  const response = await api.put(`/restaurants/${id}`, data);
  return response.data;
};

export const deleteRestaurant = async (id) => {
  const response = await api.delete(`/restaurants/${id}`);
  return response.data;
};

// Rating endpoints
export const submitRating = async (restaurantId, score) => {
  const response = await api.post('/ratings', {
    restaurant_id: restaurantId,
    restaurantId,
    score,
    rating: score,
  });
  return response.data;
};

export const getMyRatings = async () => {
  const response = await api.get('/ratings/me');
  return response.data;
};

// Recommendations endpoint
export const getRecommendations = async (params = {}) => {
  const cleanParams = {};
  if (params.top_n !== undefined) cleanParams.top_n = params.top_n;
  if (params.price_range !== undefined) cleanParams.price_range = params.price_range;
  if (params.cuisine !== undefined) cleanParams.cuisine = params.cuisine;
  if (params.ambience !== undefined) cleanParams.ambience = params.ambience;
  if (params.max_distance_km !== undefined) cleanParams.max_distance_km = params.max_distance_km;
  if (params.user_lat !== undefined && params.user_lat !== null) cleanParams.user_lat = params.user_lat;
  if (params.user_lng !== undefined && params.user_lng !== null) cleanParams.user_lng = params.user_lng;
  if (params.alpha !== undefined && params.alpha !== null) cleanParams.alpha = params.alpha;

  const response = await api.get('/recommendations', { params: cleanParams });
  return response.data;
};

// Interaction logging (clicks, views, etc.)
export const logInteraction = async (restaurantId, type = 'view') => {
  try {
    const response = await api.post('/interactions', {
      restaurant_id: restaurantId,
      restaurantId,
      interaction_type: type,
      type,
    });
    return response.data;
  } catch (err) {
    // Silently fail interaction logging so it doesn't disrupt user experience
    console.warn('Failed to log interaction:', err.message);
    return null;
  }
};

// Admin stats endpoint
export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

// Search restaurants
export const searchRestaurants = async (query) => {
  const response = await api.get('/restaurants/search', { params: { q: query } });
  return response.data;
};

// Update user preferences
export const updatePreferences = async (preferences) => {
  const response = await api.put('/auth/preferences', { ...preferences });
  return response.data;
};

// Evaluation / benchmarking endpoint
export const getEvaluation = async (k = 10) => {
  const response = await api.get('/evaluation', { params: { k }, timeout: 60000 });
  return response.data;
};

export default api;
