'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { Topic, RSSFeed, User } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import Modal from '@/components/Modal';
import YamlEditor from '@/components/YamlEditor';
import FileSelector from '@/components/FileSelector';
import { useAuth } from '@/lib/auth-context';
import { Check, X, ChevronDown, ChevronRight } from 'lucide-react';

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
  isYaml?: boolean;
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
    category: 'API & Models Configuration',
    type: 'string',
    options: ['openai', 'anthropic', 'google', 'azure', 'custom'],
    defaultValue: 'openai'
  },
  {
    key: 'default_llm_api_url',
    displayName: 'Default API Base URL',
    description: 'Default API endpoint URL (auto-filled based on provider)',
    category: 'API & Models Configuration',
    type: 'string',
    dependsOn: 'default_llm_provider',
    dependsValue: 'custom',
    defaultValue: 'https://api.openai.com/v1'
  },
  {
    key: 'default_llm_api_key_encrypted',
    displayName: 'Default API Key',
    description: 'Default API key for LLM services',
    category: 'API & Models Configuration',
    type: 'string',
    isEncrypted: true
  },

  // ===== SUMMARY MODEL =====
  {
    key: 'llm_summary_model',
    displayName: 'Article Summary Model',
    description: 'Model name for article summaries (e.g. gpt-3.5-turbo, gemini-2.0-flash-lite)',
    category: 'API & Models Configuration',
    type: 'string',
    modelGroup: 'summary',
    defaultValue: 'gpt-3.5-turbo'
  },
  {
    key: 'llm_summary_use_default',
    displayName: 'Use Default API',
    description: 'Use default API configuration for summary model',
    category: 'API & Models Configuration',
    type: 'boolean',
    modelGroup: 'summary',
    defaultValue: 'true'
  },
  {
    key: 'llm_summary_api_url',
    displayName: 'Custom API Base URL',
    description: 'Custom API endpoint for summary model (if not using default)',
    category: 'API & Models Configuration',
    type: 'string',
    modelGroup: 'summary',
    dependsOn: 'llm_summary_use_default',
    dependsNotValue: 'true'
  },
  {
    key: 'llm_summary_api_key_encrypted',
    displayName: 'Custom API Key',
    description: 'Custom API key for summary model (if not using default)',
    category: 'API & Models Configuration',
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
    category: 'API & Models Configuration',
    type: 'string',
    modelGroup: 'analysis',
    defaultValue: 'gpt-4'
  },
  {
    key: 'llm_analysis_use_default',
    displayName: 'Use Default API',
    description: 'Use default API configuration for analysis model',
    category: 'API & Models Configuration',
    type: 'boolean',
    modelGroup: 'analysis',
    defaultValue: 'true'
  },
  {
    key: 'llm_analysis_api_url',
    displayName: 'Custom API Base URL',
    description: 'Custom API endpoint for analysis model (if not using default)',
    category: 'API & Models Configuration',
    type: 'string',
    modelGroup: 'analysis',
    dependsOn: 'llm_analysis_use_default',
    dependsNotValue: 'true'
  },
  {
    key: 'llm_analysis_api_key_encrypted',
    displayName: 'Custom API Key',
    description: 'Custom API key for analysis model (if not using default)',
    category: 'API & Models Configuration',
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
    category: 'API & Models Configuration',
    type: 'string',
    modelGroup: 'embedding',
    defaultValue: 'text-embedding-ada-002'
  },
  {
    key: 'llm_embedding_use_default',
    displayName: 'Use Default API',
    description: 'Use default API configuration for embedding model',
    category: 'API & Models Configuration',
    type: 'boolean',
    modelGroup: 'embedding',
    defaultValue: 'true'
  },
  {
    key: 'llm_embedding_api_url',
    displayName: 'Custom API Base URL',
    description: 'Custom API endpoint for embedding model (if not using default)',
    category: 'API & Models Configuration',
    type: 'string',
    modelGroup: 'embedding',
    dependsOn: 'llm_embedding_use_default',
    dependsNotValue: 'true'
  },
  {
    key: 'llm_embedding_api_key_encrypted',
    displayName: 'Custom API Key',
    description: 'Custom API key for embedding model (if not using default)',
    category: 'API & Models Configuration',
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
    category: 'API & Models Configuration',
    type: 'string',
    modelGroup: 'image',
    defaultValue: 'dall-e-3'
  },
  {
    key: 'llm_image_use_default',
    displayName: 'Use Default API',
    description: 'Use default API configuration for image model',
    category: 'API & Models Configuration',
    type: 'boolean',
    modelGroup: 'image',
    defaultValue: 'true'
  },
  {
    key: 'llm_image_api_url',
    displayName: 'Custom API Base URL',
    description: 'Custom API endpoint for image model (if not using default)',
    category: 'API & Models Configuration',
    type: 'string',
    modelGroup: 'image',
    dependsOn: 'llm_image_use_default',
    dependsNotValue: 'true'
  },
  {
    key: 'llm_image_api_key_encrypted',
    displayName: 'Custom API Key',
    description: 'Custom API key for image model (if not using default)',
    category: 'API & Models Configuration',
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
    dependsOn: 'daily_summary_enabled',
    dependsNotValue: 'false',
    defaultValue: 'true'
  },

  // ===== AI PROMPTS (All YAML-based) =====
  {
    key: 'prompt_summary_creation',
    displayName: 'Article Summary Configuration',
    description: 'YAML configuration for article summary generation',
    category: 'AI Prompts',
    type: 'string',
    multiline: true,
    isYaml: true,
    defaultValue: `name: Article Summary Generation
description: Generate concise summaries for news articles
stages:
  - name: summary_generation
    type: final
    prompt: |
      Create a concise summary of the following news article:
      
      Title: {title}
      Content: {clean_text}
      
      Requirements:
      - Keep it under 150 words
      - Focus on key facts and main points
      - Use clear, engaging language
      - Maintain objectivity
    llm_params:
      temperature: 0.3
      max_tokens: 500`
  },
  {
    key: 'prompt_cluster_detection',
    displayName: 'Cluster Detection Configuration', 
    description: 'YAML configuration for detecting and clustering related news events',
    category: 'AI Prompts',
    type: 'string',
    multiline: true,
    isYaml: true,
    defaultValue: `name: News Event Clustering
description: Detect and cluster related news articles into events
stages:
  - name: cluster_analysis
    type: final
    prompt: |
      Analyze the following news articles and determine if they should be clustered together:
      
      Articles: {articles}
      
      Consider:
      - Similar topics or events
      - Time proximity
      - Geographic relevance
      - Key entities mentioned
      
      Provide clustering recommendations with confidence scores.
    llm_params:
      temperature: 0.2
      max_tokens: 800`
  },
  {
    key: 'prompt_daily_summary_system',
    displayName: 'Daily Summary Configuration',
    description: 'YAML configuration for generating daily news summaries',
    category: 'AI Prompts',
    type: 'string',
    multiline: true,
    isYaml: true,
    defaultValue: `name: Daily News Summary
description: Generate comprehensive daily summary from selected articles
stages:
  - name: daily_summary
    type: final
    prompt: |
      Create a comprehensive daily news summary from the following articles:
      
      {articles}
      
      Structure:
      - Top Stories (3-5 most important)
      - Key Developments by category
      - Notable mentions
      - Overall sentiment and trends
      
      Keep it informative yet digestible, around 300-500 words.
    llm_params:
      temperature: 0.4
      max_tokens: 1500`
  },
  {
    key: 'prompt_cover_image_generation',
    displayName: 'Cover Image Configuration',
    description: 'YAML configuration for generating cover image descriptions',
    category: 'AI Prompts',
    type: 'string',
    multiline: true,
    isYaml: true,
    defaultValue: `name: Cover Image Generation
description: Generate compelling cover image descriptions for news summaries
stages:
  - name: image_description
    type: final
    prompt: |
      Create a compelling cover image description for this news summary:
      
      Summary: {summary}
      Key Topics: {topics}
      
      Requirements:
      - Visual, descriptive language
      - Appropriate for news content
      - Professional and engaging
      - Suitable for AI image generation
      
      Provide a clear, detailed description in 1-2 sentences.
    llm_params:
      temperature: 0.7
      max_tokens: 200`
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
    key: 'max_article_age_days',
    displayName: 'Maximum Article Age (days)',
    description: 'Skip processing RSS items older than this many days (1-30 days)',
    category: 'Processing',
    type: 'integer',
    minValue: 1,
    maxValue: 30,
    defaultValue: '7'
  },
  {
    key: 'topic_similarity_threshold',
    displayName: 'Topic Matching Threshold',
    description: 'Similarity threshold for matching articles to topics (0.1-1.0)',
    category: 'Processing',
    type: 'float',
    minValue: 0.1,
    maxValue: 1.0,
    defaultValue: '0.62'
  },
  {
    key: 'cluster_threshold',
    displayName: 'Article Clustering Threshold',
    description: 'Similarity threshold for clustering articles into events (0.1-1.0)',
    category: 'Processing',
    type: 'float',
    minValue: 0.1,
    maxValue: 1.0,
    defaultValue: '0.75'
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
  },
  {
    key: 'batch_processing_size',
    displayName: 'Batch Processing Size',
    description: 'Number of articles to process in a single batch (5-100)',
    category: 'Processing',
    type: 'integer',
    minValue: 5,
    maxValue: 100,
    defaultValue: '20'
  },
  {
    key: 'batch_processing_enabled',
    displayName: 'Enable Batch Processing',
    description: 'Process multiple articles simultaneously for better performance',
    category: 'Processing',
    type: 'boolean',
    defaultValue: 'true'
  }
];

export default function SettingsPage() {
  const { user } = useAuth();

  // Define tab configuration first
  const settingTabs = [
    { id: 'api-models', label: 'API & Models', icon: '🤖', category: 'API & Models Configuration' },
    { id: 'ai-features', label: 'AI Features', icon: '⚡', category: 'AI Features' },
    { id: 'prompts', label: 'AI Prompts', icon: '💬', category: 'AI Prompts' },
    { id: 'storage', label: 'Storage', icon: '💾', category: 'Storage' },
    { id: 'processing', label: 'Processing', icon: '⚙️', category: 'Processing' }
  ];

  // User tab configuration
  const userTabs = [
    { id: 'preferences', label: 'Preferences', icon: '⚙️' },
    { id: 'topics', label: 'Topics', icon: '📚' },
    { id: 'rss-feeds', label: 'RSS Sources', icon: '📡' }
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
  const [yamlValidationErrors, setYamlValidationErrors] = useState<{[key: string]: string[]}>({});
  const [originalSystemSettings, setOriginalSystemSettings] = useState<SystemSettingItem[]>([]);
  const [activeTab, setActiveTab] = useState<string>('api-models');
  const [activeUserTab, setActiveUserTab] = useState<string>('preferences');
  const [dailySummaryEnabled, setDailySummaryEnabled] = useState(false); // Default to false for security
  const [expandedPrompts, setExpandedPrompts] = useState<{[key: string]: boolean}>({});

  useEffect(() => {
    fetchData();
    fetchUserSettings();
    if (user?.is_admin) {
      fetchSystemSettings();
    }
    checkDailySummarySettings();
  }, [user?.is_admin]);

  const checkDailySummarySettings = async () => {
    if (user && !user.is_admin) {
      try {
        const settings = await apiClient.get<Array<{setting_key: string; setting_value: string}>>(API_ENDPOINTS.PUBLIC.SETTINGS);
        const enabled = settings.find(s => s.setting_key === 'daily_summary_enabled')?.setting_value === 'true';
        setDailySummaryEnabled(enabled);
      } catch (error) {
        console.warn('Could not fetch daily summary settings:', error);
        // Keep default value of false for security
        setDailySummaryEnabled(false);
      }
    }
    // For admin users, the setting will be checked in the useEffect when systemSettings loads
  };

  // Check daily summary settings when system settings are loaded (for admin users)
  useEffect(() => {
    if (user?.is_admin && systemSettings.length > 0) {
      const setting = systemSettings.find(s => s.setting_key === 'daily_summary_enabled');
      if (setting) {
        setDailySummaryEnabled(setting.setting_value === 'true');
      }
    }
  }, [user?.is_admin, systemSettings]);

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
      setOriginalSystemSettings(JSON.parse(JSON.stringify(response))); // Deep copy
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
      // Update original settings to reflect saved state
      setOriginalSystemSettings(JSON.parse(JSON.stringify(systemSettings)));
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

  // Check if settings have changes
  const hasChanges = () => {
    if (systemSettings.length !== originalSystemSettings.length) return true;

    return systemSettings.some(setting => {
      const original = originalSystemSettings.find(orig => orig.setting_key === setting.setting_key);
      return !original || original.setting_value !== setting.setting_value;
    });
  };

  // Get list of changed setting keys
  const getChangedSettings = (): string[] => {
    const changed: string[] = [];

    systemSettings.forEach(setting => {
      const original = originalSystemSettings.find(orig => orig.setting_key === setting.setting_key);
      if (!original) {
        changed.push(setting.setting_key); // New setting
      } else if (original.setting_value !== setting.setting_value) {
        changed.push(setting.setting_key); // Modified setting
      }
    });

    return changed;
  };

  // Check if a specific setting has changed
  const isSettingChanged = (key: string): boolean => {
    const current = systemSettings.find(s => s.setting_key === key);
    const original = originalSystemSettings.find(s => s.setting_key === key);

    if (!current && !original) return false;
    if (!current || !original) return true;

    return current.setting_value !== original.setting_value;
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

  // Helper function to get setting value
  const getSettingValue = (key: string): string => {
    const setting = systemSettings.find(s => s.setting_key === key);
    return setting?.setting_value || '';
  };

  // Helper function to check if a setting should use YAML editor
  const isYamlSetting = (definition: StaticSettingDefinition): boolean => {
    return definition.isYaml === true;
  };

  // Helper function to toggle prompt accordion
  const togglePromptExpanded = (promptKey: string) => {
    setExpandedPrompts(prev => ({
      ...prev,
      [promptKey]: !prev[promptKey]
    }));
  };

  // Function to validate YAML syntax
  const validateYamlSyntax = (yamlContent: string, settingKey: string) => {
    if (!yamlContent || yamlContent.trim() === '') {
      setYamlValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[settingKey];
        return newErrors;
      });
      return;
    }

    try {
      // Basic YAML structure validation
      const errors: string[] = [];

      // Check for basic YAML structure indicators
      if (!yamlContent.includes('name:') && !yamlContent.includes('description:') && !yamlContent.includes('stages:')) {
        errors.push('YAML should contain basic structure with name, description, and stages');
      }

      // Check for basic YAML syntax issues
      let bracketCount = 0;
      let inString = false;
      let stringChar = '';

      for (let i = 0; i < yamlContent.length; i++) {
        const char = yamlContent[i];
        
        if (!inString && (char === '"' || char === "'")) {
          inString = true;
          stringChar = char;
        } else if (inString && char === stringChar && yamlContent[i-1] !== '\\') {
          inString = false;
          stringChar = '';
        } else if (!inString) {
          if (char === '[' || char === '{') bracketCount++;
          if (char === ']' || char === '}') bracketCount--;
        }
      }

      if (bracketCount !== 0) {
        errors.push('Unmatched brackets or braces');
      }

      // Set validation errors
      setYamlValidationErrors(prev => ({
        ...prev,
        [settingKey]: errors
      }));

      // Call backend validation if no basic syntax errors
      if (errors.length === 0) {
        validateYamlOnServer(yamlContent, settingKey);
      }

    } catch (error) {
      setYamlValidationErrors(prev => ({
        ...prev,
        [settingKey]: [`Syntax error: ${error instanceof Error ? error.message : 'Unknown error'}`]
      }));
    }
  };

  // Function to validate YAML on server
  const validateYamlOnServer = async (yamlContent: string, settingKey: string) => {
    try {
      const response = await apiClient.post('/api/admin/validate-chain-yaml', yamlContent, {
        headers: {
          'Content-Type': 'text/plain'
        }
      });

      if (response.data.valid) {
        setYamlValidationErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors[settingKey];
          return newErrors;
        });
      } else {
        setYamlValidationErrors(prev => ({
          ...prev,
          [settingKey]: response.data.errors || ['Validation failed']
        }));
      }
    } catch (error) {
      console.error('Server YAML validation failed:', error);
      // Don't show server errors in UI for now, keep client-side validation
    }
  };

  // Function to handle file content loading into editor
  const handleFileContentLoad = (content: string, fileName: string, promptKey: string) => {
    // Update the setting value in the local state
    updateSettingValue(promptKey, content);
    
    // Show success message
    console.log(`Loaded content from ${fileName} into ${promptKey}`);
  };

  // Get static definitions for use in component
  const staticDefinitions = createStaticSettingDefinitions();

  // Get current tab info
  const currentTab = settingTabs.find(tab => tab.id === activeTab) || settingTabs[0];
  const currentUserTab = userTabs.find(tab => tab.id === activeUserTab) || userTabs[0];

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
    const isChanged = isSettingChanged(definition.key);
    const baseClasses = `w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 ${isChanged
        ? 'border-amber-400 bg-amber-50 focus:ring-amber-500'
        : 'border-gray-300 focus:ring-blue-500'
      }`;
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

        // Use YAML editor for YAML settings, regular textarea for others
        if (definition.multiline || definition.key.includes('prompt')) {
          const isYaml = isYamlSetting(definition);
          const hasValidationErrors = yamlValidationErrors[definition.key]?.length > 0;
          
          if (isYaml) {
            return (
              <div>
                <YamlEditor
                  value={value}
                  onChange={(newValue) => {
                    updateSettingValue(definition.key, newValue);
                    
                    // Debounce validation to avoid too many API calls
                    clearTimeout((window as any)[`yamlTimeout_${definition.key}`]);
                    (window as any)[`yamlTimeout_${definition.key}`] = setTimeout(() => {
                      validateYamlSyntax(newValue, definition.key);
                    }, 1000);
                  }}
                  height="400px"
                  placeholder={definition.defaultValue || `Enter YAML configuration:\nname: Example Chain\ndescription: Description here\nstages:\n  - name: stage1\n    type: final\n    prompt: "Your prompt here"`}
                  className={hasValidationErrors ? 'border-red-500' : ''}
                />
                
                {/* YAML validation feedback */}
                <div className="mt-2">
                  {hasValidationErrors ? (
                    <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
                      <div className="font-medium">YAML Validation Errors:</div>
                      <ul className="mt-1 list-disc list-inside">
                        {yamlValidationErrors[definition.key]?.map((error, index) => (
                          <li key={index}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  ) : value && value.trim() ? (
                    <div className="text-sm text-green-600 bg-green-50 border border-green-200 rounded p-2">
                      ✓ YAML syntax appears valid
                    </div>
                  ) : null}
                  
                  {/* YAML help text */}
                  <div className="text-xs text-gray-500 mt-2">
                    <details className="cursor-pointer">
                      <summary className="font-medium">YAML Chain Configuration Help</summary>
                      <div className="mt-2 p-2 bg-gray-50 rounded">
                        <p className="mb-2">Required structure:</p>
                        <pre className="text-xs bg-white p-2 rounded border">{`name: Chain Name
description: Chain description
stages:
  - name: stage1
    type: question|final|transform|conditional
    prompt: "Your prompt template"
    llm_params:  # optional LLM control parameters
      temperature: 0.7      # 0.0-2.0, controls randomness
      max_tokens: 1000      # max output tokens
      top_p: 0.9           # 0.0-1.0, nucleus sampling
      frequency_penalty: 0  # -2.0-2.0, reduce repetition
      presence_penalty: 0   # -2.0-2.0, encourage new topics
    options: ["option1", "option2"]  # for question type
    next_stages:  # optional branching
      option1: next_stage_name`}</pre>
                      </div>
                    </details>
                  </div>
                </div>
              </div>
            );
          }
          
          // Regular textarea for non-YAML multiline settings
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
      'api-models': 'Configure API providers, credentials, and model settings for all AI services',
      'ai-features': 'Enable or disable AI-powered features like daily summaries and cover images',
      'prompts': 'Customize AI prompts used for content generation and analysis',
      'storage': 'Configure S3 storage settings for images and file uploads',
      'processing': 'Adjust processing intervals, thresholds, and system performance parameters'
    };
    return descriptions[tabId as keyof typeof descriptions] || 'Configure system settings';
  };

  // Get description for user tabs
  const getUserTabDescription = (tabId: string): string => {
    const descriptions = {
      'preferences': 'Customize your personal preferences and daily summary settings',
      'topics': 'Manage your news topics and keywords for personalized content',
      'rss-feeds': 'Configure your personal RSS feed sources and subscriptions'
    };
    return descriptions[tabId as keyof typeof descriptions] || 'Manage your settings';
  };

  // Render user tab content
  const renderUserTabContent = () => {
    switch (activeUserTab) {
      case 'preferences':
        return (
          <div className="space-y-6">
            {dailySummaryEnabled ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Daily Summary Prompt
                </label>
                <textarea
                  value={userSettings.daily_summary_prompt}
                  onChange={(e) => setUserSettings({ ...userSettings, daily_summary_prompt: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={4}
                  placeholder="Enter your custom prompt for daily news summaries (optional)"
                />
                <p className="text-xs text-gray-500 mt-2">
                  This prompt will be used to customize your daily news summaries. Leave empty to use the default prompt.
                </p>
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
                <p className="text-gray-600 text-sm">
                  Daily Summary feature is currently disabled. Contact your administrator to enable this feature.
                </p>
              </div>
            )}
          </div>
        );

      case 'topics':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="text-lg font-medium text-gray-900">Your Topics</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Manage topics to personalize your news feed
                </p>
              </div>
              <button
                onClick={() => openTopicModal()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Add Topic
              </button>
            </div>

            <div className="space-y-3">
              {topics.length > 0 ? (
                topics.map((topic) => (
                  <div key={topic.id} className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h5 className="font-medium text-gray-900">{topic.name}</h5>
                          <span className={`px-2 py-1 text-xs rounded-full ${topic.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
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
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">📚</div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">No Topics Yet</h4>
                  <p className="text-gray-600 mb-4">Create your first topic to start personalizing your news feed</p>
                  <button
                    onClick={() => openTopicModal()}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                  >
                    Add Your First Topic
                  </button>
                </div>
              )}
            </div>
          </div>
        );

      case 'rss-feeds':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="text-lg font-medium text-gray-900">RSS Sources</h4>
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

            <div className="space-y-3">
              {rssFeeds.length > 0 ? (
                rssFeeds.map((feed) => (
                  <div key={feed.id} className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h5 className="font-medium text-gray-900">{feed.title || 'Untitled Feed'}</h5>
                        <p className="text-sm text-gray-600 mt-1">{feed.url}</p>
                        <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                          <span>Interval: {feed.fetch_interval_minutes}min</span>
                          <span className={`px-2 py-1 rounded-full ${feed.last_fetch_status === 'success' ? 'bg-green-100 text-green-800' :
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
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">📡</div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">No RSS Feeds</h4>
                  <p className="text-gray-600 mb-4">Add RSS feeds to get news from your favorite sources</p>
                  <button
                    onClick={() => openRSSModal()}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                  >
                    Add Your First RSS Feed
                  </button>
                </div>
              )}
            </div>
          </div>
        );

      default:
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⚙️</div>
            <h4 className="text-lg font-medium text-gray-900 mb-2">Settings</h4>
            <p className="text-gray-600">Select a category from the sidebar to manage your settings.</p>
          </div>
        );
    }
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



      {/* User Settings (Non-Admin Users) */}
      {!user?.is_admin && (
        <div className="border border-gray-200 rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">User Settings</h2>
            <p className="text-sm text-gray-600 mt-1">
              Customize your preferences and manage your content sources
            </p>
          </div>

          {/* Tab Layout */}
          <div className="flex">
            {/* Left Sidebar - Tab Navigation */}
            <div className="w-64 border-r border-gray-200 bg-gray-50 flex flex-col min-h-[600px]">
              <nav className="p-4 space-y-1 flex-1 overflow-y-auto">
                {userTabs.map((tab) => {
                  const isActive = activeUserTab === tab.id;

                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveUserTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2 text-left rounded-md transition-colors ${isActive
                          ? 'bg-blue-100 text-blue-900 border-l-4 border-blue-500'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                        }`}
                    >
                      <span className="text-lg">{tab.icon}</span>
                      <div className="flex-1 flex items-center justify-between">
                        <span className="text-sm font-medium">{tab.label}</span>
                      </div>
                    </button>
                  );
                })}

                {/* Save Button in Sidebar - at bottom */}
                <div className="p-4 border-t border-gray-200">
                  <button
                    onClick={updateUserSettings}
                    disabled={isSavingUser}
                    className="w-full px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium shadow-sm"
                  >
                    {isSavingUser ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Saving...
                      </>
                    ) : (
                      'Save Settings'
                    )}
                  </button>
                </div>
              </nav>
            </div>

            {/* Right Content Area */}
            <div className="flex-1 min-h-[600px] overflow-y-auto">
              <div className="p-6">
                {currentUserTab ? (
                  <>
                    {/* Tab Header */}
                    <div className="mb-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                            <span className="text-2xl">{currentUserTab.icon}</span>
                            {currentUserTab.label}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            {getUserTabDescription(currentUserTab.id)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Tab Content */}
                    <div className="space-y-6">
                      {renderUserTabContent()}
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
          <div className="flex">
            {/* Left Sidebar - Tab Navigation */}
            <div className="w-64 border-r border-gray-200 bg-gray-50 flex flex-col min-h-[600px]">
              <nav className="p-4 space-y-1 flex-1 overflow-y-auto">
                {settingTabs.map((tab) => {
                  const isActive = activeTab === tab.id;
                  // Check if this tab has any modified settings
                  const tabSettings = staticDefinitions.filter(def => def.category === tab.category);
                  const hasTabChanges = tabSettings.some(def => isSettingChanged(def.key));

                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2 text-left rounded-md transition-colors ${isActive
                          ? 'bg-blue-100 text-blue-900 border-l-4 border-blue-500'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                        }`}
                    >
                      <span className="text-lg">{tab.icon}</span>
                      <div className="flex-1 flex items-center justify-between">
                        <span className="text-sm font-medium">{tab.label}</span>
                        {hasTabChanges && (
                          <span className="w-2 h-2 bg-amber-400 rounded-full flex-shrink-0" title="This tab has modified settings"></span>
                        )}
                      </div>
                    </button>
                  );
                })}

                {/* Save Button in Sidebar - at bottom */}
                <div className="p-4 border-t border-gray-200">
                  <button
                    onClick={updateSystemSettings}
                    disabled={isSavingSystem || !hasChanges()}
                    className="w-full px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium shadow-sm"
                  >
                    {isSavingSystem ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Saving...
                      </>
                    ) : hasChanges() ? (
                      <>
                        Save Settings ({getChangedSettings().length})
                      </>
                    ) : (
                      'No Changes'
                    )}
                  </button>
                </div>
              </nav>
            </div>

            {/* Right Content Area */}
            <div className="flex-1 min-h-[600px] overflow-y-auto">
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
                          {(() => {
                            const changedInTab = getCurrentTabSettings().filter(item => isSettingChanged(item.definition.key));
                            return changedInTab.length > 0 ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                                {changedInTab.length} modified
                              </span>
                            ) : null;
                          })()}
                        </div>
                      </div>
                    </div>

                    {/* Tab Content */}
                    <div className="space-y-6">
                      {(() => {
                        const tabSettings = getCurrentTabSettings();

                        // Special handling for AI Prompts tab - use accordion display
                        if (currentTab.id === 'prompts') {
                          // Group prompt settings by prompt type
                          const promptGroups: Record<string, typeof tabSettings> = {};
                          
                          tabSettings.forEach(item => {
                            const key = item.definition.key;
                            let promptType = '';
                            
                            if (key.startsWith('prompt_summary_creation')) {
                              promptType = 'summary_creation';
                            } else if (key.startsWith('prompt_cluster_detection')) {
                              promptType = 'cluster_detection';
                            } else if (key.startsWith('prompt_daily_summary_system')) {
                              promptType = 'daily_summary_system';
                            } else if (key.startsWith('prompt_cover_image_generation')) {
                              promptType = 'cover_image_generation';
                            }
                            
                            if (promptType) {
                              if (!promptGroups[promptType]) {
                                promptGroups[promptType] = [];
                              }
                              promptGroups[promptType].push(item);
                            }
                          });
                          
                          const promptTypeInfo = {
                            summary_creation: { title: 'Article Summary', icon: '📝', description: 'Prompt for generating article summaries' },
                            cluster_detection: { title: 'Cluster Detection', icon: '🔍', description: 'Prompt for detecting related news events' },
                            daily_summary_system: { title: 'Daily Summary', icon: '📅', description: 'Prompt for generating daily summaries' },
                            cover_image_generation: { title: 'Cover Image', icon: '🖼️', description: 'Prompt for cover image descriptions' }
                          };
                          
                          return Object.entries(promptGroups).map(([promptType, groupItems]) => {
                            const info = promptTypeInfo[promptType as keyof typeof promptTypeInfo];
                            const isExpanded = expandedPrompts[promptType] || false;
                            const hasChanges = groupItems.some(item => isSettingChanged(item.definition.key));
                            
                            // Filter visible items
                            const visibleItems = groupItems.filter(item => isSettingVisible(item.definition));
                            
                            return (
                              <div key={promptType} className="border border-gray-200 rounded-lg overflow-hidden">
                                {/* Accordion Header */}
                                <button
                                  onClick={() => togglePromptExpanded(promptType)}
                                  className={`w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50 transition-colors ${
                                    hasChanges ? 'bg-amber-50 border-l-4 border-l-amber-400' : ''
                                  }`}
                                >
                                  <div className="flex items-center gap-3">
                                    <span className="text-xl">{info.icon}</span>
                                    <div>
                                      <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                                        {info.title}
                                        {hasChanges && (
                                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                                            Modified
                                          </span>
                                        )}
                                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                          YAML
                                        </span>
                                      </h4>
                                      <p className="text-sm text-gray-600 mt-1">{info.description}</p>
                                    </div>
                                  </div>
                                  {isExpanded ? (
                                    <ChevronDown className="w-5 h-5 text-gray-400" />
                                  ) : (
                                    <ChevronRight className="w-5 h-5 text-gray-400" />
                                  )}
                                </button>
                                
                                {/* Accordion Content */}
                                {isExpanded && (
                                  <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
                                    <div className="space-y-4">
                                      {/* Configuration Editor */}
                                      {visibleItems.map(({ definition, setting }) => {                                      
                                        return (
                                          <div key={definition.key} className="bg-white p-4 rounded-lg border border-gray-200">
                                            <div className="flex items-center justify-between mb-2">
                                              <label className="block text-sm font-medium text-gray-700">
                                                <div className="flex items-center gap-2">
                                                  {definition.displayName}
                                                  {isSettingChanged(definition.key) && (
                                                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-amber-200 text-amber-800">
                                                      ✏️ Modified
                                                    </span>
                                                  )}
                                                  {definition.isYaml && (
                                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                                      YAML Configuration
                                                    </span>
                                                  )}
                                                </div>
                                              </label>
                                              
                                              {/* File Selector for YAML settings */}
                                              {definition.isYaml && (
                                                <FileSelector
                                                  onFileSelect={(content, fileName) => 
                                                    handleFileContentLoad(content, fileName, definition.key)
                                                  }
                                                  acceptedTypes={['.yaml', '.yml', '.txt']}
                                                  className="flex-shrink-0"
                                                />
                                              )}
                                            </div>
                                            
                                            {renderSettingInput(definition, setting)}
                                            
                                            {definition.description && (
                                              <p className="text-xs text-gray-500 mt-2">
                                                {definition.description}
                                              </p>
                                            )}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          });
                        }
                        
                        // Default handling for other tabs - use existing group logic
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
                                      <div className="flex items-center gap-2">
                                        {definition.displayName}
                                        {isSettingChanged(definition.key) && (
                                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-amber-200 text-amber-800">
                                            ✏️ Modified
                                          </span>
                                        )}
                                        {definition.isEncrypted && (
                                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                                            🔒 Encrypted
                                          </span>
                                        )}
                                      </div>
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
          <div className={`mx-auto flex items-center justify-center h-12 w-12 rounded-full mb-4 ${feedbackModal.type === 'success' ? 'bg-green-100' : 'bg-red-100'
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
            className={`px-4 py-2 rounded text-white transition-colors ${feedbackModal.type === 'success'
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
