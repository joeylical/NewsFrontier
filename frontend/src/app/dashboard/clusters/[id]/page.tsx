'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { Article } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import ListView from '@/components/ListView';
import ListItem from '@/components/ListItem';
import { formatDate } from '@/lib/utils';

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
              <h1 className="text-3xl font-semibold text-gray-900 mb-2">{cluster.title}</h1>
              <div className="flex items-center gap-6 text-sm text-gray-600">
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
                  Updated {formatDate(cluster.updated_at)}
                </span>
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                  </svg>
                  Created {formatDate(cluster.created_at)}
                </span>
              </div>
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
              href="/dashboard"
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Dashboard
            </Link>
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
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                            </svg>
                            {article.author}
                          </span>
                        )}
                        {article.published_at && (
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                            </svg>
                            {formatDate(article.published_at)}
                          </span>
                        )}
                        {article.category && (
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                            </svg>
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
                            {article.content.length > 300 
                              ? `${article.content.substring(0, 300)}...`
                              : article.content
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
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 48 48">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M34 40h10v-4a6 6 0 00-10.712-3.714M34 40H14m20 0v-4a9.971 9.971 0 00-.712-3.714M14 40H4v-4a6 6 0 0110.713-3.714M14 40v-4c0-1.313.253-2.566.713-3.714m0 0A9.971 9.971 0 0118 32a9.971 9.971 0 013.287.714M14 36.286c0-2.442.45-4.778 1.287-6.857C16.85 27.002 19.294 26 22 26s5.15 1.002 6.713 3.429c.837 2.08 1.287 4.415 1.287 6.857" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Articles Found
              </h3>
              <p className="text-gray-600 mb-6">
                This cluster doesn't contain any articles yet. This might happen if the articles are still being processed or if they were removed.
              </p>
              <Link
                href="/dashboard/topics"
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Back to Topics
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Cluster Statistics */}
      {cluster.articles.length > 0 && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Articles</p>
                <p className="text-lg font-semibold text-gray-900">{cluster.articles.length}</p>
              </div>
            </div>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Unique Authors</p>
                <p className="text-lg font-semibold text-gray-900">
                  {new Set(cluster.articles.filter(a => a.author).map(a => a.author)).size}
                </p>
              </div>
            </div>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Categories</p>
                <p className="text-lg font-semibold text-gray-900">
                  {new Set(cluster.articles.filter(a => a.category).map(a => a.category)).size}
                </p>
              </div>
            </div>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Processed</p>
                <p className="text-lg font-semibold text-gray-900">
                  {cluster.articles.filter(a => a.processing_status === 'completed').length}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}