'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import Modal from './Modal';
import { Check, X, Edit, Trash2, Plus, ChevronDown, ChevronRight } from 'lucide-react';

interface LLMModel {
  id: number;
  name: string;
  model_type: 'chat' | 'embedding' | 'image' | 'audio' | 'transcript';
  provider: string;
  model_name: string;
  api_base_url?: string;
  is_active: boolean;
  config_json?: string;
  description?: string;
  has_api_key: boolean;
  created_at: string;
  updated_at: string;
}

interface LLMModelFormData {
  name: string;
  model_type: 'chat' | 'embedding' | 'image' | 'audio' | 'transcript';
  provider: string;
  model_name: string;
  api_key?: string;
  api_base_url?: string;
  is_active: boolean;
  config_json?: string;
  description?: string;
}

interface LLMModelManagerProps {
  onModelChange?: () => void;
}

const modelTypeInfo = {
  chat: { icon: '💬', label: 'Chat/Text Generation', color: 'blue' },
  embedding: { icon: '🔢', label: 'Text Embeddings', color: 'green' },
  image: { icon: '🖼️', label: 'Image Generation', color: 'purple' },
  audio: { icon: '🎵', label: 'Audio Processing', color: 'orange' },
  transcript: { icon: '📝', label: 'Speech-to-Text', color: 'red' },
};

export default function LLMModelManager({ onModelChange }: LLMModelManagerProps) {
  const [models, setModels] = useState<LLMModel[]>([]);
  const [providers, setProviders] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<LLMModel | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  
  // Expandable groups
  const [expandedTypes, setExpandedTypes] = useState<Record<string, boolean>>({});

  // Form data
  const [formData, setFormData] = useState<LLMModelFormData>({
    name: '',
    model_type: 'chat',
    provider: '',
    model_name: '',
    api_key: '',
    api_base_url: '',
    is_active: true,
    config_json: '',
    description: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [modelsResponse, providersResponse] = await Promise.all([
        apiClient.get<LLMModel[]>('/api/admin/llm-models'),
        apiClient.get<{ providers: string[] }>('/api/admin/llm-providers')
      ]);
      
      setModels(modelsResponse);
      setProviders(providersResponse.providers || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load LLM models');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTypeExpanded = (modelType: string) => {
    setExpandedTypes(prev => ({
      ...prev,
      [modelType]: !prev[modelType]
    }));
  };

  const openModal = (model?: LLMModel) => {
    if (model) {
      setEditingModel(model);
      setFormData({
        name: model.name,
        model_type: model.model_type,
        provider: model.provider,
        model_name: model.model_name,
        api_key: '', // Don't show existing encrypted key
        api_base_url: model.api_base_url || '',
        is_active: model.is_active,
        config_json: model.config_json || '',
        description: model.description || ''
      });
    } else {
      setEditingModel(null);
      setFormData({
        name: '',
        model_type: 'chat',
        provider: '',
        model_name: '',
        api_key: '',
        api_base_url: '',
        is_active: true,
        config_json: '',
        description: ''
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingModel(null);
    setFormData({
      name: '',
      model_type: 'chat',
      provider: '',
      model_name: '',
      api_key: '',
      api_base_url: '',
      is_active: true,
      config_json: '',
      description: ''
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);

    try {
      if (editingModel) {
        await apiClient.put(`/api/admin/llm-models/${editingModel.id}`, formData);
      } else {
        await apiClient.post('/api/admin/llm-models', formData);
      }
      
      await fetchData();
      closeModal();
      onModelChange?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save model');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (model: LLMModel) => {
    if (!confirm(`Are you sure you want to delete the model "${model.name}"?`)) {
      return;
    }

    try {
      await apiClient.delete(`/api/admin/llm-models/${model.id}`);
      await fetchData();
      onModelChange?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete model');
    }
  };

  // Group models by type
  const modelsByType = models.reduce((acc, model) => {
    if (!acc[model.model_type]) {
      acc[model.model_type] = [];
    }
    acc[model.model_type].push(model);
    return acc;
  }, {} as Record<string, LLMModel[]>);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
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

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">LLM Model Configuration</h3>
          <p className="text-sm text-gray-600 mt-1">
            Manage multiple LLM models for different AI tasks. Each model can have its own provider, API key, and configuration.
          </p>
        </div>
        <button
          onClick={() => openModal()}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Model
        </button>
      </div>

      {/* Model Groups by Type */}
      <div className="space-y-4">
        {Object.entries(modelTypeInfo).map(([modelType, typeInfo]) => {
          const typeModels = modelsByType[modelType] || [];
          const isExpanded = expandedTypes[modelType] !== false; // Default to expanded

          return (
            <div key={modelType} className="border border-gray-200 rounded-lg">
              {/* Type Header */}
              <button
                onClick={() => toggleTypeExpanded(modelType)}
                className="w-full px-4 py-3 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">{typeInfo.icon}</span>
                  <div>
                    <h4 className="font-medium text-gray-900 flex items-center gap-2">
                      {typeInfo.label}
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-${typeInfo.color}-100 text-${typeInfo.color}-800`}>
                        {typeModels.length} models
                      </span>
                    </h4>
                    <p className="text-sm text-gray-600">
                      {typeModels.length === 0 
                        ? 'No models configured for this type' 
                        : `${typeModels.filter(m => m.is_active).length} active`
                      }
                    </p>
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                )}
              </button>

              {/* Type Content */}
              {isExpanded && (
                <div className="border-t border-gray-200 p-4">
                  {typeModels.length > 0 ? (
                    <div className="space-y-3">
                      {typeModels.map((model) => (
                        <div
                          key={model.id}
                          className={`p-4 rounded-lg border ${
                            model.is_active ? 'border-gray-200 bg-white' : 'border-gray-100 bg-gray-50'
                          }`}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <h5 className="font-medium text-gray-900">{model.name}</h5>
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  model.is_active 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-gray-100 text-gray-600'
                                }`}>
                                  {model.is_active ? 'Active' : 'Inactive'}
                                </span>
                              </div>
                              
                              <div className="text-sm text-gray-600 space-y-1">
                                <div><span className="font-medium">Provider:</span> {model.provider}</div>
                                <div><span className="font-medium">Model:</span> {model.model_name}</div>
                                {model.api_base_url && (
                                  <div><span className="font-medium">API URL:</span> {model.api_base_url}</div>
                                )}
                                {model.description && (
                                  <div><span className="font-medium">Description:</span> {model.description}</div>
                                )}
                                <div className="flex items-center gap-4 text-xs">
                                  <span className={`flex items-center gap-1 ${model.has_api_key ? 'text-green-600' : 'text-red-600'}`}>
                                    {model.has_api_key ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                                    {model.has_api_key ? 'API Key Set' : 'No API Key'}
                                  </span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex gap-2 ml-4">
                              <button
                                onClick={() => openModal(model)}
                                className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                                title="Edit model"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(model)}
                                className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                                title="Delete model"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <div className="text-4xl mb-2">{typeInfo.icon}</div>
                      <p>No {typeInfo.label.toLowerCase()} models configured</p>
                      <button
                        onClick={() => {
                          setFormData(prev => ({ ...prev, model_type: modelType as any }));
                          openModal();
                        }}
                        className="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        Add your first {typeInfo.label.toLowerCase()} model
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {models.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <div className="text-4xl mb-4">🤖</div>
          <h4 className="text-lg font-medium text-gray-900 mb-2">No LLM Models Configured</h4>
          <p className="text-gray-600 mb-4">
            Add your first LLM model to start using AI features. You need at least a chat model and an embedding model.
          </p>
          <button
            onClick={() => openModal()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Add Your First Model
          </button>
        </div>
      )}

      {/* Model Configuration Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingModel ? 'Edit LLM Model' : 'Add New LLM Model'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Model Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Model Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                pattern="^[a-zA-Z][a-zA-Z0-9_]*$"
                placeholder="e.g., default_chat, claude_sonnet"
                title="Must start with a letter and contain only letters, numbers, and underscores"
              />
              <p className="text-xs text-gray-500 mt-1">
                Used in YAML configurations (letters, numbers, underscores only)
              </p>
            </div>

            {/* Model Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Model Type <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.model_type}
                onChange={(e) => setFormData({ ...formData, model_type: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {Object.entries(modelTypeInfo).map(([type, info]) => (
                  <option key={type} value={type}>
                    {info.icon} {info.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Provider */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Provider <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.provider}
                onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Select Provider</option>
                {providers.map(provider => (
                  <option key={provider} value={provider}>{provider}</option>
                ))}
              </select>
            </div>

            {/* Model Name from Provider */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Provider Model <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.model_name}
                onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                placeholder="e.g., gpt-4, claude-3-sonnet-20240229"
              />
            </div>
          </div>

          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Key {editingModel && <span className="text-sm text-gray-500">(leave empty to keep existing)</span>}
            </label>
            <input
              type="password"
              value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={editingModel ? 'Enter new key to replace existing' : 'Enter API key'}
            />
          </div>

          {/* API Base URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Base URL <span className="text-sm text-gray-500">(optional)</span>
            </label>
            <input
              type="url"
              value={formData.api_base_url}
              onChange={(e) => setFormData({ ...formData, api_base_url: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Custom endpoint URL (leave empty for provider default)"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description <span className="text-sm text-gray-500">(optional)</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={2}
              placeholder="Brief description of this model's purpose"
            />
          </div>

          {/* Options */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
            />
            <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
              Active
            </label>
          </div>

          {/* Advanced Configuration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Advanced Config <span className="text-sm text-gray-500">(JSON format, optional)</span>
            </label>
            <textarea
              value={formData.config_json}
              onChange={(e) => setFormData({ ...formData, config_json: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder='{"temperature": 0.7, "max_tokens": 1000}'
            />
          </div>

          {/* Modal Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={closeModal}
              className="px-4 py-2 border border-gray-300 rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  {editingModel ? 'Updating...' : 'Creating...'}
                </>
              ) : (
                <>
                  {editingModel ? 'Update Model' : 'Create Model'}
                </>
              )}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}