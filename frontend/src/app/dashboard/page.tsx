'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { DashboardData } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import { formatDate } from '@/lib/utils';

export default function DashboardPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const data = await apiClient.get<DashboardData>(API_ENDPOINTS.DASHBOARD.TODAY);
        setDashboardData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (isLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto mt-8 p-4 border border-red-300 rounded-lg text-red-700">
        <h3 className="font-semibold">Error loading dashboard</h3>
        <p className="text-sm mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          {dashboardData?.date ? formatDate(dashboardData.date) : 'Today'}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 border border-gray-200 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Articles</h3>
          <p className="text-3xl font-semibold text-blue-600">
            {dashboardData?.total_articles || 0}
          </p>
          <p className="text-sm text-gray-600 mt-1">Articles processed today</p>
        </div>
        
        <div className="p-6 border border-gray-200 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-2">News Clusters</h3>
          <p className="text-3xl font-semibold text-green-600">
            {dashboardData?.clusters_count || 0}
          </p>
          <p className="text-sm text-gray-600 mt-1">Topics identified</p>
        </div>
        
        <div className="p-6 border border-gray-200 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Top Topics</h3>
          <p className="text-3xl font-semibold text-purple-600">
            {dashboardData?.top_topics?.length || 0}
          </p>
          <p className="text-sm text-gray-600 mt-1">Active categories</p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Summary */}
        <div className="p-6 border border-gray-200 rounded-lg shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Summary</h2>
          {dashboardData?.summary ? (
            <p className="text-gray-700 leading-relaxed">
              {dashboardData.summary}
            </p>
          ) : (
            <p className="text-gray-500 italic">
              No summary available for today.
            </p>
          )}
        </div>

        {/* Top Topics */}
        <div className="p-6 border border-gray-200 rounded-lg shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Topics</h2>
          <div className="space-y-2">
            {dashboardData?.top_topics && dashboardData.top_topics.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {dashboardData.top_topics.map((topic, index) => (
                  <span key={index} className="px-3 py-1 border border-gray-300 rounded-full text-sm text-gray-700">
                    {topic}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 italic">
                No topics identified today.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Trending Keywords */}
      {dashboardData?.trending_keywords && dashboardData.trending_keywords.length > 0 && (
        <div className="p-6 border border-gray-200 rounded-lg shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Trending Keywords</h2>
          <div className="flex flex-wrap gap-2">
            {dashboardData.trending_keywords.map((keyword, index) => (
              <span key={index} className="px-2 py-1 border border-gray-400 rounded text-sm text-gray-800">
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="p-6 border border-gray-200 rounded-lg shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <button className="px-4 py-2 border border-blue-600 text-blue-600 rounded hover:bg-blue-50 transition-colors">
            View All Topics
          </button>
          <button className="px-4 py-2 border border-green-600 text-green-600 rounded hover:bg-green-50 transition-colors">
            Manage RSS Feeds
          </button>
          <button className="px-4 py-2 border border-purple-600 text-purple-600 rounded hover:bg-purple-50 transition-colors">
            Update Settings
          </button>
        </div>
      </div>
    </div>
  );
}