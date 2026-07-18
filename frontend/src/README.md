# Frontend Structure

This document outlines the professional folder structure for the personalized-ai-storybook frontend.

## 📁 Directory Structure

```
src/
├── assets/                 # Static assets (images, icons, etc.)
├── hooks/                  # Custom React hooks
│   └── useLoadingMessages.js
├── layout/                 # Layout components (Navigation, Footer)
│   ├── Navigation.js
│   ├── Navigation.css
│   ├── Footer.js
│   ├── Footer.css
│   └── index.js
├── pages/                  # Page components
│   ├── Home/               # Home/Landing page
│   │   ├── LandingPage.js
│   │   ├── LandingPage.css
│   │   └── index.js
│   └── Story/              # Story-related pages
│       ├── StoryInput.js
│       ├── StoryInput.css
│       ├── StoryDisplay.js
│       ├── StoryDisplay.css
│       └── index.js
├── shared/                 # Shared/reusable components
│   └── components/
│       ├── ContactSection.js
│       ├── ContactSection.css
│       ├── LoadingExperience.js
│       ├── LoadingExperience.css
│       └── index.js
├── styles/                 # Global styles
│   └── globals.css
├── utils/                  # Utility functions and constants
│   └── constants.js
├── App.js                  # Main application component
└── index.js               # Application entry point
```

## 🎯 Organization Principles

### 1. **Feature-Based Organization**
- Components are organized by feature/domain (Home, Story, Layout)
- Related files (JS, CSS) are kept together
- Each feature has its own directory with an index.js for clean imports

### 2. **Separation of Concerns**
- **Layout**: Navigation, Footer, and other layout components
- **Pages**: Main page components (Home, Story creation/display)
- **Shared**: Reusable components used across multiple pages
- **Hooks**: Custom React hooks for shared logic
- **Utils**: Constants, helper functions, and utilities
- **Styles**: Global styles and CSS variables

### 3. **Clean Imports**
- Each directory has an `index.js` file for clean imports
- Import paths are shorter and more maintainable
- Easy to refactor and move components

## 📦 Import Examples

```javascript
// Layout components
import { Navigation, Footer } from './layout';

// Page components
import { LandingPage } from './pages/Home';
import { StoryInput, StoryDisplay } from './pages/Story';

// Shared components
import { ContactSection, LoadingExperience } from './shared/components';

// Utilities
import { API_ENDPOINTS, LOADING_MESSAGES } from './utils/constants';

// Custom hooks
import { useLoadingMessages } from './hooks/useLoadingMessages';
```

## 🚀 Benefits

1. **Scalability**: Easy to add new features and components
2. **Maintainability**: Clear separation of concerns
3. **Reusability**: Shared components are easily accessible
4. **Developer Experience**: Clean imports and logical organization
5. **Team Collaboration**: Clear structure for multiple developers
6. **Performance**: Better code splitting opportunities

## 🔄 Migration Notes

- All components have been moved from `components/` to their appropriate locations
- Import paths have been updated throughout the application
- CSS files have been moved alongside their corresponding JS files
- Global styles moved to `styles/globals.css`
- Constants extracted to `utils/constants.js`
- Custom hooks created for shared logic

This structure follows React best practices and makes the codebase more professional and maintainable.
