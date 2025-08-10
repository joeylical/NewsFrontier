'use client';

import React from 'react';
import { formatRelativeTime } from '@/lib/utils';

interface TimelineItem {
  id: string | number;
  title: string;
  description?: string;
  timestamp: string;
  status?: 'active' | 'completed' | 'pending';
  icon?: React.ReactNode;
}

interface TimelineProps {
  items: TimelineItem[];
  onItemClick?: (item: TimelineItem) => void;
  className?: string;
}

export default function Timeline({ items, onItemClick, className = '' }: TimelineProps) {
  const getStatusClasses = (status?: string) => {
    switch (status) {
      case 'completed':
        return 'timeline-start timeline-box bg-success text-success-content';
      case 'active':
        return 'timeline-start timeline-box bg-primary text-primary-content';
      case 'pending':
      default:
        return 'timeline-start timeline-box bg-base-200';
    }
  };

  return (
    <div className={`timeline timeline-vertical ${className}`}>
      {items.map((item, index) => (
        <li key={item.id}>
          {index > 0 && <hr />}
          <div className="timeline-middle">
            <div className="timeline-item-icon">
              {item.icon || (
                <div 
                  className={`w-3 h-3 rounded-full ${
                    item.status === 'completed' ? 'bg-success' :
                    item.status === 'active' ? 'bg-primary' : 'bg-base-300'
                  }`}
                />
              )}
            </div>
          </div>
          <div 
            className={getStatusClasses(item.status) + (onItemClick ? ' cursor-pointer hover:shadow-md transition-shadow' : '')}
            onClick={onItemClick ? () => onItemClick(item) : undefined}
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h4 className="font-semibold">{item.title}</h4>
                {item.description && (
                  <p className="text-sm opacity-70 mt-1">{item.description}</p>
                )}
              </div>
              <time className="text-xs opacity-60">
                {formatRelativeTime(item.timestamp)}
              </time>
            </div>
          </div>
          {index < items.length - 1 && <hr />}
        </li>
      ))}
    </div>
  );
}