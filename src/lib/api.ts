import axios from 'axios';

// In development: Next.js runs on 3000, FastAPI on 8000.
// In production (Vercel): both are served from the same origin — /api routes
// are handled by the Python serverless function via vercel.json routes.
const baseURL = '/api';

export const apiClient = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000, // 30s timeout for serverless cold starts
});

// ── Request interceptor: attach JWT token from localStorage ──────────────
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: redirect to login on 401 ───────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && typeof window !== 'undefined') {
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/') {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const fetcher = (url: string) => apiClient.get(url).then(res => res.data);
