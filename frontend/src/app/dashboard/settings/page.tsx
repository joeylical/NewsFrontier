'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { Topic, RSSFeed, User } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import Modal from '@/components/Modal';
import { useAuth } from '@/lib/auth-context';

interface TopicFormData {
  name: string;
  keywords: string;
  active: boolean;
}

interface RSSFeedFormData {
  url: string;
  title: string;
  fetch_interval_minutes: number;
}

interface UserSettings {
  daily_summary_prompt: string;
}

export default function SettingsPage() {
  const { user } = useAuth();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [rssFeeds, setRssFeeds] = useState<RSSFeed[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [isTopicModalOpen, setIsTopicModalOpen] = useState(false);
  const [isRSSModalOpen, setIsRSSModalOpen] = useState(false);
  const [editingTopic, setEditingTopic] = useState<Topic | null>(null);
  const [editingRSSFeed, setEditingRSSFeed] = useState<RSSFeed | null>(null);

  // Form data
  const [topicForm, setTopicForm] = useState<TopicFormData>({
    name: '',
    keywords: '',
    active: true
  });
  const [rssForm, setRSSForm] = useState<RSSFeedFormData>({
    url: '',
    title: '',
    fetch_interval_minutes: 60
  });
  const [userSettings, setUserSettings] = useState<UserSettings>({
    daily_summary_prompt: ''
  });
  
  // User RSS feeds (for non-admin users)
  const [userRssFeeds, setUserRssFeeds] = useState<RSSFeed[]>([]);

  useEffect(() => {
    fetchData();
    fetchUserSettings();
  }, []);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [topicsData, adminRssData, userRssData] = await Promise.all([
        apiClient.get<{ topics: Topic[] }>(API_ENDPOINTS.TOPICS.LIST),
        // Admin RSS feeds
        user?.is_admin ? apiClient.get<RSSFeed[]>(API_ENDPOINTS.ADMIN.RSS_FEEDS).catch(() => []) : Promise.resolve([]),
        // User's subscribed RSS feeds
        apiClient.get<RSSFeed[]>('/api/user/rss-feeds').catch(() => [])
      ]);
      
      setTopics(topicsData.topics || []);
      setRssFeeds(Array.isArray(adminRssData) ? adminRssData : []);
      setUserRssFeeds(Array.isArray(userRssData) ? userRssData : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings data');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUserSettings = async () => {
    try {
      const userData = await apiClient.get<User>('/api/user/me');
      setUserSettings({
        daily_summary_prompt: userData.daily_summary_prompt || ''
      });
    } catch (err) {
      console.error('Failed to load user settings:', err);
    }
  };

  const updateUserSettings = async () => {
    try {
      await apiClient.put('/api/user/settings', userSettings);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user settings');
    }
  };

  // Topic management functions
  const handleTopicSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        name: topicForm.name,
        keywords: topicForm.keywords.split(',').map(k => k.trim()).filter(k => k),
        active: topicForm.active
      };

      if (editingTopic) {
        await apiClient.put(`${API_ENDPOINTS.TOPICS.LIST}/${editingTopic.id}`, data);
      } else {
        await apiClient.post(API_ENDPOINTS.TOPICS.CREATE, data);
      }

      await fetchData();
      closeTopicModal();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save topic');
    }
  };

  const handleDeleteTopic = async (topicId: number) => {
    if (confirm('Are you sure you want to delete this topic?')) {
      try {
        await apiClient.delete(`${API_ENDPOINTS.TOPICS.LIST}/${topicId}`);
        await fetchData();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete topic');
      }
    }
  };

  const openTopicModal = (topic?: Topic) => {
    if (topic) {
      setEditingTopic(topic);
      setTopicForm({
        name: topic.name,
        keywords: topic.keywords.join(', '),
        active: topic.active
      });
    } else {
      setEditingTopic(null);
      setTopicForm({
        name: '',
        keywords: '',
        active: true
      });
    }
    setIsTopicModalOpen(true);
  };

  const closeTopicModal = () => {
    setIsTopicModalOpen(false);
    setEditingTopic(null);
    setTopicForm({ name: '', keywords: '', active: true });
  };

  // RSS Feed management functions
  const handleRSSSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = rssForm;
      const endpoint = user?.is_admin ? API_ENDPOINTS.ADMIN.RSS_FEEDS : '/api/user/rss-feeds';

      if (editingRSSFeed) {
        await apiClient.put(`${endpoint}/${editingRSSFeed.id}`, data);
      } else {
        await apiClient.post(endpoint, data);
      }

      await fetchData();
      closeRSSModal();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save RSS feed');
    }
  };

  const handleDeleteRSSFeed = async (feedId: number, isUserFeed = false) => {
    if (confirm('Are you sure you want to delete this RSS feed?')) {
      try {
        const endpoint = isUserFeed || !user?.is_admin ? '/api/user/rss-feeds' : API_ENDPOINTS.ADMIN.RSS_FEEDS;
        await apiClient.delete(`${endpoint}/${feedId}`);
        await fetchData();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete RSS feed');
      }
    }
  };

  const openRSSModal = (feed?: RSSFeed) => {
    if (feed) {
      setEditingRSSFeed(feed);
      setRSSForm({
        url: feed.url,
        title: feed.title || '',
        fetch_interval_minutes: feed.fetch_interval_minutes
      });
    } else {
      setEditingRSSFeed(null);
      setRSSForm({
        url: '',
        title: '',
        fetch_interval_minutes: 60
      });
    }
    setIsRSSModalOpen(true);
  };

  const closeRSSModal = () => {
    setIsRSSModalOpen(false);
    setEditingRSSFeed(null);
    setRSSForm({ url: '', title: '', fetch_interval_minutes: 60 });
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-semibold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your topics and preferences</p>
      </div>

      {error && (
        <div className="p-4 border border-red-300 rounded-lg text-red-700 bg-red-50">
          <p>{error}</p>
          <button 
            onClick={() => setError(null)}
            className="mt-2 text-sm underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* User Settings */}
      <div className="border border-gray-200 rounded-lg shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">User Preferences</h2>
          <p className="text-sm text-gray-600 mt-1">
            Customize your news experience and daily summaries
          </p>
        </div>
        
        <div className="p-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Daily Summary Prompt
              </label>
              <textarea
                value={userSettings.daily_summary_prompt}
                onChange={(e) => setUserSettings({ ...userSettings, daily_summary_prompt: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="Enter your custom prompt for daily news summaries (optional)"
              />
              <p className="text-xs text-gray-500 mt-1">
                This prompt will be used to customize your daily news summaries. Leave empty to use the default prompt.
              </p>
            </div>
            
            <div className="flex justify-end">
              <button
                onClick={updateUserSettings}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Save Preferences
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Topics Management */}
      <div className="border border-gray-200 rounded-lg shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Topics</h2>
              <p className="text-sm text-gray-600 mt-1">
                Manage your news topics and keywords
              </p>
            </div>
            <button
              onClick={() => openTopicModal()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Add Topic
            </button>
          </div>
        </div>
        
        <div className="divide-y divide-gray-200">
          {topics.length > 0 ? (
            topics.map((topic) => (
              <div key={topic.id} className="p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-gray-900">{topic.name}</h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        topic.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {topic.active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {topic.keywords.map((keyword, index) => (
                        <span key={index} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => openTopicModal(topic)}
                      className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteTopic(topic.id)}
                      className="px-3 py-1 text-sm border border-red-300 text-red-600 rounded hover:bg-red-50"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-gray-500">
              <p>No topics configured yet.</p>
              <button
                onClick={() => openTopicModal()}
                className="mt-2 text-blue-600 hover:text-blue-800 underline"
              >
                Add your first topic
              </button>
            </div>
          )}
        </div>
      </div>

      {/* User RSS Feeds Management */}
      <div className="border border-gray-200 rounded-lg shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">My RSS Sources</h2>
              <p className="text-sm text-gray-600 mt-1">
                Manage your personal RSS feed subscriptions
              </p>
            </div>
            <button
              onClick={() => openRSSModal()}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            >
              Add RSS Feed
            </button>
          </div>
        </div>
        
        <div className="divide-y divide-gray-200">
          {userRssFeeds.length > 0 ? (
            userRssFeeds.map((feed) => (
              <div key={feed.id} className="p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{feed.title || 'Untitled Feed'}</h3>
                    <p className="text-sm text-gray-600 mt-1">{feed.url}</p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                      <span>Interval: {feed.fetch_interval_minutes}min</span>
                      <span className={`px-2 py-1 rounded-full ${
                        feed.last_fetch_status === 'success' ? 'bg-green-100 text-green-800' :
                        feed.last_fetch_status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {feed.last_fetch_status}
                      </span>
                      {feed.last_fetch_at && (
                        <span>Last fetch: {new Date(feed.last_fetch_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => openRSSModal(feed)}
                      className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteRSSFeed(feed.id, true)}
                      className="px-3 py-1 text-sm border border-red-300 text-red-600 rounded hover:bg-red-50"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-gray-500">
              <p>No RSS feeds configured yet.</p>
              <button
                onClick={() => openRSSModal()}
                className="mt-2 text-green-600 hover:text-green-800 underline"
              >
                Add your first RSS feed
              </button>
            </div>
          )}
        </div>
      </div>

      {/* System RSS Feeds Management (Admin Only) */}
      {user?.is_admin && (
        <div className="border border-gray-200 rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">System RSS Sources</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Manage global RSS feed sources (Admin only)
                </p>
              </div>
              <button
                onClick={() => openRSSModal()}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
              >
                Add RSS Feed
              </button>
            </div>
          </div>
          
          <div className="divide-y divide-gray-200">
            {rssFeeds.length > 0 ? (
              rssFeeds.map((feed) => (
                <div key={feed.id} className="p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{feed.title || 'Untitled Feed'}</h3>
                      <p className="text-sm text-gray-600 mt-1">{feed.url}</p>
                      <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                        <span>Interval: {feed.fetch_interval_minutes}min</span>
                        <span className={`px-2 py-1 rounded-full ${
                          feed.last_fetch_status === 'success' ? 'bg-green-100 text-green-800' :
                          feed.last_fetch_status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {feed.last_fetch_status}
                        </span>
                        {feed.last_fetch_at && (
                          <span>Last fetch: {new Date(feed.last_fetch_at).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => openRSSModal(feed)}
                        className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteRSSFeed(feed.id)}
                        className="px-3 py-1 text-sm border border-red-300 text-red-600 rounded hover:bg-red-50"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-gray-500">
                <p>No RSS feeds configured yet.</p>
                <button
                  onClick={() => openRSSModal()}
                  className="mt-2 text-green-600 hover:text-green-800 underline"
                >
                  Add your first RSS feed
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Topic Modal */}
      <Modal
        isOpen={isTopicModalOpen}
        onClose={closeTopicModal}
        title={editingTopic ? 'Edit Topic' : 'Add New Topic'}
      >
        <form onSubmit={handleTopicSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Topic Name
            </label>
            <input
              type="text"
              value={topicForm.name}
              onChange={(e) => setTopicForm({ ...topicForm, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
              placeholder="e.g., Technology, Politics, Sports"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Keywords (comma-separated)
            </label>
            <textarea
              value={topicForm.keywords}
              onChange={(e) => setTopicForm({ ...topicForm, keywords: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              placeholder="e.g., AI, artificial intelligence, machine learning, automation"
            />
            <p className="text-xs text-gray-500 mt-1">
              Separate keywords with commas. These help categorize articles automatically.
            </p>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="active"
              checked={topicForm.active}
              onChange={(e) => setTopicForm({ ...topicForm, active: e.target.checked })}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
            />
            <label htmlFor="active" className="ml-2 text-sm text-gray-700">
              Active (receive news for this topic)
            </label>
          </div>
          
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={closeTopicModal}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              {editingTopic ? 'Update' : 'Create'} Topic
            </button>
          </div>
        </form>
      </Modal>

      {/* RSS Feed Modal (Admin only) */}
      {user?.is_admin && (
        <Modal
          isOpen={isRSSModalOpen}
          onClose={closeRSSModal}
          title={editingRSSFeed ? 'Edit RSS Feed' : 'Add New RSS Feed'}
        >
          <form onSubmit={handleRSSSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                RSS Feed URL
              </label>
              <input
                type="url"
                value={rssForm.url}
                onChange={(e) => setRSSForm({ ...rssForm, url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                required
                placeholder="https://example.com/rss.xml"
              />
              <p className="text-xs text-gray-500 mt-1">
                Enter a valid RSS or Atom feed URL
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Feed Title (optional)
              </label>
              <input
                type="text"
                value={rssForm.title}
                onChange={(e) => setRSSForm({ ...rssForm, title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                placeholder="Custom name for this feed"
              />
              <p className="text-xs text-gray-500 mt-1">
                If left empty, the feed title will be automatically detected
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fetch Interval (minutes)
              </label>
              <select
                value={rssForm.fetch_interval_minutes}
                onChange={(e) => setRSSForm({ ...rssForm, fetch_interval_minutes: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
              >
                <option value={15}>15 minutes</option>
                <option value={30}>30 minutes</option>
                <option value={60}>1 hour</option>
                <option value={120}>2 hours</option>
                <option value={240}>4 hours</option>
                <option value={480}>8 hours</option>
                <option value={720}>12 hours</option>
                <option value={1440}>24 hours</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                How often to check this feed for new articles
              </p>
            </div>
            
            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={closeRSSModal}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
              >
                {editingRSSFeed ? 'Update' : 'Create'} Feed
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}