export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/login',
    LOGOUT: '/api/logout',
    REGISTER: '/api/register',
    USER_INFO: '/api/user/me',
    USER_SETTINGS: '/api/user/settings',
  },
  DASHBOARD: {
    TODAY: '/api/today',
    AVAILABLE_DATES: (year: number, month: number) => `/api/available-dates?year=${year}&month=${month}`,
    COVER_IMAGE: '/api/cover-image',
  },
  TOPICS: {
    LIST: '/api/topics',
    CREATE: '/api/topics',
    DETAIL: (id: number) => `/api/topic/${id}`,
  },
  ARTICLES: {
    LIST: '/api/articles',
    DETAIL: (id: number) => `/api/article/${id}`,
  },
  CLUSTERS: {
    DETAIL: (id: number) => `/api/cluster/${id}`,
  },
  RSS_FEEDS: {
    LIST: '/api/feeds',
    CREATE: '/api/feeds',
    UPDATE: (uuid: string) => `/api/feeds/${uuid}`,
    DELETE: (uuid: string) => `/api/feeds/${uuid}`,
    STATUS: (uuid: string) => `/api/feeds/${uuid}/status`,
    FETCH: (uuid: string) => `/api/feeds/${uuid}/fetch`,
  },
  ADMIN: {
    USERS: '/api/admin/users',
    RSS_FEEDS: '/api/admin/rss-feeds',
    SYSTEM: '/api/admin/system',
    SETTINGS: '/api/admin/system-settings',
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