'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Theme, ThemeConfig } from '../types/theme';

// Beautiful Light Theme
const lightTheme: ThemeConfig = {
  colors: {
    // Primary colors - Beautiful blue gradient
    primary: '#3B82F6',
    primaryDark: '#1D4ED8',
    primaryLight: '#60A5FA',
    accent: '#F59E0B',
    
    // Background colors - Clean whites and grays
    background: '#FFFFFF',
    backgroundSecondary: '#F8FAFC',
    backgroundTertiary: '#F1F5F9',
    
    // Text colors - Dark grays for readability
    textPrimary: '#1E293B',
    textSecondary: '#475569',
    textTertiary: '#64748B',
    
    // Surface colors - Subtle grays
    surface: '#FFFFFF',
    surfaceSecondary: '#F8FAFC',
    surfaceTertiary: '#F1F5F9',
    
    // Border colors
    border: '#E2E8F0',
    borderSecondary: '#CBD5E1',
    
    // Status colors
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
    
    // Shadow colors
    shadow: 'rgba(0, 0, 0, 0.1)',
    shadowLight: 'rgba(0, 0, 0, 0.05)',
    
    // Gradient colors
    gradientPrimary: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)',
    gradientSecondary: 'linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%)',
    gradientAccent: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
  },
  fonts: {
    primary: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    secondary: "'Playfair Display', Georgia, serif",
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem',
  },
  borderRadius: {
    sm: '0.375rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  },
};

// Magical Story Dark Theme - A Canvas of Beautiful Colors
const darkTheme: ThemeConfig = {
  colors: {
    // Primary colors - Magical purple with rainbow accents
    primary: '#8B5CF6', // Vibrant purple
    primaryDark: '#7C3AED', // Deep purple
    primaryLight: '#A78BFA', // Light purple
    accent: '#F59E0B', // Golden accent
    
    // Background colors - Deep magical night sky
    background: '#0A0A0F', // Deep space blue-black
    backgroundSecondary: '#1A1A2E', // Rich dark blue
    backgroundTertiary: '#16213E', // Mystical dark blue
    
    // Text colors - Soft magical light
    textPrimary: '#E2E8F0', // Soft white
    textSecondary: '#CBD5E1', // Light gray
    textTertiary: '#94A3B8', // Medium gray
    
    // Surface colors - Magical surfaces with subtle colors
    surface: '#1A1A2E', // Rich dark blue
    surfaceSecondary: '#16213E', // Mystical dark blue
    surfaceTertiary: '#0F3460', // Deep ocean blue
    
    // Border colors - Subtle magical borders
    border: '#2D3748', // Soft dark gray
    borderSecondary: '#4A5568', // Medium gray
    
    // Status colors - Vibrant magical colors
    success: '#10B981', // Emerald green
    warning: '#F59E0B', // Golden yellow
    error: '#EF4444', // Ruby red
    info: '#3B82F6', // Sky blue
    
    // Shadow colors - Magical shadows
    shadow: 'rgba(0, 0, 0, 0.4)',
    shadowLight: 'rgba(0, 0, 0, 0.2)',
    
    // Gradient colors - Magical rainbow gradients
    gradientPrimary: 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 50%, #F59E0B 100%)', // Purple to pink to gold
    gradientSecondary: 'linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%)', // Deep blues
    gradientAccent: 'linear-gradient(135deg, #F59E0B 0%, #EC4899 50%, #8B5CF6 100%)', // Gold to pink to purple
  },
  fonts: {
    primary: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    secondary: "'Playfair Display', Georgia, serif",
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem',
  },
  borderRadius: {
    sm: '0.375rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.3)',
  },
};

interface ThemeContextType {
  theme: Theme;
  themeConfig: ThemeConfig;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>('light'); // Default for SSR
  const [mounted, setMounted] = useState(false);

  // Handle hydration
  useEffect(() => {
    setMounted(true);
    
    // Get theme from localStorage or system preference
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme) {
      setTheme(savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark');
    }
  }, []);

  const themeConfig = theme === 'light' ? lightTheme : darkTheme;

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    
    // Only access localStorage on client side
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', newTheme);
    }
  };

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    // Apply theme to document root
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update CSS custom properties
    const root = document.documentElement;
    Object.entries(themeConfig.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });
    
    Object.entries(themeConfig.fonts).forEach(([key, value]) => {
      root.style.setProperty(`--font-${key}`, value);
    });
    
    Object.entries(themeConfig.spacing).forEach(([key, value]) => {
      root.style.setProperty(`--spacing-${key}`, value);
    });
    
    Object.entries(themeConfig.borderRadius).forEach(([key, value]) => {
      root.style.setProperty(`--radius-${key}`, value);
    });
    
    Object.entries(themeConfig.shadows).forEach(([key, value]) => {
      root.style.setProperty(`--shadow-${key}`, value);
    });
  }, [theme, themeConfig]);

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return (
      <ThemeContext.Provider value={{ theme: 'light', themeConfig: lightTheme, toggleTheme }}>
        {children}
      </ThemeContext.Provider>
    );
  }

  return (
    <ThemeContext.Provider value={{ theme, themeConfig, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
