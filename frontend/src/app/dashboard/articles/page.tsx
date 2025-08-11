'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS, PAGINATION } from '@/lib/constants';
import { Article, ApiResponse } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import { formatDate, stripHtmlTags } from '@/lib/utils';
import { FileText, User, Clock, TrendingUp } from 'lucide-react';


export default function ArticlesPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [articles, setArticles] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    // Redirect admin users to system settings
    if (user?.is_admin) {
      router.replace('/dashboard/settings');
      return;
    }
    
    fetchArticles();
  }, [currentPage, user, router]);

  const fetchArticles = async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: PAGINATION.DEFAULT_LIMIT.toString(),
        status: 'completed', // Only fetch completed articles
      });

      const response = await apiClient.get<ApiResponse<Article[]>>(`${API_ENDPOINTS.ARTICLES.LIST}?${params}`);
      
      if (Array.isArray(response)) {
        // Handle direct array response (no pagination wrapper)
        setArticles(response);
        setTotalCount(response.length);
        setTotalPages(1);
      } else if (response.data) {
        // Handle paginated response
        setArticles(response.data);
        setTotalCount(response.pagination?.total || response.data.length);
        setTotalPages(Math.ceil((response.pagination?.total || response.data.length) / PAGINATION.DEFAULT_LIMIT));
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load articles');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusStyles = {
      'completed': 'bg-green-100 text-green-800',
      'processing': 'bg-yellow-100 text-yellow-800',
      'failed': 'bg-red-100 text-red-800',
      'pending': 'bg-gray-100 text-gray-600'
    };
    return statusStyles[status as keyof typeof statusStyles] || statusStyles.pending;
  };

  const calculateReadingTime = (content: string): number => {
    if (!content) return 0;
    const wordsPerMinute = 200;
    const wordCount = content.trim().split(/\s+/).length;
    return Math.ceil(wordCount / wordsPerMinute);
  };

  if (isLoading && currentPage === 1) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-6 mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-semibold text-gray-900">Articles</h1>
            <p className="text-gray-600 mt-1">
              Browse completed news articles ({totalCount} total)
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard/topics"
              className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Topics
            </Link>
            <Link
              href="/dashboard"
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </div>


      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 border border-red-300 rounded-lg text-red-700 bg-red-50">
          <p>{error}</p>
          <button 
            onClick={() => {
              setError(null);
              fetchArticles();
            }}
            className="mt-2 text-sm underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Articles List */}
      {isLoading && currentPage > 1 && (
        <div className="text-center py-4">
          <LoadingSpinner size="md" />
        </div>
      )}

      {articles.length === 0 && !isLoading ? (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2 mt-4">No Articles Found</h3>
            <p className="text-gray-600 mb-6">
              No completed articles have been processed yet.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {articles.map((article) => (
            <div key={article.id} className="border border-gray-200 rounded-lg hover:shadow-sm transition-shadow">
              <div className="p-6">
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    {/* Title */}
                    <Link
                      href={`/dashboard/article/${article.id}`}
                      className="block group"
                    >
                      <h3 className="text-lg font-medium text-gray-900 group-hover:text-blue-600 transition-colors mb-2 line-clamp-2">
                        {article.title}
                      </h3>
                    </Link>

                    {/* Metadata */}
                    <div className="flex items-center gap-6 text-sm text-gray-600 mb-3">
                      {article.author && (
                        <span className="flex items-center gap-1">
                          <User className="w-4 h-4" />
                          {article.author}
                        </span>
                      )}
                      {article.published_at && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {formatDate(article.published_at)}
                        </span>
                      )}
                      {article.category && (
                        <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                          {article.category}
                        </span>
                      )}
                      {article.content && (
                        <span className="flex items-center gap-1">
                          <TrendingUp className="w-4 h-4" />
                          {calculateReadingTime(article.content)} min read
                        </span>
                      )}
                    </div>

                    {/* Content Preview */}
                    {article.content && (
                      <p className="text-gray-700 text-sm line-clamp-2 mb-3">
                        {stripHtmlTags(article.content).substring(0, 200)}...
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col items-end gap-3 ml-6">
                    <div className="flex gap-2">
                      {article.url && (
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors"
                        >
                          Source
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8 flex justify-between items-center">
          <div className="text-sm text-gray-700">
            Showing page {currentPage} of {totalPages} ({totalCount} total articles)
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 text-sm border border-gray-300 rounded text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 text-sm border border-gray-300 rounded text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
