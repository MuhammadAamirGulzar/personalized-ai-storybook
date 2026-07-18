// Theme types
export type Theme = 'light' | 'dark';

export interface ThemeColors {
  // Primary colors
  primary: string;
  primaryDark: string;
  primaryLight: string;
  accent: string;
  
  // Background colors
  background: string;
  backgroundSecondary: string;
  backgroundTertiary: string;
  
  // Text colors
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  
  // Surface colors
  surface: string;
  surfaceSecondary: string;
  surfaceTertiary: string;
  
  // Border colors
  border: string;
  borderSecondary: string;
  
  // Status colors
  success: string;
  warning: string;
  error: string;
  info: string;
  
  // Shadow colors
  shadow: string;
  shadowLight: string;
  
  // Gradient colors
  gradientPrimary: string;
  gradientSecondary: string;
  gradientAccent: string;
}

export interface ThemeConfig {
  colors: ThemeColors;
  fonts: {
    primary: string;
    secondary: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
}
