'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { Topic, RSSFeed, User } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import Modal from '@/components/Modal';
import { useAuth } from '@/lib/auth-context';
import { Check, X } from 'lucide-react';

interface TopicFormData {
  name: string;
  keywords?: string; // Keep for internal state management but not used in API
  active: boolean;
}

interface RSSFeedFormData {
  url: string;
  title: string;
}

interface UserSettings {
  daily_summary_prompt: string;
}

interface SystemSettingItem {
  setting_key: string;
  setting_value: string;
  setting_type: 'string' | 'integer' | 'float' | 'boolean';
  setting_description?: string;
  setting_category?: string;
  min_value?: number;
  max_value?: number;
  options?: string[];
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
  
  // Feedback states
  const [isSavingUser, setIsSavingUser] = useState(false);
  const [isSavingSystem, setIsSavingSystem] = useState(false);
  const [feedbackModal, setFeedbackModal] = useState<{
    isOpen: boolean;
    type: 'success' | 'error';
    title: string;
    message: string;
  }>({ isOpen: false, type: 'success', title: '', message: '' });
  const [rssForm, setRSSForm] = useState<RSSFeedFormData>({
    url: '',
    title: ''
  });
  const [userSettings, setUserSettings] = useState<UserSettings>({
    daily_summary_prompt: ''
  });
  const [systemSettings, setSystemSettings] = useState<SystemSettingItem[]>([]);

  useEffect(() => {
    fetchData();
    fetchUserSettings();
    if (user?.is_admin) {
      fetchSystemSettings();
    }
  }, [user?.is_admin]);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [topicsData, rssData] = await Promise.all([
        apiClient.get<{ topics: Topic[] }>(API_ENDPOINTS.TOPICS.LIST),
        // User's subscribed RSS feeds
        apiClient.get<RSSFeed[]>(API_ENDPOINTS.RSS_FEEDS.LIST).catch(() => [])
      ]);
      
      setTopics(topicsData.topics || []);
      setRssFeeds(Array.isArray(rssData) ? rssData : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings data');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUserSettings = async () => {
    try {
      const userData = await apiClient.get<User>(API_ENDPOINTS.AUTH.USER_INFO);
      setUserSettings({
        daily_summary_prompt: userData.daily_summary_prompt || ''
      });
    } catch (err) {
      console.error('Failed to load user settings:', err);
    }
  };

  const updateUserSettings = async () => {
    setIsSavingUser(true);
    try {
      await apiClient.put(API_ENDPOINTS.AUTH.USER_SETTINGS, userSettings);
      setError(null);
      setFeedbackModal({
        isOpen: true,
        type: 'success',
        title: 'Success!',
        message: 'Your preferences have been saved successfully.'
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update user settings';
      setError(errorMessage);
      setFeedbackModal({
        isOpen: true,
        type: 'error',
        title: 'Error',
        message: errorMessage
      });
    } finally {
      setIsSavingUser(false);
    }
  };

  const fetchSystemSettings = async () => {
    try {
      const response = await apiClient.get<SystemSettingItem[]>(API_ENDPOINTS.ADMIN.SETTINGS);
      setSystemSettings(response);
    } catch (err) {
      console.error('Failed to load system settings:', err);
    }
  };

  const updateSystemSettings = async () => {
    setIsSavingSystem(true);
    try {
      await apiClient.put(API_ENDPOINTS.ADMIN.SETTINGS, systemSettings);
      setError(null);
      setFeedbackModal({
        isOpen: true,
        type: 'success',
        title: 'Success!',
        message: 'All system settings have been saved successfully.'
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update system settings';
      setError(errorMessage);
      setFeedbackModal({
        isOpen: true,
        type: 'error',
        title: 'Error',
        message: errorMessage
      });
    } finally {
      setIsSavingSystem(false);
    }
  };

  const updateSettingValue = (key: string, value: string) => {
    setSystemSettings(prev => 
      prev.map(setting => 
        setting.setting_key === key 
          ? { ...setting, setting_value: value }
          : setting
      )
    );
  };

  const formatSettingLabel = (key: string) => {
    return key
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const groupSettingsByCategory = (settings: SystemSettingItem[]) => {
    const grouped = settings.reduce((acc, setting) => {
      const category = setting.setting_category || 'General';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(setting);
      return acc;
    }, {} as Record<string, SystemSettingItem[]>);
    
    return grouped;
  };

  const renderSettingInput = (setting: SystemSettingItem) => {
    const baseClasses = "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500";
    
    switch (setting.setting_type) {
      case 'boolean':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              id={setting.setting_key}
              checked={setting.setting_value === 'true'}
              onChange={(e) => updateSettingValue(setting.setting_key, e.target.checked.toString())}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
            />
            <label htmlFor={setting.setting_key} className="ml-2 text-sm text-gray-700">
              Enable {formatSettingLabel(setting.setting_key)}
            </label>
          </div>
        );
      
      case 'integer':
        return (
          <input
            type="number"
            value={setting.setting_value}
            onChange={(e) => updateSettingValue(setting.setting_key, e.target.value)}
            min={setting.min_value}
            max={setting.max_value}
            className={baseClasses}
            step="1"
          />
        );
      
      case 'float':
        return (
          <input
            type="number"
            value={setting.setting_value}
            onChange={(e) => updateSettingValue(setting.setting_key, e.target.value)}
            min={setting.min_value}
            max={setting.max_value}
            className={baseClasses}
            step="0.1"
          />
        );
      
      case 'string':
      default:
        if (setting.options && setting.options.length > 0) {
          return (
            <select
              value={setting.setting_value}
              onChange={(e) => updateSettingValue(setting.setting_key, e.target.value)}
              className={baseClasses}
            >
              {setting.options.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          );
        }
        
        // Multi-line for prompts or long text
        if (setting.setting_key.includes('prompt') || setting.setting_value.length > 100) {
          return (
            <textarea
              value={setting.setting_value}
              onChange={(e) => updateSettingValue(setting.setting_key, e.target.value)}
              className={baseClasses}
              rows={4}
              placeholder={`Enter ${formatSettingLabel(setting.setting_key).toLowerCase()}`}
            />
          );
        }
        
        return (
          <input
            type="text"
            value={setting.setting_value}
            onChange={(e) => updateSettingValue(setting.setting_key, e.target.value)}
            className={baseClasses}
            placeholder={`Enter ${formatSettingLabel(setting.setting_key).toLowerCase()}`}
          />
        );
    }
  };

  // Topic management functions
  const handleTopicSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        name: topicForm.name,
        keywords: [],
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
        keywords: '', // Don't populate keywords from existing topic
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

      if (editingRSSFeed) {
        await apiClient.put(API_ENDPOINTS.RSS_FEEDS.UPDATE(editingRSSFeed.uuid), data);
      } else {
        await apiClient.post(API_ENDPOINTS.RSS_FEEDS.CREATE, data);
      }

      await fetchData();
      closeRSSModal();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save RSS feed');
    }
  };

  const handleDeleteRSSFeed = async (feed: RSSFeed) => {
    if (confirm('Are you sure you want to delete this RSS feed?')) {
      try {
        await apiClient.delete(API_ENDPOINTS.RSS_FEEDS.DELETE(feed.uuid));
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
        title: feed.title || ''
      });
    } else {
      setEditingRSSFeed(null);
      setRSSForm({
        url: '',
        title: ''
      });
    }
    setIsRSSModalOpen(true);
  };

  const closeRSSModal = () => {
    setIsRSSModalOpen(false);
    setEditingRSSFeed(null);
    setRSSForm({ url: '', title: '' });
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-semibold text-gray-900">
          {user?.is_admin ? 'System Settings' : 'Settings'}
        </h1>
        <p className="text-gray-600 mt-1">
          {user?.is_admin 
            ? 'Manage AI processing prompts and system configuration' 
            : 'Manage your topics and preferences'
          }
        </p>
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

      {/* User Settings - Hidden for Admin Users */}
      {!user?.is_admin && (
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
                  disabled={isSavingUser}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isSavingUser ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Saving...
                    </>
                  ) : (
                    'Save Preferences'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Topics Management - Hidden for Admin Users */}
      {!user?.is_admin && (
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
      )}

      {/* User RSS Feeds Management - Hidden for Admin Users */}
      {!user?.is_admin && (
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
                        onClick={() => handleDeleteRSSFeed(feed)}
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


      {/* System Settings (Admin Only) */}
      {user?.is_admin && (
        <div className="border border-gray-200 rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">System Settings</h2>
            <p className="text-sm text-gray-600 mt-1">
              Configure system-wide parameters and AI processing settings (Admin only)
            </p>
          </div>
          
          <div className="p-6 space-y-8">
            {systemSettings.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">Loading system settings...</p>
              </div>
            ) : (
              Object.entries(groupSettingsByCategory(systemSettings)).map(([category, settings]) => (
                <div key={category} className="space-y-6">
                  <h3 className="text-md font-semibold text-gray-800 border-b border-gray-200 pb-2">
                    {category}
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {settings.map((setting) => (
                      <div key={setting.setting_key} className={
                        setting.setting_key.includes('prompt') || setting.setting_value.length > 100 
                          ? 'md:col-span-2' 
                          : ''
                      }>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          {formatSettingLabel(setting.setting_key)}
                        </label>
                        {renderSettingInput(setting)}
                        {setting.setting_description && (
                          <p className="text-xs text-gray-500 mt-1">
                            {setting.setting_description}
                          </p>
                        )}
                        {setting.min_value !== undefined && setting.max_value !== undefined && (
                          <p className="text-xs text-gray-500 mt-1">
                            Range: {setting.min_value} - {setting.max_value}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
            
            <div className="flex justify-end pt-4 border-t border-gray-200">
              <button
                onClick={updateSystemSettings}
                disabled={isSavingSystem}
                className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSavingSystem ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Saving...
                  </>
                ) : (
                  'Save All Settings'
                )}
              </button>
            </div>
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

      {/* RSS Feed Modal */}
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

      {/* Feedback Modal */}
      <Modal
        isOpen={feedbackModal.isOpen}
        onClose={() => setFeedbackModal({ ...feedbackModal, isOpen: false })}
        title={feedbackModal.title}
      >
        <div className="text-center py-4">
          <div className={`mx-auto flex items-center justify-center h-12 w-12 rounded-full mb-4 ${
            feedbackModal.type === 'success' ? 'bg-green-100' : 'bg-red-100'
          }`}>
            {feedbackModal.type === 'success' ? (
              <Check className={`h-6 w-6 text-green-600`} />
            ) : (
              <X className={`h-6 w-6 text-red-600`} />
            )}
          </div>
          <p className="text-gray-700 mb-6">{feedbackModal.message}</p>
          <button
            onClick={() => setFeedbackModal({ ...feedbackModal, isOpen: false })}
            className={`px-4 py-2 rounded text-white transition-colors ${
              feedbackModal.type === 'success' 
                ? 'bg-green-600 hover:bg-green-700' 
                : 'bg-red-600 hover:bg-red-700'
            }`}
          >
            OK
          </button>
        </div>
      </Modal>
    </div>
  );
}
