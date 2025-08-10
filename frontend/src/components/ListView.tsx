'use client';

import React from 'react';
import LoadingSpinner from './LoadingSpinner';
import ErrorBoundary from './ErrorBoundary';

interface ListViewProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  isLoading?: boolean;
  error?: string;
  emptyMessage?: string;
  title?: string;
  actions?: React.ReactNode;
  className?: string;
}

export default function ListView<T>({
  items,
  renderItem,
  isLoading = false,
  error,
  emptyMessage = 'No items found',
  title,
  actions,
  className = '',
}: ListViewProps<T>) {
  if (isLoading) {
    return (
      <div className={`min-h-[200px] ${className}`}>
        <LoadingSpinner size="lg" className="h-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`alert alert-error ${className}`}>
        <div>
          <h3 className="font-bold">Error loading data</h3>
          <div className="text-sm">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className={`space-y-4 ${className}`}>
        {title && (
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">{title}</h2>
            {actions && <div className="flex gap-2">{actions}</div>}
          </div>
        )}
        
        {items.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-base-content/60">
              <svg 
                className="w-16 h-16 mx-auto mb-4 text-base-content/30" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={1.5} 
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
                />
              </svg>
              <p className="text-lg font-medium">{emptyMessage}</p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((item, index) => (
              <div key={index}>{renderItem(item, index)}</div>
            ))}
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}