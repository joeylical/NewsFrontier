'use client';

import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import LoadingSpinner from '@/components/LoadingSpinner';
import DebugModal from '@/components/DebugModal';
import { Menu } from 'lucide-react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout, isLoading } = useAuth();
  const router = useRouter();
  const [isDebugModalOpen, setIsDebugModalOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-gray-200 bg-gray-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex-shrink-0">
              <Link 
                href={user?.is_admin ? "/dashboard/settings" : "/dashboard"} 
                className="text-xl font-semibold text-gray-900 hover:text-gray-700"
              >
                NewsFrontier
              </Link>
            </div>
            
            {/* Navigation Links */}
            <div className="hidden md:flex space-x-8">
              {user?.is_admin ? (
                // Admin users only see System Settings
                <Link href="/dashboard/settings" className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                  System Settings
                </Link>
              ) : (
                // Regular users see normal dashboard
                <>
                  <Link href="/dashboard" className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                    HOME
                  </Link>
                  <Link href="/dashboard/topics" className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                    Topics
                  </Link>
                  <Link href="/dashboard/articles" className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                    Articles
                  </Link>
                </>
              )}
            </div>
            
            {/* User Menu */}
            <div className="relative">
              <div className="flex items-center space-x-4">
                {/* Debug Button - Only in development */}
                {process.env.NODE_ENV === 'development' && (
                  <button
                    onClick={() => setIsDebugModalOpen(true)}
                    className="px-3 py-1 text-xs font-medium text-orange-600 border border-orange-300 rounded hover:bg-orange-50 transition-colors"
                    title="Development Debug Tools"
                  >
                    Debug
                  </button>
                )}
                <span className="text-sm text-gray-700">{user?.username}</span>
                <div className="relative group">
                  <button className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-medium">
                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                  </button>
                  <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                    <div className="py-2">
                      {!user?.is_admin && (
                        <Link href="/dashboard/settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                          Settings
                        </Link>
                      )}
                      <button 
                        onClick={handleLogout}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        Logout
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button className="text-gray-700 hover:text-gray-900">
                <Menu className="h-6 w-6" />
              </button>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Main Content */}
      <main className="pt-8">
        {children}
      </main>

      {/* Debug Modal */}
      <DebugModal 
        isOpen={isDebugModalOpen}
        onClose={() => setIsDebugModalOpen(false)}
        onDataRefresh={() => {
          // Trigger a page refresh to reload dashboard data
          window.location.reload();
        }}
      />
    </div>
  );
}
