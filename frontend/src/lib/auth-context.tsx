'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, AuthResponse } from './types';
import { apiClient } from './api-client';
import { API_ENDPOINTS, STORAGE_KEYS } from './constants';

// Cookie helper functions
const getCookie = (name: string): string | null => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
  return null;
};

const setCookie = (name: string, value: string, days: number = 7) => {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Strict`;
};

const deleteCookie = (name: string) => {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
};

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (username: string, password: string, email?: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const savedToken = getCookie(STORAGE_KEYS.AUTH_TOKEN);
      const savedUser = getCookie(STORAGE_KEYS.USER_DATA);
      
      if (savedToken) {
        try {
          apiClient.setAuthToken(savedToken);
          
          if (savedUser) {
            const userData = JSON.parse(savedUser);
            setToken(savedToken);
            setUser(userData);
            
            // Optionally verify token is still valid by fetching fresh user data
            try {
              const freshUserData = await apiClient.get<User>(API_ENDPOINTS.AUTH.USER_INFO);
              if (JSON.stringify(freshUserData) !== JSON.stringify(userData)) {
                setUser(freshUserData);
                setCookie(STORAGE_KEYS.USER_DATA, JSON.stringify(freshUserData));
              }
            } catch (error) {
              console.warn('Failed to refresh user data, using cached data:', error);
            }
          } else {
            // Token exists but no user data, fetch from backend
            try {
              const userData = await apiClient.get<User>(API_ENDPOINTS.AUTH.USER_INFO);
              setToken(savedToken);
              setUser(userData);
              setCookie(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
            } catch (error) {
              console.error('Failed to fetch user data with saved token:', error);
              deleteCookie(STORAGE_KEYS.AUTH_TOKEN);
              apiClient.setAuthToken(null);
            }
          }
        } catch (error) {
          console.error('Failed to initialize auth:', error);
          deleteCookie(STORAGE_KEYS.AUTH_TOKEN);
          deleteCookie(STORAGE_KEYS.USER_DATA);
          apiClient.setAuthToken(null);
        }
      }
      
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await apiClient.post<AuthResponse>(API_ENDPOINTS.AUTH.LOGIN, {
        username,
        password,
      });
      
      setToken(response.token);
      apiClient.setAuthToken(response.token);
      setCookie(STORAGE_KEYS.AUTH_TOKEN, response.token);
      
      // Fetch user data from backend if not included in login response
      let userData: User;
      if (response.user) {
        userData = response.user;
      } else {
        // Fetch user info from backend
        userData = await apiClient.get<User>(API_ENDPOINTS.AUTH.USER_INFO);
      }
      
      setUser(userData);
      setCookie(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      setUser(null);
      setToken(null);
      apiClient.setAuthToken(null);
      deleteCookie(STORAGE_KEYS.AUTH_TOKEN);
      deleteCookie(STORAGE_KEYS.USER_DATA);
    }
  };

  const register = async (username: string, password: string, email?: string) => {
    try {
      await apiClient.post(API_ENDPOINTS.AUTH.REGISTER, {
        username,
        password,
        email,
      });
      
      // Automatically log in after successful registration
      await login(username, password);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const value = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    login,
    logout,
    register,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}