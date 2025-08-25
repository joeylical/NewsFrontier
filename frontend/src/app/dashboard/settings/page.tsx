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
}

// Provider configuration
interface ProviderUrls {
  [key: string]: string;
}

// Static configuration definitions for frontend display
interface StaticSettingDefinition {
  key: string;
  displayName: string;
  description: string;
  category: string;
  type: 'string' | 'integer' | 'float' | 'boolean';
  isEncrypted?: boolean;
  multiline?: boolean;
  options?: string[];
  minValue?: number;
  maxValue?: number;
  dependsOn?: string;
  dependsValue?: string;
  dependsNotValue?: string;
  modelGroup?: string;
  isSeparatorAfter?: boolean;
  defaultValue?: string;
}

// Static configuration definitions - all display logic in frontend
const createStaticSettingDefinitions = (): StaticSettingDefinition[] => [
  // ===== DEFAULT API CONFIGURATION =====
  {
    key: 'default_llm_provider',
    displayName: 'Default API Provider',
    description: 'Default API provider for all LLM services',
    category: 'Default API Configuration',
    type: 'string',
    options: ['openai', 'anthropic', 'google', 'azure', 'custom'],
    defaultValue: 'openai'
  },
  {
    key: 'default_llm_api_url',
    displayName: 'Default API Base URL',
    description: 'Default API endpoint URL (auto-filled based on provider)',
    category: 'Default API Configuration',
    type: 'string',
    dependsOn: 'default_llm_provider',
    dependsValue: 'custom',
    defaultValue: 'https://api.openai.com/v1'
  },
  {
    key: 'default_llm_api_key_encrypted',
    displayName: 'Default API Key',
    description: 'Default API key for LLM services',
    category: 'Default API Configuration',
    type: 'string',
    isEncrypted: true
  },
  
  // ===== SUMMARY MODEL =====
  {
    key: 'llm_summary_model',
    displayName: 'Article Summary Model',
    description: 'Model name for article summaries (e.g. gpt-3.5-turbo, gemini-2.0-flash-lite)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'summary',
    defaultValue: 'gpt-3.5-turbo'
  },
  {
    key: 'llm_summary_use_default',
    displayName: 'Use Default API',
    description: 'Use default API configuration for summary model',
    category: 'AI & LLM Models',
    type: 'boolean',
    modelGroup: 'summary',
    defaultValue: 'true'
  },
  {
    key: 'llm_summary_api_url',
    displayName: 'Custom API Base URL',
    description: 'Custom API endpoint for summary model (if not using default)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'summary',
    dependsOn: 'llm_summary_use_default',
    dependsNotValue: 'true'
  },
  {
    key: 'llm_summary_api_key_encrypted',
    displayName: 'Custom API Key',
    description: 'Custom API key for summary model (if not using default)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'summary',
    dependsOn: 'llm_summary_use_default',
    dependsNotValue: 'true',
    isEncrypted: true,
    isSeparatorAfter: true
  },
  
  // ===== ANALYSIS MODEL =====
  {
    key: 'llm_analysis_model',
    displayName: 'Analysis Model',
    description: 'Model name for analysis tasks (e.g. gpt-4, gemini-2.5-pro)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'analysis',
    defaultValue: 'gpt-4'
  },
  {
    key: 'llm_analysis_use_default',
    displayName: 'Use Default API',
    description: 'Use default API configuration for analysis model',
    category: 'AI & LLM Models',
    type: 'boolean',
    modelGroup: 'analysis',
    defaultValue: 'true'
  },
  {
    key: 'llm_analysis_api_url',
    displayName: 'Custom API Base URL',
    description: 'Custom API endpoint for analysis model (if not using default)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'analysis',
    dependsOn: 'llm_analysis_use_default',
    dependsNotValue: 'true'
  },
  {
    key: 'llm_analysis_api_key_encrypted',
    displayName: 'Custom API Key',
    description: 'Custom API key for analysis model (if not using default)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'analysis',
    dependsOn: 'llm_analysis_use_default',
    dependsNotValue: 'true',
    isEncrypted: true,
    isSeparatorAfter: true
  },
  
  // ===== EMBEDDING MODEL =====
  {
    key: 'llm_embedding_model',
    displayName: 'Embedding Model',
    description: 'Model name for embeddings (e.g. text-embedding-ada-002, text-embedding-004)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'embedding',
    defaultValue: 'text-embedding-ada-002'
  },
  {
    key: 'llm_embedding_use_default',
    displayName: 'Use Default API',
    description: 'Use default API configuration for embedding model',
    category: 'AI & LLM Models',
    type: 'boolean',
    modelGroup: 'embedding',
    defaultValue: 'true'
  },
  {
    key: 'llm_embedding_api_url',
    displayName: 'Custom API Base URL',
    description: 'Custom API endpoint for embedding model (if not using default)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'embedding',
    dependsOn: 'llm_embedding_use_default',
    dependsNotValue: 'true'
  },
  {
    key: 'llm_embedding_api_key_encrypted',
    displayName: 'Custom API Key',
    description: 'Custom API key for embedding model (if not using default)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'embedding',
    dependsOn: 'llm_embedding_use_default',
    dependsNotValue: 'true',
    isEncrypted: true,
    isSeparatorAfter: true
  },
  
  // ===== IMAGE MODEL =====
  {
    key: 'llm_image_model',
    displayName: 'Image Generation Model',
    description: 'Model name for image generation (e.g. dall-e-3, imagen-3.0-generate-002)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'image',
    defaultValue: 'dall-e-3'
  },
  {
    key: 'llm_image_use_default',
    displayName: 'Use Default API',
    description: 'Use default API configuration for image model',
    category: 'AI & LLM Models',
    type: 'boolean',
    modelGroup: 'image',
    defaultValue: 'true'
  },
  {
    key: 'llm_image_api_url',
    displayName: 'Custom API Base URL',
    description: 'Custom API endpoint for image model (if not using default)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'image',
    dependsOn: 'llm_image_use_default',
    dependsNotValue: 'true'
  },
  {
    key: 'llm_image_api_key_encrypted',
    displayName: 'Custom API Key',
    description: 'Custom API key for image model (if not using default)',
    category: 'AI & LLM Models',
    type: 'string',
    modelGroup: 'image',
    dependsOn: 'llm_image_use_default',
    dependsNotValue: 'true',
    isEncrypted: true,
    isSeparatorAfter: true
  },
  
  // ===== AI FEATURES =====
  {
    key: 'daily_summary_enabled',
    displayName: 'Enable Daily Summary',
    description: 'Enable automatic daily summary generation',
    category: 'AI Features',
    type: 'boolean',
    defaultValue: 'true'
  },
  {
    key: 'daily_summary_cover_enabled',
    displayName: 'Enable Daily Summary Cover',
    description: 'Enable cover image generation for daily summaries',
    category: 'AI Features',
    type: 'boolean',
    defaultValue: 'true'
  },
  
  // ===== AI PROMPTS =====
  {
    key: 'prompt_summary_creation',
    displayName: 'Article Summary Prompt',
    description: 'System prompt for creating article summaries',
    category: 'AI Prompts',
    type: 'string',
    multiline: true,
    defaultValue: 'Create a concise summary of the following news article...'
  },
  {
    key: 'prompt_cluster_detection',
    displayName: 'Cluster Detection Prompt',
    description: 'System prompt for detecting and clustering related news events',
    category: 'AI Prompts',
    type: 'string',
    multiline: true,
    defaultValue: 'Analyze the following news articles and identify clusters...'
  },
  {
    key: 'prompt_daily_summary_system',
    displayName: 'Daily Summary Prompt',
    description: 'System prompt for generating daily news summaries',
    category: 'AI Prompts',
    type: 'string',
    multiline: true,
    defaultValue: 'Generate a comprehensive daily summary...'
  },
  {
    key: 'prompt_cover_image_generation',
    displayName: 'Cover Image Generation Prompt',
    description: 'Prompt template for generating cover image descriptions',
    category: 'AI Prompts',
    type: 'string',
    multiline: true,
    defaultValue: 'Create a compelling cover image description...'
  },
  
  // ===== STORAGE =====
  {
    key: 's3_region',
    displayName: 'S3 Region',
    description: 'AWS S3 region for file storage (e.g. us-east-1, eu-west-1)',
    category: 'Storage',
    type: 'string',
    defaultValue: 'us-east-1'
  },
  {
    key: 's3_bucket',
    displayName: 'S3 Bucket Name',
    description: 'S3 bucket name for storing images and files',
    category: 'Storage',
    type: 'string'
  },
  {
    key: 's3_endpoint_encrypted',
    displayName: 'S3 Endpoint URL',
    description: 'S3 endpoint URL (leave empty for AWS default)',
    category: 'Storage',
    type: 'string',
    isEncrypted: true
  },
  {
    key: 's3_access_key_id_encrypted',
    displayName: 'S3 Access Key ID',
    description: 'AWS access key ID for S3 operations',
    category: 'Storage',
    type: 'string',
    isEncrypted: true
  },
  {
    key: 's3_secret_key_encrypted',
    displayName: 'S3 Secret Access Key',
    description: 'AWS secret access key for S3 operations',
    category: 'Storage',
    type: 'string',
    isEncrypted: true
  },
  
  // ===== PROCESSING =====
  {
    key: 'scraper_interval_minutes',
    displayName: 'Scraper Interval (minutes)',
    description: 'How often the RSS scraper runs (5-1440 minutes)',
    category: 'Processing',
    type: 'integer',
    minValue: 5,
    maxValue: 1440,
    defaultValue: '60'
  },
  {
    key: 'postprocess_interval_minutes',
    displayName: 'Post-process Interval (minutes)',
    description: 'How often post-processing runs (1-60 minutes)',
    category: 'Processing',
    type: 'integer',
    minValue: 1,
    maxValue: 60,
    defaultValue: '30'
  },
  {
    key: 'cluster_threshold',
    displayName: 'Article Clustering Threshold',
    description: 'Similarity threshold for clustering articles (0.1-1.0)',
    category: 'Processing',
    type: 'float',
    minValue: 0.1,
    maxValue: 1.0,
    defaultValue: '0.8'
  },
  {
    key: 'max_processing_attempts',
    displayName: 'Max Processing Attempts',
    description: 'Maximum retry attempts for failed processing (1-10)',
    category: 'Processing',
    type: 'integer',
    minValue: 1,
    maxValue: 10,
    defaultValue: '3'
  },
  {
    key: 'embedding_dimension',
    displayName: 'Embedding Dimension',
    description: 'Vector dimension for embeddings',
    category: 'Processing',
    type: 'string',
    options: ['768', '1536', '3072'],
    defaultValue: '1536'
  }
];

export default function SettingsPage() {
  const { user } = useAuth();
  
  // Define tab configuration first
  const settingTabs = [
    { id: 'default-api', label: 'Default API', icon: '🔑', category: 'Default API Configuration' },
    { id: 'ai-models', label: 'AI Models', icon: '🤖', category: 'AI & LLM Models' },
    { id: 'ai-features', label: 'AI Features', icon: '⚡', category: 'AI Features' },
    { id: 'prompts', label: 'AI Prompts', icon: '💬', category: 'AI Prompts' },
    { id: 'storage', label: 'Storage', icon: '💾', category: 'Storage' },
    { id: 'processing', label: 'Processing', icon: '⚙️', category: 'Processing' }
  ];
  
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
  const [activeTab, setActiveTab] = useState<string>('default-api');

  useEffect(() => {
    fetchData();
    fetchUserSettings();
    if (user?.is_admin) {
      fetchSystemSettings();
    }
  }, [user?.is_admin]);
  
  // Set initial tab based on URL hash or default
  useEffect(() => {
    const hash = window.location.hash.replace('#', '');
    const validTab = settingTabs.find(tab => tab.id === hash);
    if (validTab) {
      setActiveTab(hash);
    }
  }, []);
  
  // Update URL hash when tab changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.history.replaceState(null, '', `#${activeTab}`);
    }
  }, [activeTab]);

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
    setSystemSettings(prev => {
      const existingSetting = prev.find(s => s.setting_key === key);
      if (existingSetting) {
        return prev.map(setting => 
          setting.setting_key === key 
            ? { ...setting, setting_value: value }
            : setting
        );
      } else {
        // Create new setting if it doesn't exist
        const staticDef = staticDefinitions.find(d => d.key === key);
        if (staticDef) {
          const newSetting: SystemSettingItem = {
            setting_key: key,
            setting_value: value,
            setting_type: staticDef.type
          };
          return [...prev, newSetting];
        }
        return prev;
      }
    });
  };

  // Get static definitions for use in component
  const staticDefinitions = createStaticSettingDefinitions();
  
  // Get current tab info
  const currentTab = settingTabs.find(tab => tab.id === activeTab) || settingTabs[0];
  
  // Get display name from static definitions or format from key
  const getDisplayName = (key: string) => {
    const staticDef = staticDefinitions.find(d => d.key === key);
    return staticDef?.displayName || key
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Get settings for current tab
  const getCurrentTabSettings = () => {
    const currentCategory = currentTab.category;
    const categorySettings: { definition: StaticSettingDefinition; setting: SystemSettingItem }[] = [];
    
    staticDefinitions.forEach(staticDef => {
      if (staticDef.category === currentCategory) {
        // Find corresponding system setting or create placeholder
        const systemSetting = systemSettings.find(s => s.setting_key === staticDef.key) || {
          setting_key: staticDef.key,
          setting_value: staticDef.defaultValue || '',
          setting_type: staticDef.type
        };
        
        categorySettings.push({
          definition: staticDef,
          setting: systemSetting
        });
      }
    });
    
    return categorySettings;
  };

  // Check if a setting should be visible based on dependencies
  const isSettingVisible = (definition: StaticSettingDefinition): boolean => {
    if (!definition.dependsOn) return true;
    
    const dependentSetting = systemSettings.find(s => s.setting_key === definition.dependsOn);
    const dependentValue = dependentSetting?.setting_value || '';
    
    if (definition.dependsValue) {
      return dependentValue === definition.dependsValue;
    }
    if (definition.dependsNotValue) {
      return dependentValue !== definition.dependsNotValue;
    }
    
    return true;
  };
  
  // Get provider URLs for auto-completion
  const [providerUrls, setProviderUrls] = useState<ProviderUrls>({
    openai: 'https://api.openai.com/v1',
    anthropic: 'https://api.anthropic.com',
    google: 'https://generativelanguage.googleapis.com/v1beta',
    azure: 'https://YOUR_RESOURCE.openai.azure.com',
    custom: ''
  });
  
  // Auto-update API URLs based on provider selection
  const handleProviderChange = (key: string, provider: string) => {
    updateSettingValue(key, provider);
    
    // Auto-update corresponding API URL if it's the default provider setting
    if (key === 'default_llm_provider') {
      const urlSetting = systemSettings.find(s => s.setting_key === 'default_llm_api_url');
      if (!urlSetting || !urlSetting.setting_value || providerUrls[urlSetting.setting_value]) {
        updateSettingValue('default_llm_api_url', providerUrls[provider] || '');
      }
    }
  };
  
  const renderSettingInput = (definition: StaticSettingDefinition, setting: SystemSettingItem) => {
    const baseClasses = "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500";
    const value = setting.setting_value || '';
    
    // Handle encrypted fields
    if (definition.isEncrypted) {
      const isPlaceholder = value === '<encrypted>';
      return (
        <input
          type="password"
          value={isPlaceholder ? '' : value}
          onChange={(e) => updateSettingValue(definition.key, e.target.value)}
          className={baseClasses}
          placeholder={isPlaceholder ? 'Enter new key to replace encrypted value' : `Enter ${definition.displayName.toLowerCase()}`}
        />
      );
    }
    
    switch (definition.type) {
      case 'boolean':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              id={definition.key}
              checked={value === 'true'}
              onChange={(e) => updateSettingValue(definition.key, e.target.checked.toString())}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
            />
            <label htmlFor={definition.key} className="ml-2 text-sm text-gray-700">
              {definition.displayName}
            </label>
          </div>
        );
      
      case 'integer':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => updateSettingValue(definition.key, e.target.value)}
            min={definition.minValue}
            max={definition.maxValue}
            className={baseClasses}
            step="1"
            placeholder={definition.defaultValue}
          />
        );
      
      case 'float':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => updateSettingValue(definition.key, e.target.value)}
            min={definition.minValue}
            max={definition.maxValue}
            className={baseClasses}
            step="0.1"
            placeholder={definition.defaultValue}
          />
        );
      
      case 'string':
      default:
        // Handle dropdown options
        if (definition.options && definition.options.length > 0) {
          return (
            <select
              value={value}
              onChange={(e) => {
                // Special handling for provider selection
                if (definition.key.includes('provider')) {
                  handleProviderChange(definition.key, e.target.value);
                } else {
                  updateSettingValue(definition.key, e.target.value);
                }
              }}
              className={baseClasses}
            >
              <option value="">Select {definition.displayName}</option>
              {definition.options.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          );
        }
        
        // Multi-line textarea for prompts or long descriptions
        if (definition.multiline || definition.key.includes('prompt')) {
          return (
            <textarea
              value={value}
              onChange={(e) => updateSettingValue(definition.key, e.target.value)}
              className={baseClasses}
              rows={4}
              placeholder={definition.defaultValue || `Enter ${definition.displayName.toLowerCase()}`}
            />
          );
        }
        
        // Regular text input
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => updateSettingValue(definition.key, e.target.value)}
            className={baseClasses}
            placeholder={definition.defaultValue || `Enter ${definition.displayName.toLowerCase()}`}
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

  // Load provider URLs on component mount
  useEffect(() => {
    if (user?.is_admin) {
      const fetchProviderUrls = async () => {
        try {
          const urls = await apiClient.get<ProviderUrls>(API_ENDPOINTS.ADMIN.PROVIDER_URLS);
          setProviderUrls(urls);
        } catch (err) {
          console.error('Failed to load provider URLs:', err);
        }
      };
      fetchProviderUrls();
    }
  }, [user?.is_admin]);
  
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
  
  // Get description for each tab
  const getTabDescription = (tabId: string): string => {
    const descriptions = {
      'default-api': 'Configure the default API provider and credentials used across all AI services',
      'ai-models': 'Set up specific models for different AI tasks with custom API configurations',
      'ai-features': 'Enable or disable AI-powered features like daily summaries and cover images',
      'prompts': 'Customize AI prompts used for content generation and analysis',
      'storage': 'Configure S3 storage settings for images and file uploads',
      'processing': 'Adjust processing intervals, thresholds, and system performance parameters'
    };
    return descriptions[tabId as keyof typeof descriptions] || 'Configure system settings';
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="flex justify-between items-center">
          <div>
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
          {/* Breadcrumb for admin users */}
          {user?.is_admin && currentTab && (
            <nav className="flex items-center space-x-2 text-sm text-gray-500">
              <span>Settings</span>
              <span>/</span>
              <span className="flex items-center gap-1 text-blue-600 font-medium">
                <span className="text-base">{currentTab.icon}</span>
                {currentTab.label}
              </span>
            </nav>
          )}
        </div>
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
          
          {/* Tab Layout */}
          <div className="flex min-h-[600px]">
            {/* Left Sidebar - Tab Navigation */}
            <div className="w-64 border-r border-gray-200 bg-gray-50 flex flex-col">
              <nav className="p-4 space-y-1">
                {settingTabs.map((tab) => {
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2 text-left rounded-md transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-900 border-l-4 border-blue-500'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <span className="text-lg">{tab.icon}</span>
                      <span className="text-sm font-medium">{tab.label}</span>
                    </button>
                  );
                })}
              </nav>
              
              {/* Save Button in Sidebar */}
              <div className="p-4 border-t border-gray-200 mt-auto">
                <button
                  onClick={updateSystemSettings}
                  disabled={isSavingSystem}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isSavingSystem ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Saving...
                    </>
                  ) : (
                    'Save Settings'
                  )}
                </button>
              </div>
            </div>
            
            {/* Right Content Area */}
            <div className="flex-1">
              <div className="p-6">
                {currentTab ? (
                  <>
                    {/* Tab Header */}
                    <div className="mb-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                            <span className="text-2xl">{currentTab.icon}</span>
                            {currentTab.label}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            {getTabDescription(currentTab.id)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {getCurrentTabSettings().length} settings
                          </span>
                        </div>
                      </div>
                    </div>
                
                {/* Tab Content */}
                <div className="space-y-6">
                  {(() => {
                    const tabSettings = getCurrentTabSettings();
                    
                    // Group by model groups within current tab
                    const modelGroups: Record<string, typeof tabSettings> = { '': [] };
                    
                    tabSettings.forEach(item => {
                      const groupKey = item.definition.modelGroup || '';
                      if (!modelGroups[groupKey]) {
                        modelGroups[groupKey] = [];
                      }
                      modelGroups[groupKey].push(item);
                    });
                    
                    return Object.entries(modelGroups).map(([modelGroup, groupItems]) => {
                      // Filter out items that shouldn't be visible due to dependencies
                      const visibleItems = groupItems.filter(item => isSettingVisible(item.definition));
                      
                      if (visibleItems.length === 0) return null;
                      
                      return (
                        <div key={`${currentTab.id}-${modelGroup}`} className="space-y-4">
                          {modelGroup && (
                            <div className="border-l-4 border-blue-400 pl-4">
                              <h4 className="text-lg font-medium text-gray-800 capitalize">
                                {modelGroup} Model Configuration
                              </h4>
                              <p className="text-sm text-gray-600 mt-1">
                                Configure {modelGroup} model API settings and credentials
                              </p>
                            </div>
                          )}
                          
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {visibleItems.map(({ definition, setting }) => (
                              <div key={definition.key} className={
                                definition.multiline || definition.key.includes('prompt') 
                                  ? 'lg:col-span-2' 
                                  : ''
                              }>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                  {definition.displayName}
                                  {definition.isEncrypted && (
                                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                                      🔒 Encrypted
                                    </span>
                                  )}
                                </label>
                                {renderSettingInput(definition, setting)}
                                {definition.description && (
                                  <p className="text-xs text-gray-500 mt-2">
                                    {definition.description}
                                  </p>
                                )}
                                {definition.minValue !== undefined && definition.maxValue !== undefined && (
                                  <p className="text-xs text-blue-600 mt-1">
                                    Range: {definition.minValue} - {definition.maxValue}
                                  </p>
                                )}
                                
                                {/* Add separator after certain settings */}
                                {definition.isSeparatorAfter && (
                                  <div className="mt-6 border-b border-gray-200"></div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    });
                  })()
                  }
                  
                  {/* Empty state for tabs with no settings */}
                  {getCurrentTabSettings().length === 0 && (
                    <div className="text-center py-12">
                      <div className="text-4xl mb-4">{currentTab.icon}</div>
                      <h4 className="text-lg font-medium text-gray-900 mb-2">No Settings Available</h4>
                      <p className="text-gray-600">This section is currently empty or under development.</p>
                    </div>
                  )}
                    </div>
                  </>
                ) : (
                  <div className="flex items-center justify-center h-64">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                      <p className="text-gray-600">Loading settings...</p>
                    </div>
                  </div>
                )}
              </div>
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
