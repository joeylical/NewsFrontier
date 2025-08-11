'use client';

import React, { useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { X, Loader2 } from 'lucide-react';

interface DebugModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDataRefresh?: () => void;
}

interface DebugActionResponse {
  success: boolean;
  message: string;
  details?: string;
}

export default function DebugModal({ isOpen, onClose, onDataRefresh }: DebugModalProps) {
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const debugActions = [
    {
      id: 'regenerate-summary',
      title: 'Regenerate Daily Summary',
      description: 'Clear existing summary and generate a fresh one based on today\'s articles',
      icon: '📄',
      endpoint: '/api/debug/regenerate-daily-summary'
    },
    {
      id: 'fetch-rss',
      title: 'Refresh RSS Feeds',
      description: 'Manually trigger RSS feed collection from all configured sources',
      icon: '📡',
      endpoint: '/api/debug/fetch-rss'
    },
    {
      id: 'process-articles',
      title: 'Process Pending Articles',
      description: 'Run AI analysis on unprocessed articles (summaries, clustering, etc.)',
      icon: '⚙️',
      endpoint: '/api/debug/process-articles'
    }
  ];

  const handleAction = async (action: typeof debugActions[0]) => {
    setIsLoading(action.id);
    setStatus(null);

    try {
      const response = await apiClient.post<DebugActionResponse>(action.endpoint, {});
      
      setStatus({
        type: 'success',
        message: response.message || `${action.title} completed successfully!`
      });

      // Refresh data after a short delay for summary regeneration
      if (action.id === 'regenerate-summary' && onDataRefresh) {
        setTimeout(() => {
          onDataRefresh();
        }, 2000);
      }
      
    } catch (error) {
      setStatus({
        type: 'error',
        message: error instanceof Error ? error.message : `Failed to ${action.title.toLowerCase()}`
      });
    } finally {
      setIsLoading(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Debug Tools</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <p className="text-sm text-gray-600 mb-6">
            Development utilities for testing system functionality
          </p>

          {/* Debug Actions */}
          <div className="space-y-3">
            {debugActions.map((action) => (
              <div key={action.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <span className="text-2xl">{action.icon}</span>
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{action.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{action.description}</p>
                    <button
                      onClick={() => handleAction(action)}
                      disabled={isLoading !== null}
                      className={`mt-3 px-4 py-2 rounded text-sm font-medium transition-colors ${
                        isLoading === action.id
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800'
                      }`}
                    >
                      {isLoading === action.id ? (
                        <span className="flex items-center">
                          <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
                          Processing...
                        </span>
                      ) : (
                        'Execute'
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Status Display */}
          {status && (
            <div className={`p-3 rounded text-sm ${
              status.type === 'success' 
                ? 'bg-green-100 text-green-800 border border-green-200' 
                : 'bg-red-100 text-red-800 border border-red-200'
            }`}>
              {status.message}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
          <p className="text-xs text-gray-500">
            <strong>Note:</strong> These tools are for development and testing purposes only.
          </p>
        </div>
      </div>
    </div>
  );
}