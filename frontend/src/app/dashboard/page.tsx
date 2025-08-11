'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { DashboardData } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import { formatDate } from '@/lib/utils';
import { SummaryContent } from '@/components/SafeHtmlContent';
import DatePickerCalendar from '@/components/DatePickerCalendar';
import { Calendar, ExternalLink } from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [showCalendar, setShowCalendar] = useState(false);
  const [coverImageUrl, setCoverImageUrl] = useState<string | null>(null);
  const [coverImageLoading, setCoverImageLoading] = useState(false);

  const fetchCoverImage = async (date: string) => {
    setCoverImageLoading(true);
    try {
      const isToday = date === new Date().toISOString().split('T')[0];
      const endpoint = isToday 
        ? API_ENDPOINTS.DASHBOARD.COVER_IMAGE 
        : `${API_ENDPOINTS.DASHBOARD.COVER_IMAGE}?date_param=${date}`;
      const response = await apiClient.get<{ cover_url: string; date: string; s3_key: string }>(endpoint);
      setCoverImageUrl(response.cover_url);
    } catch {
      // Cover image is optional, so don't show error if it's not available
      setCoverImageUrl(null);
    } finally {
      setCoverImageLoading(false);
    }
  };

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Use the updated API that supports date parameters
        const isToday = selectedDate === new Date().toISOString().split('T')[0];
        const endpoint = isToday 
          ? API_ENDPOINTS.DASHBOARD.TODAY 
          : `${API_ENDPOINTS.DASHBOARD.TODAY}?date_param=${selectedDate}`;
        const data = await apiClient.get<DashboardData>(endpoint);
        setDashboardData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
    fetchCoverImage(selectedDate);
  }, [user, router, selectedDate]);

  // const handleDateChange = (direction: 'prev' | 'next') => {
  //   const currentDate = new Date(selectedDate);
  //   const newDate = new Date(currentDate);
  //   newDate.setDate(currentDate.getDate() + (direction === 'next' ? 1 : -1));
  //   setSelectedDate(newDate.toISOString().split('T')[0]);
  //   setIsLoading(true);
  //   setError(null);
  // };

  // const goToToday = () => {
  //   setSelectedDate(new Date().toISOString().split('T')[0]);
  //   setIsLoading(true);
  //   setError(null);
  // };

  const handleDateSelect = (date: string) => {
    setSelectedDate(date);
    setIsLoading(true);
    setError(null);
  };

  // const isToday = selectedDate === new Date().toISOString().split('T')[0];

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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-gray-900">Today&apos;s News Summary</h1>
            <p className="text-gray-600 mt-1">
              {dashboardData?.date ? formatDate(dashboardData.date) : formatDate(selectedDate)}
            </p>
          </div>
          <div className="flex items-center">
            <button
              onClick={() => setShowCalendar(true)}
              className="btn btn-primary btn-square btn-sm"
              title="Select date"
            >
              <Calendar className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Cover Image */}
      {(coverImageUrl || coverImageLoading) && (
        <div>
          {coverImageLoading ? (
            <div className="w-full h-64 bg-gray-200 rounded-lg animate-pulse flex items-center justify-center">
              <span className="text-gray-500">Loading cover image...</span>
            </div>
          ) : coverImageUrl ? (
            <div className="w-full">
              <Image 
                src={coverImageUrl} 
                alt="Daily news summary cover" 
                className="w-full h-auto rounded-lg shadow-lg object-cover max-h-96"
                width={800}
                height={400}
                onError={() => setCoverImageUrl(null)}
              />
            </div>
          ) : null}
        </div>
      )}

      {/* Daily Summary - Direct Display */}
      <div className="space-y-6">
        {dashboardData?.summary ? (
          <div className="space-y-6">
            <div className="text-lg text-gray-700 leading-relaxed">
              <SummaryContent content={dashboardData.summary} />
            </div>
            
            {/* Related Clusters */}
            {dashboardData.clusters && dashboardData.clusters.length > 0 && (
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Related News Clusters</h3>
                <div className="grid gap-4">
                  {dashboardData.clusters.slice(0, 5).map((cluster) => (
                    <div key={cluster.id} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <a 
                          href={`/dashboard/clusters/${cluster.id}`}
                          className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                        >
                          {cluster.title}
                        </a>
                        <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded">
                          {cluster.article_count} articles
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 line-clamp-2">
                        <SummaryContent content={cluster.summary} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Articles */}
            {dashboardData.top_articles && dashboardData.top_articles.length > 0 && (
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Key Articles</h3>
                <div className="space-y-3">
                  {dashboardData.top_articles.slice(0, 8).map((article) => (
                    <div key={article.id} className="flex justify-between items-start p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
                      <div className="flex-1">
                        <a 
                          href={article.url || `/dashboard/article/${article.id}`}
                          target={article.url ? '_blank' : '_self'}
                          rel={article.url ? 'noopener noreferrer' : undefined}
                          className="text-blue-700 hover:text-blue-900 font-medium text-sm block"
                        >
                          {article.title}
                        </a>
                        {article.published_at && (
                          <p className="text-xs text-gray-500 mt-1">
                            {formatDate(article.published_at)}
                          </p>
                        )}
                      </div>
                      {article.url && (
                        <ExternalLink className="w-4 h-4 text-gray-400 ml-2 flex-shrink-0" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500 italic text-lg">
            No summary available for this date.
          </p>
        )}
      </div>

      {/* Calendar Popup */}
      {showCalendar && (
        <DatePickerCalendar
          selectedDate={selectedDate}
          onDateSelect={handleDateSelect}
          onClose={() => setShowCalendar(false)}
        />
      )}
    </div>
  );
}