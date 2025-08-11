'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { Topic, Cluster } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import { Check, Plus } from 'lucide-react';

interface TopicClustersProps {
  topicId: number;
}

function TopicClusters({ topicId }: TopicClustersProps) {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchClusters = async () => {
      try {
        const data = await apiClient.get<{ clusters: Cluster[] }>(API_ENDPOINTS.TOPICS.DETAIL(topicId));
        setClusters(data.clusters || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load clusters');
      } finally {
        setIsLoading(false);
      }
    };

    fetchClusters();
  }, [topicId]);

  if (isLoading) {
    return <LoadingSpinner size="md" />;
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        <p>Error loading clusters: {error}</p>
      </div>
    );
  }

  if (clusters.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No clusters found for this topic yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Clusters</h3>
      {clusters.slice(0, 5).map((cluster: Cluster) => (
        <div key={cluster.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
          <Link 
            href={`/dashboard/clusters/${cluster.id}`}
            className="font-medium text-gray-900 mb-1 hover:text-blue-600 transition-colors block"
          >
            {cluster.title}
          </Link>
          <p className="text-sm text-gray-600 mb-2 line-clamp-2">{cluster.summary}</p>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>{cluster.article_count} articles</span>
            <span>{new Date(cluster.updated_at).toLocaleDateString()}</span>
          </div>
        </div>
      ))}
      {clusters.length > 5 && (
        <div className="text-center">
          <Link
            href={`/dashboard/topics/${topicId}`}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            View all {clusters.length} clusters →
          </Link>
        </div>
      )}
    </div>
  );
}

export default function TopicsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);

  useEffect(() => {
    // Redirect admin users to system settings
    if (user?.is_admin) {
      router.replace('/dashboard/settings');
      return;
    }
    
    fetchTopics();
  }, [user, router]);

  const fetchTopics = async () => {
    try {
      const data = await apiClient.get<{ topics: Topic[] }>(API_ENDPOINTS.TOPICS.LIST);
      setTopics(data.topics || []);
      
      // Auto-select first active topic if available
      const activeTopics = data.topics?.filter(t => t.active) || [];
      if (activeTopics.length > 0) {
        setSelectedTopic(activeTopics[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load topics');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTopicStatus = async (topic: Topic) => {
    try {
      await apiClient.put(`${API_ENDPOINTS.TOPICS.LIST}/${topic.id}`, {
        ...topic,
        active: !topic.active
      });
      await fetchTopics();
      
      // If we deactivated the selected topic, clear selection
      if (selectedTopic?.id === topic.id && !topic.active) {
        setSelectedTopic(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update topic');
    }
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto mt-8 p-4 border border-red-300 rounded-lg text-red-700">
        <h3 className="font-semibold">Error loading topics</h3>
        <p className="text-sm mt-1">{error}</p>
        <button 
          onClick={() => {
            setError(null);
            fetchTopics();
          }}
          className="mt-2 text-sm underline"
        >
          Try again
        </button>
      </div>
    );
  }

  const activeTopics = topics.filter(topic => topic.active);
  const inactiveTopics = topics.filter(topic => !topic.active);

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4 mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-semibold text-gray-900">Topics</h1>
            <p className="text-gray-600 mt-1">
              Explore your news topics and discover trending clusters
            </p>
          </div>
        </div>
      </div>

      {topics.length === 0 ? (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Topics Yet</h3>
            <p className="text-gray-600 mb-6">
              Create your first topic to start organizing news by your interests.
            </p>
            <Link
              href="/dashboard/settings"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Create Your First Topic
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Topics List */}
          <div className="lg:col-span-1 space-y-4">
            {/* Active Topics */}
            {activeTopics.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-3">
                  Active Topics ({activeTopics.length})
                </h2>
                <div className="space-y-2">
                  {activeTopics.map((topic) => (
                    <div
                      key={topic.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        selectedTopic?.id === topic.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => setSelectedTopic(topic)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900">{topic.name}</h3>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {topic.keywords.slice(0, 3).map((keyword, index) => (
                              <span key={index} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                                {keyword}
                              </span>
                            ))}
                            {topic.keywords.length > 3 && (
                              <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                                +{topic.keywords.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleTopicStatus(topic);
                          }}
                          className="ml-2 text-green-600 hover:text-green-800"
                          title="Deactivate topic"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Inactive Topics */}
            {inactiveTopics.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold text-gray-500 mb-3">
                  Inactive Topics ({inactiveTopics.length})
                </h2>
                <div className="space-y-2">
                  {inactiveTopics.map((topic) => (
                    <div
                      key={topic.id}
                      className="p-4 border border-gray-200 rounded-lg bg-gray-50"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-600">{topic.name}</h3>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {topic.keywords.slice(0, 3).map((keyword, index) => (
                              <span key={index} className="px-2 py-1 text-xs bg-gray-200 text-gray-600 rounded">
                                {keyword}
                              </span>
                            ))}
                            {topic.keywords.length > 3 && (
                              <span className="px-2 py-1 text-xs bg-gray-200 text-gray-500 rounded">
                                +{topic.keywords.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => toggleTopicStatus(topic)}
                          className="ml-2 text-gray-400 hover:text-gray-600"
                          title="Activate topic"
                        >
                          <Plus className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No Active Topics Message */}
            {activeTopics.length === 0 && inactiveTopics.length > 0 && (
              <div className="p-4 border border-yellow-300 rounded-lg bg-yellow-50">
                <p className="text-yellow-800 text-sm">
                  No active topics. Activate at least one topic to see news clusters.
                </p>
              </div>
            )}
          </div>

          {/* Topic Timeline/Clusters View */}
          <div className="lg:col-span-2">
            {selectedTopic ? (
              <div className="border border-gray-200 rounded-lg">
                <div className="p-6 border-b border-gray-200">
                  <Link 
                    href={`/dashboard/topics/${selectedTopic.id}`}
                    className="text-xl font-semibold text-gray-900 hover:text-blue-600 transition-colors block"
                  >
                    {selectedTopic.name}
                  </Link>
                  <p className="text-gray-600 mt-1">
                    News clusters and timeline for this topic
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {selectedTopic.keywords.map((keyword, index) => (
                      <span key={index} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="p-6">
                  <TopicClusters topicId={selectedTopic.id} />
                </div>
              </div>
            ) : activeTopics.length > 0 ? (
              <div className="border border-gray-200 rounded-lg bg-gray-50">
                <div className="p-12 text-center">
                  <div className="max-w-md mx-auto">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Select a Topic
                    </h3>
                    <p className="text-gray-600">
                      Choose a topic from the left to view its news clusters and timeline.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="border border-gray-200 rounded-lg bg-gray-50">
                <div className="p-12 text-center">
                  <div className="max-w-md mx-auto">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No Active Topics
                    </h3>
                    <p className="text-gray-600 mb-6">
                      Activate at least one topic to start seeing news clusters and trends.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}