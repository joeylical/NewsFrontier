import React from 'react';
import { formatRelativeTime, getProcessingStatusBadgeClass } from '@/lib/utils';

interface ListItemProps {
  title: string;
  subtitle?: string;
  timestamp?: string;
  status?: string;
  count?: number;
  onClick?: () => void;
  className?: string;
  children?: React.ReactNode;
}

export default function ListItem({
  title,
  subtitle,
  timestamp,
  status,
  count,
  onClick,
  className = '',
  children,
}: ListItemProps) {
  return (
    <div 
      className={`card bg-base-100 shadow-sm border border-base-300 hover:shadow-md transition-shadow ${
        onClick ? 'cursor-pointer hover:bg-base-200' : ''
      } ${className}`}
      onClick={onClick}
    >
      <div className="card-body p-4">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="card-title text-base font-semibold">{title}</h3>
            {subtitle && (
              <p className="text-sm text-base-content/70 mt-1">{subtitle}</p>
            )}
          </div>
          <div className="flex flex-col items-end gap-2">
            {count !== undefined && (
              <div className="badge badge-neutral badge-sm">{count}</div>
            )}
            {status && (
              <div className={`badge badge-sm ${getProcessingStatusBadgeClass(status)}`}>
                {status}
              </div>
            )}
          </div>
        </div>
        
        {children && (
          <div className="mt-3">
            {children}
          </div>
        )}
        
        {timestamp && (
          <div className="text-xs text-base-content/50 mt-2">
            {formatRelativeTime(timestamp)}
          </div>
        )}
      </div>
    </div>
  );
}