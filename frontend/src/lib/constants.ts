export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/login',
    LOGOUT: '/api/logout',
    REGISTER: '/api/register',
    USER_INFO: '/api/user/me',
  },
  DASHBOARD: {
    TODAY: '/api/today',
  },
  TOPICS: {
    LIST: '/api/topics',
    CREATE: '/api/topics',
    DETAIL: (id: number) => `/api/topic/${id}`,
  },
  CLUSTERS: {
    DETAIL: (id: number) => `/api/cluster/${id}`,
  },
  ADMIN: {
    USERS: '/api/admin/users',
    RSS_FEEDS: '/api/admin/rss-feeds',
    SYSTEM: '/api/admin/system',
  },
} as const;

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'newsfrontier_auth_token',
  USER_DATA: 'newsfrontier_user_data',
  THEME: 'newsfrontier_theme',
} as const;

export const PROCESSING_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing', 
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_LIMIT: 20,
  MAX_LIMIT: 100,
} as const;

export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
} as const;