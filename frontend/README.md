# personalized-ai-storybook Frontend - Next.js

A modern, responsive frontend for the personalized-ai-storybook application built with **Next.js 14** and **React 18**.

## 🚀 Features

- **Next.js App Router**: Modern routing with server-side rendering
- **TypeScript**: Full type safety throughout the application
- **Theme Support**: Beautiful light and dark themes with smooth transitions
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Interactive Story Generation**: Real-time story creation with AI
- **Page Navigation**: Smooth story reading experience
- **Loading States**: Engaging loading animations and feedback

## 🛠️ Technology Stack

- **Next.js 14.2**: React framework with App Router
- **React 18.2**: UI library with concurrent features
- **TypeScript 5.0**: Type-safe development
- **CSS3**: Custom styling with CSS variables
- **ESLint**: Code quality and consistency

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx         # Root layout with metadata
│   │   └── page.tsx           # Main page component
│   ├── components/            # Reusable components
│   │   └── ClientThemeProvider.tsx
│   ├── pages/                 # Page components
│   │   ├── Home/
│   │   │   └── LandingPage.tsx
│   │   └── Story/
│   │       ├── StoryInput.tsx
│   │       └── StoryDisplay.tsx
│   ├── layout/                # Layout components
│   │   ├── Navigation.tsx
│   │   └── Footer.tsx
│   ├── shared/components/     # Shared UI components
│   │   ├── LoadingExperience.tsx
│   │   ├── ThemeToggle.tsx
│   │   └── ContactSection.tsx
│   ├── contexts/              # React contexts
│   │   └── ThemeContext.tsx
│   ├── hooks/                 # Custom React hooks
│   │   └── useLoadingMessages.ts
│   ├── styles/                # Global styles
│   │   └── globals.css
│   ├── types/                 # TypeScript type definitions
│   │   └── theme.ts
│   └── utils/                 # Utility functions
│       └── constants.ts
├── public/                    # Static assets
├── next.config.js            # Next.js configuration
├── tsconfig.json             # TypeScript configuration
├── package.json              # Dependencies and scripts
└── start_frontend.bat        # Development startup script
```

## 🚀 Getting Started

### Prerequisites

- **Node.js 18+**: Required for Next.js 14
- **npm**: Package manager (comes with Node.js)

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   # or use the batch file
   .\start_frontend.bat
   ```

4. **Open your browser:**
   Visit [http://localhost:3000](http://localhost:3000)

## 📜 Available Scripts

### Development

```bash
npm run dev          # Start development server
```

- Runs on `http://localhost:3000`
- Hot reload enabled
- TypeScript checking
- ESLint integration

### Production

```bash
npm run build        # Build for production
npm run start        # Start production server
```

- Optimized bundle
- Static generation where possible
- Image optimization
- Code splitting

### Code Quality

```bash
npm run lint         # Run ESLint
```

- TypeScript checking
- Code style enforcement
- Next.js specific rules

## 🎨 Theme System

The application features a sophisticated theme system with:

### Light Theme
- Clean, modern design
- High contrast for readability
- Professional color palette
- Optimized for productivity

### Dark Theme
- Magical, storybook-inspired colors
- Purple and gold accents
- Reduced eye strain
- Perfect for storytelling

### Theme Features
- **Automatic Detection**: Respects system preferences
- **Persistent Storage**: Remembers user choice
- **Smooth Transitions**: CSS transitions between themes
- **CSS Variables**: Dynamic theming with CSS custom properties

## 🧩 Component Architecture

### App Router Structure
- **Server Components**: Default for better performance
- **Client Components**: Marked with `'use client'` directive
- **Layout System**: Nested layouts with shared UI
- **Metadata API**: SEO optimization

### Key Components

#### Layout Components
- **Navigation**: Responsive navigation with theme toggle
- **Footer**: Comprehensive footer with links and info

#### Page Components
- **LandingPage**: Hero section with features and CTA
- **StoryInput**: Story generation interface
- **StoryDisplay**: Interactive story reader

#### Shared Components
- **LoadingExperience**: Animated loading states
- **ThemeToggle**: Theme switching button
- **ContactSection**: Contact form and information

## 🔧 Configuration

### Next.js Configuration (`next.config.js`)

```javascript
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};
```

**Features:**
- API proxy to backend
- React Strict Mode
- SWC minification
- Optimized builds

### TypeScript Configuration (`tsconfig.json`)

- **Strict Mode**: Full type checking
- **Path Mapping**: `@/` alias for clean imports
- **Next.js Integration**: Optimized for Next.js
- **Modern Target**: ES5 with modern features

## 🎯 Development Guidelines

### Client vs Server Components

**Use Server Components (default) for:**
- Static content
- Data fetching
- SEO optimization
- Performance-critical components

**Use Client Components (`'use client'`) for:**
- Interactive features
- React hooks (`useState`, `useEffect`)
- Browser APIs (`localStorage`, `window`)
- Event handlers

### Import Patterns

```typescript
// Use path aliases for clean imports
import { ThemeProvider } from '@/contexts/ThemeContext';
import { Navigation } from '@/layout';
import { StoryInput } from '@/pages/Story';
```

### Styling Approach

- **CSS Modules**: Component-scoped styles
- **Global CSS**: Shared styles and variables
- **CSS Variables**: Dynamic theming
- **Responsive Design**: Mobile-first approach

## 🚀 Performance Features

### Next.js Optimizations
- **Automatic Code Splitting**: Smaller bundle sizes
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Automatic font loading
- **Static Generation**: Pre-rendered pages where possible

### React 18 Features
- **Concurrent Rendering**: Better user experience
- **Automatic Batching**: Optimized re-renders
- **Suspense**: Better loading states

## 🔍 Troubleshooting

### Common Issues

**1. Client Component Errors**
```bash
Error: You're importing a component that needs createContext
```
**Solution**: Add `'use client'` directive to components using hooks

**2. Import Path Errors**
```bash
Module not found: Can't resolve '@/components/...'
```
**Solution**: Check `tsconfig.json` path mapping configuration

**3. Build Errors**
```bash
Type error: Property 'theme' does not exist
```
**Solution**: Ensure TypeScript types are properly defined

### Development Tips

1. **Hot Reload**: Changes reflect immediately
2. **TypeScript**: Fix type errors before building
3. **ESLint**: Follow code style guidelines
4. **Console**: Check browser console for runtime errors

## 📱 Browser Support

- **Modern Browsers**: Chrome, Firefox, Safari, Edge
- **Mobile**: iOS Safari, Chrome Mobile
- **Features**: ES6+, CSS Grid, Flexbox
- **Fallbacks**: Graceful degradation for older browsers

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

**Output:**
- Optimized JavaScript bundles
- Static assets
- Server-side rendered pages
- Image optimizations

### Deployment Options

- **Vercel**: Recommended (Next.js creators)
- **Netlify**: Static site hosting
- **AWS**: Full-stack deployment
- **Docker**: Containerized deployment

## 📚 Learn More

### Next.js Resources
- [Next.js Documentation](https://nextjs.org/docs)
- [App Router Guide](https://nextjs.org/docs/app)
- [Performance Best Practices](https://nextjs.org/docs/advanced-features/performance)

### React Resources
- [React Documentation](https://react.dev/)
- [React 18 Features](https://react.dev/blog/2022/03/29/react-v18)
- [Hooks Reference](https://react.dev/reference/react)

### TypeScript Resources
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React TypeScript](https://react-typescript-cheatsheet.netlify.app/)

## 🤝 Contributing

1. Follow TypeScript best practices
2. Use meaningful component names
3. Add proper type definitions
4. Test components thoroughly
5. Follow Next.js conventions

## 📄 License

This project is part of the personalized-ai-storybook Final Year Project.

---

**Built with ❤️ using Next.js, React, and TypeScript**