'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { Topic, Cluster } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import { formatDate } from '@/lib/utils';
import { ChevronLeft, FileStack, Clock, Users } from 'lucide-react';

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
        <div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Go back"
            >
              <ChevronLeft className="w-5 h-5 text-gray-600" />
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
                  <div className="mb-4">
                    <Link 
                      href={`/dashboard/clusters/${cluster.id}`}
                      className="text-lg font-semibold text-gray-900 mb-2 hover:text-blue-600 transition-colors block"
                    >
                      {cluster.title}
                    </Link>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <FileStack className="w-4 h-4" />
                        {cluster.article_count} articles
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatDate(cluster.updated_at)}
                      </span>
                    </div>
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
              <Users className="mx-auto h-12 w-12 text-gray-400" />
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
            </div>
          </div>
        </div>
      )}

    </div>
  );
}