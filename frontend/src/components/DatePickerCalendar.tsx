'use client';

import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';
import { AvailableDatesData } from '@/lib/types';
import { formatDate } from '@/lib/utils';

interface DatePickerCalendarProps {
  selectedDate: string;
  onDateSelect: (date: string) => void;
  onClose: () => void;
}

export default function DatePickerCalendar({ selectedDate, onDateSelect, onClose }: DatePickerCalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(() => {
    const date = new Date(selectedDate);
    return { year: date.getFullYear(), month: date.getMonth() + 1 };
  });
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const calendarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchAvailableDates = async () => {
      setIsLoading(true);
      try {
        const data = await apiClient.get<AvailableDatesData>(
          API_ENDPOINTS.DASHBOARD.AVAILABLE_DATES(currentMonth.year, currentMonth.month)
        );
        setAvailableDates(data.available_dates);
      } catch (error) {
        console.error('Failed to fetch available dates:', error);
        setAvailableDates([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAvailableDates();
  }, [currentMonth]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (calendarRef.current && !calendarRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const getDaysInMonth = (year: number, month: number) => {
    return new Date(year, month, 0).getDate();
  };

  const getFirstDayOfMonth = (year: number, month: number) => {
    return new Date(year, month - 1, 1).getDay();
  };

  const handlePrevMonth = () => {
    setCurrentMonth(prev => {
      if (prev.month === 1) {
        return { year: prev.year - 1, month: 12 };
      }
      return { year: prev.year, month: prev.month - 1 };
    });
  };

  const handleNextMonth = () => {
    setCurrentMonth(prev => {
      if (prev.month === 12) {
        return { year: prev.year + 1, month: 1 };
      }
      return { year: prev.year, month: prev.month + 1 };
    });
  };

  const handleDateClick = (day: number) => {
    const dateStr = `${currentMonth.year}-${String(currentMonth.month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    onDateSelect(dateStr);
    onClose();
  };

  const handleTodayClick = () => {
    const today = new Date().toISOString().split('T')[0];
    onDateSelect(today);
    onClose();
  };

  const renderCalendarDays = () => {
    const daysInMonth = getDaysInMonth(currentMonth.year, currentMonth.month);
    const firstDay = getFirstDayOfMonth(currentMonth.year, currentMonth.month);
    const days = [];

    // Empty cells for days before first day of month
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="w-8 h-8"></div>);
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${currentMonth.year}-${String(currentMonth.month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isSelected = dateStr === selectedDate;
      const isAvailable = availableDates.includes(dateStr);
      const isToday = dateStr === new Date().toISOString().split('T')[0];

      days.push(
        <button
          key={day}
          onClick={() => handleDateClick(day)}
          className={`w-8 h-8 text-sm rounded-md transition-colors relative ${
            isSelected
              ? 'bg-blue-600 text-white'
              : isAvailable
              ? 'bg-green-100 text-green-800 hover:bg-green-200'
              : 'text-gray-400 hover:bg-gray-100'
          } ${isToday ? 'ring-2 ring-blue-300' : ''}`}
          title={isAvailable ? `Summary available for ${formatDate(dateStr)}` : `No summary for ${formatDate(dateStr)}`}
        >
          {day}
          {isAvailable && (
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-green-500 rounded-full"></div>
          )}
        </button>
      );
    }

    return days;
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div ref={calendarRef} className="bg-white rounded-lg shadow-lg p-6 max-w-sm w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={handlePrevMonth}
            className="p-1 hover:bg-gray-100 rounded-md transition-colors"
            title="Previous month"
          >
            ←
          </button>
          <h3 className="text-lg font-semibold">
            {monthNames[currentMonth.month - 1]} {currentMonth.year}
          </h3>
          <button
            onClick={handleNextMonth}
            className="p-1 hover:bg-gray-100 rounded-md transition-colors"
            title="Next month"
          >
            →
          </button>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="text-center py-4">
            <div className="inline-block w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm text-gray-500 mt-2">Loading available dates...</p>
          </div>
        )}

        {/* Calendar grid */}
        {!isLoading && (
          <>
            {/* Day names */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
                <div key={day} className="w-8 h-8 text-xs font-medium text-gray-500 flex items-center justify-center">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar days */}
            <div className="grid grid-cols-7 gap-1">
              {renderCalendarDays()}
            </div>
          </>
        )}

        {/* Legend */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-green-100 rounded border border-green-200"></div>
                <span>Available</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-gray-100 rounded border border-gray-200"></div>
                <span>No data</span>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={handleTodayClick}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Go to Today
          </button>
          <button
            onClick={onClose}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}