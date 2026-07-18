'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import ThemeToggle from '@/shared/components/ThemeToggle';
import './Navigation.css';

interface NavigationProps {
  onReset: () => void;
  showReset: boolean;
  onGoHome?: () => void;
  onShowLogin?: () => void;
  onShowRegister?: () => void;
}

const Navigation: React.FC<NavigationProps> = ({ onReset, showReset = false, onGoHome, onShowLogin, onShowRegister }) => {
  const [isScrolled, setIsScrolled] = useState<boolean>(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState<boolean>(false);
  const { theme } = useTheme();
  const { isAuthenticated, user, logout } = useAuth();

  useEffect(() => {
    const handleScroll = (): void => {
      setIsScrolled(window.scrollY > 50);
    };

    const handleClickOutside = (event: MouseEvent): void => {
      const target = event.target as HTMLElement;
      if (!target.closest('.nav-user-menu-container')) {
        setIsUserMenuOpen(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    document.addEventListener('mousedown', handleClickOutside);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const scrollToSection = (sectionId: string): void => {
    if (sectionId === 'home' && onGoHome) {
      // If we're not on the landing page, use onGoHome to navigate back
      onGoHome();
    } else {
      // Otherwise, scroll to the section
      const element = document.getElementById(sectionId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
    setIsMobileMenuOpen(false);
  };

  return (
    <nav className={`navigation ${isScrolled ? 'scrolled' : ''} ${theme}`}>
      <div className="nav-container">
        {/* Logo */}
        <div className="nav-logo" onClick={() => scrollToSection('home')}>
          <div className="logo-icon">📖</div>
          <span className="logo-text">MyAIStorybook</span>
        </div>

        {/* Desktop Menu */}
        <div className="nav-menu">
          <button 
            className="nav-link" 
            onClick={() => scrollToSection('home')}
          >
            Home
          </button>
          <button 
            className="nav-link" 
            onClick={() => scrollToSection('features')}
          >
            Features
          </button>
          <button 
            className="nav-link" 
            onClick={() => scrollToSection('about')}
          >
            About
          </button>
          <button 
            className="nav-link" 
            onClick={() => scrollToSection('contact')}
          >
            Contact
          </button>
          {!isAuthenticated ? (
            <>
              <button 
                className="nav-link nav-button" 
                onClick={onShowLogin}
              >
                Login
              </button>
              <button 
                className="nav-link nav-button-primary" 
                onClick={onShowRegister}
              >
                Sign Up
              </button>
            </>
          ) : (
            <div className="nav-user">
              <div className="nav-user-menu-container">
                <div 
                  className="nav-avatar" 
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  title="Click to view profile"
                >
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </div>
                {isUserMenuOpen && (
                  <div className="nav-user-dropdown">
                    <div className="nav-user-dropdown-item">
                      <span className="nav-user-dropdown-label">Email:</span>
                      <span className="nav-user-dropdown-value">{user?.email}</span>
                    </div>
                    <div className="nav-user-dropdown-item">
                      <span className="nav-user-dropdown-label">Username:</span>
                      <span className="nav-user-dropdown-value">{user?.username}</span>
                    </div>
                    <div className="nav-user-dropdown-divider"></div>
                    <button 
                      className="nav-user-dropdown-button" 
                      onClick={() => {
                        logout();
                        setIsUserMenuOpen(false);
                      }}
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
          <ThemeToggle />
          {showReset && (
            <button 
              className="nav-link reset-link" 
              onClick={onReset}
            >
              New Story
            </button>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button 
          className="mobile-menu-button"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle mobile menu"
        >
          <span className={`hamburger ${isMobileMenuOpen ? 'open' : ''}`}>
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>
      </div>

      {/* Mobile Menu */}
      <div className={`mobile-menu ${isMobileMenuOpen ? 'open' : ''}`}>
        <button 
          className="mobile-nav-link" 
          onClick={() => scrollToSection('home')}
        >
          Home
        </button>
        <button 
          className="mobile-nav-link" 
          onClick={() => scrollToSection('features')}
        >
          Features
        </button>
        <button 
          className="mobile-nav-link" 
          onClick={() => scrollToSection('about')}
        >
          About
        </button>
        <button 
          className="mobile-nav-link" 
          onClick={() => scrollToSection('contact')}
        >
          Contact
        </button>
        {!isAuthenticated ? (
          <>
            <button 
              className="mobile-nav-link" 
              onClick={() => { onShowLogin?.(); setIsMobileMenuOpen(false); }}
            >
              Login
            </button>
            <button 
              className="mobile-nav-link" 
              onClick={() => { onShowRegister?.(); setIsMobileMenuOpen(false); }}
            >
              Sign Up
            </button>
          </>
        ) : (
          <>
            <div className="mobile-nav-user">
              <div className="mobile-nav-avatar" title={user?.username}>
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <span className="mobile-nav-username">{user?.username}</span>
            </div>
            <button 
              className="mobile-nav-link" 
              onClick={() => { logout(); setIsMobileMenuOpen(false); }}
            >
              Logout
            </button>
          </>
        )}
        <div className="mobile-theme-toggle">
          <ThemeToggle />
        </div>
        {showReset && (
          <button 
            className="mobile-nav-link reset-link" 
            onClick={onReset}
          >
            New Story
          </button>
        )}
      </div>
    </nav>
  );
};

export default Navigation;
