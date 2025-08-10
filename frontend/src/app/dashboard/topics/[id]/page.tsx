'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { Topic, Cluster } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import { formatDate } from '@/lib/utils';

interface TopicDetail {
  topic: Topic;
  clusters: Cluster[];
}

export default function TopicDetailPage() {
  const params = useParams();
  const router = useRouter();
  const topicId = parseInt(params.id as string);
  
  const [topicDetail, setTopicDetail] = useState<TopicDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNaN(topicId)) {
      setError('Invalid topic ID');
      setIsLoading(false);
      return;
    }
    
    fetchTopicDetail();
  }, [topicId]);

  const fetchTopicDetail = async () => {
    try {
      const data = await apiClient.get<TopicDetail>(API_ENDPOINTS.TOPICS.DETAIL(topicId));
      setTopicDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load topic details');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  if (error || !topicDetail) {
    return (
      <div className="max-w-4xl mx-auto mt-8 p-4 border border-red-300 rounded-lg text-red-700">
        <h3 className="font-semibold">Error loading topic</h3>
        <p className="text-sm mt-1">{error || 'Topic not found'}</p>
        <div className="mt-4 flex gap-3">
          <button 
            onClick={() => router.back()}
            className="text-sm underline"
          >
            Go back
          </button>
          {error && (
            <button 
              onClick={() => {
                setError(null);
                fetchTopicDetail();
              }}
              className="text-sm underline"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    );
  }

  const { topic, clusters } = topicDetail;

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Go back"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-semibold text-gray-900">{topic.name}</h1>
                <span className={`px-3 py-1 text-sm rounded-full ${
                  topic.active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {topic.active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <p className="text-gray-600 mt-1">
                {clusters.length} news clusters found
              </p>
            </div>
          </div>
          
          <div className="flex gap-3">
            <Link
              href="/dashboard/topics"
              className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Back to Topics
            </Link>
            <Link
              href="/dashboard/settings"
              className="px-4 py-2 border border-blue-300 text-blue-600 rounded hover:bg-blue-50 transition-colors"
            >
              Edit Topic
            </Link>
          </div>
        </div>

        {/* Keywords */}
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Keywords:</h3>
          <div className="flex flex-wrap gap-2">
            {topic.keywords.map((keyword, index) => (
              <span key={index} className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full">
                {keyword}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Clusters Grid */}
      {clusters.length > 0 ? (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">
              News Clusters ({clusters.length})
            </h2>
            <div className="text-sm text-gray-600">
              Sorted by most recent
            </div>
          </div>

          <div className="grid gap-6">
            {clusters.map((cluster) => (
              <div key={cluster.id} className="border border-gray-200 rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow">
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {cluster.title}
                      </h3>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                          </svg>
                          {cluster.article_count} articles
                        </span>
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                          </svg>
                          {formatDate(cluster.updated_at)}
                        </span>
                      </div>
                    </div>
                    
                    <Link
                      href={`/dashboard/clusters/${cluster.id}`}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex-shrink-0"
                    >
                      View Cluster
                    </Link>
                  </div>
                  
                  {/* Cluster Summary */}
                  <div className="border-t border-gray-100 pt-4">
                    <p className="text-gray-700 leading-relaxed">
                      {cluster.summary}
                    </p>
                  </div>

                  {/* Sample Articles Preview (if available) */}
                  {cluster.articles && cluster.articles.length > 0 && (
                    <div className="mt-4 border-t border-gray-100 pt-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        Sample Articles:
                      </h4>
                      <div className="space-y-2">
                        {cluster.articles.slice(0, 3).map((article) => (
                          <div key={article.id} className="text-sm">
                            <Link
                              href={`/dashboard/article/${article.id}`}
                              className="text-blue-600 hover:text-blue-800 hover:underline"
                            >
                              {article.title}
                            </Link>
                            {article.published_at && (
                              <span className="text-gray-500 ml-2">
                                · {formatDate(article.published_at)}
                              </span>
                            )}
                          </div>
                        ))}
                        {cluster.article_count > 3 && (
                          <div className="text-sm text-gray-500">
                            ... and {cluster.article_count - 3} more articles
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <div className="mb-4">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 48 48">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M34 40h10v-4a6 6 0 00-10.712-3.714M34 40H14m20 0v-4a9.971 9.971 0 00-.712-3.714M14 40H4v-4a6 6 0 0110.713-3.714M14 40v-4c0-1.313.253-2.566.713-3.714m0 0A9.971 9.971 0 0118 32a9.971 9.971 0 013.287.714M14 36.286c0-2.442.45-4.778 1.287-6.857C16.85 27.002 19.294 26 22 26s5.15 1.002 6.713 3.429c.837 2.08 1.287 4.415 1.287 6.857" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No Clusters Found
            </h3>
            <p className="text-gray-600 mb-6">
              {topic.active 
                ? "No news clusters have been generated for this topic yet. This could mean there are no recent matching articles, or the clustering process is still running."
                : "This topic is currently inactive. Activate it to start collecting and clustering news articles."
              }
            </p>
            <div className="flex justify-center gap-3">
              {!topic.active && (
                <Link
                  href="/dashboard/settings"
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Activate Topic
                </Link>
              )}
              <Link
                href="/dashboard/topics"
                className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Back to Topics
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Topic Statistics */}
      {clusters.length > 0 && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Clusters</p>
                <p className="text-lg font-semibold text-gray-900">{clusters.length}</p>
              </div>
            </div>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Articles</p>
                <p className="text-lg font-semibold text-gray-900">
                  {clusters.reduce((sum, cluster) => sum + cluster.article_count, 0)}
                </p>
              </div>
            </div>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 3a1 1 0 00-1.447-.894L8.763 6H5a3 3 0 000 6h.28l1.771 5.316A1 1 0 008 18h1a1 1 0 001-1v-4.382l6.553 3.276A1 1 0 0018 15V3z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Keywords</p>
                <p className="text-lg font-semibold text-gray-900">{topic.keywords.length}</p>
              </div>
            </div>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Avg per Cluster</p>
                <p className="text-lg font-semibold text-gray-900">
                  {Math.round(clusters.reduce((sum, cluster) => sum + cluster.article_count, 0) / clusters.length)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}