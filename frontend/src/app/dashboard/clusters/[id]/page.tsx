'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { Article } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
// import ListView from '@/components/ListView';
// import ListItem from '@/components/ListItem';
import { formatDate, stripHtmlTags } from '@/lib/utils';
import { ChevronLeft, FileStack, Clock, Calendar, User, Tag, Users } from 'lucide-react';

interface ClusterDetail {
  cluster: {
    id: number;
    title: string;
    summary: string;
    article_count: number;
    created_at: string;
    updated_at: string;
    articles: Article[];
  };
}

export default function ClusterDetailPage() {
  const params = useParams();
  const router = useRouter();
  const clusterId = parseInt(params.id as string);
  
  const [clusterDetail, setClusterDetail] = useState<ClusterDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNaN(clusterId)) {
      setError('Invalid cluster ID');
      setIsLoading(false);
      return;
    }
    
    fetchClusterDetail();
  }, [clusterId]);

  const fetchClusterDetail = async () => {
    try {
      const data = await apiClient.get<ClusterDetail>(API_ENDPOINTS.CLUSTERS.DETAIL(clusterId));
      setClusterDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cluster details');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  if (error || !clusterDetail) {
    return (
      <div className="max-w-4xl mx-auto mt-8 p-4 border border-red-300 rounded-lg text-red-700">
        <h3 className="font-semibold">Error loading cluster</h3>
        <p className="text-sm mt-1">{error || 'Cluster not found'}</p>
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
                fetchClusterDetail();
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

  const { cluster } = clusterDetail;

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-6 mb-6">
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
              <h1 className="text-3xl font-semibold text-gray-900 mb-2">{cluster.title}</h1>
              <div className="flex items-center gap-6 text-sm text-gray-600">
                <span className="flex items-center gap-1">
                  <FileStack className="w-4 h-4" />
                  {cluster.article_count} articles
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  Updated {formatDate(cluster.updated_at)}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  Created {formatDate(cluster.created_at)}
                </span>
              </div>
            </div>
          </div>
          
        </div>
      </div>

      {/* Cluster Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
        <h2 className="text-lg font-semibold text-blue-900 mb-3">Cluster Summary</h2>
        <p className="text-blue-800 leading-relaxed">
          {cluster.summary}
        </p>
      </div>

      {/* Articles List */}
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">
            Articles ({cluster.articles.length})
          </h2>
          <div className="text-sm text-gray-600">
            Sorted by publication date
          </div>
        </div>

        {cluster.articles.length > 0 ? (
          <div className="space-y-4">
            {cluster.articles.map((article) => (
              <div key={article.id} className="border border-gray-200 rounded-lg bg-white hover:shadow-md transition-shadow">
                <div className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <Link
                        href={`/dashboard/article/${article.id}`}
                        className="block group"
                      >
                        <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors mb-2">
                          {article.title}
                        </h3>
                      </Link>
                      
                      <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
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
                          <span className="flex items-center gap-1">
                            <Tag className="w-4 h-4" />
                            {article.category}
                          </span>
                        )}
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          article.processing_status === 'completed' ? 'bg-green-100 text-green-800' :
                          article.processing_status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                          article.processing_status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {article.processing_status}
                        </span>
                      </div>

                      {/* Article Content Preview */}
                      {article.content && (
                        <div className="text-gray-700 text-sm leading-relaxed">
                          <p className="line-clamp-3">
                            {stripHtmlTags(article.content).length > 300 
                              ? `${stripHtmlTags(article.content).substring(0, 300)}...`
                              : stripHtmlTags(article.content)
                            }
                          </p>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex flex-col gap-2 ml-4">
                      <Link
                        href={`/dashboard/article/${article.id}`}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                      >
                        Read Article
                      </Link>
                      {article.url && (
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors text-sm text-center"
                        >
                          Original Source
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              <div className="mb-4">
                <Users className="mx-auto h-12 w-12 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Articles Found
              </h3>
              <p className="text-gray-600 mb-6">
                This cluster doesn&apos;t contain any articles yet. This might happen if the articles are still being processed or if they were removed.
              </p>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}