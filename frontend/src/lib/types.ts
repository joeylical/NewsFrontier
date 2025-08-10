export interface User {
  id: number;
  username: string;
  email?: string;
  is_admin: boolean;
  daily_summary_prompt?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  token: string;
  user_id: number;
  expires: string;
  user?: User;
}

export interface Topic {
  id: number;
  name: string;
  keywords: string[];
  active: boolean;
  user_id?: number;
  created_at: string;
  updated_at: string;
}

export interface RSSFeed {
  id: number;
  uuid: string;
  url: string;
  title?: string;
  description?: string;
  last_fetch_at?: string;
  last_fetch_status: string;
  fetch_interval_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface Article {
  id: number;
  title: string;
  content?: string;
  url?: string;
  published_at?: string;
  author?: string;
  category?: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
}

export interface ArticleDerivative {
  id: number;
  summary?: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  summary_generated_at?: string;
  embeddings_generated_at?: string;
  llm_model_version?: string;
  embedding_model_version?: string;
}

export interface Cluster {
  id: number;
  title: string;
  summary: string;
  article_count: number;
  articles?: Article[];
  created_at: string;
  updated_at: string;
}

export interface DashboardData {
  date: string;
  total_articles: number;
  clusters_count: number;
  top_topics: string[];
  summary: string;
  trending_keywords: string[];
}

export interface ApiError {
  message: string;
  status_code?: number;
  details?: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  offset?: number;
}

export interface ApiResponse<T> {
  data: T;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    has_next: boolean;
    has_prev: boolean;
  };
  error?: ApiError;
}