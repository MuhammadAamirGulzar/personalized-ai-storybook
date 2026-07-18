// Application constants

// ── API Base URL ─────────────────────────────────────────────────────────────
// In production (Vercel), set NEXT_PUBLIC_API_URL to your Render backend URL.
// Example: https://myaistorybook-backend.onrender.com
// In local development, it defaults to http://localhost:8000
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const LOADING_MESSAGES: string[] = [
  "Awakening the Storyteller...",
  "Gathering stardust and moonbeams...",
  "Dreaming up characters and quests...",
  "Painting scenes with vibrant colors...",
  "The final chapter is being written...",
];

export const API_ENDPOINTS = {
  GENERATE: `${API_BASE_URL}/api/generate`,
  DEVICE: `${API_BASE_URL}/device`,
  GENERATED: `${API_BASE_URL}/generated`,
  AUTH_LOGIN: `${API_BASE_URL}/api/auth/login`,
  AUTH_REGISTER: `${API_BASE_URL}/api/auth/register`,
  AUTH_ME: `${API_BASE_URL}/api/auth/me`
} as const;

export const APP_CONFIG = {
  NAME: 'MyAIStorybook',
  DESCRIPTION: 'Create magical illustrated children\'s stories with AI',
  VERSION: '1.0.0'
} as const;
