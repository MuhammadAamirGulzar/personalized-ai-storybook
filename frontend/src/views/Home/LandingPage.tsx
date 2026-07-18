import React from 'react';
import { ContactSection } from '@/shared/components';
import './LandingPage.css';

interface LandingPageProps {
  onStartCreating: () => void;
  onOpenWorkshop: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onStartCreating, onOpenWorkshop }) => {
  const scrollToSection = (sectionId: string): void => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section id="home" className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <div className="hero-text">
              <h1 className="hero-title">
                Create Magical Stories with
                <span className="hero-highlight"> AI Magic</span>
              </h1>
              <p className="hero-description">
                Transform your ideas into beautiful, illustrated children's stories in minutes.
                Our AI-powered platform creates engaging narratives with stunning visuals,
                perfect for bedtime stories, educational content, or creative inspiration.
              </p>
              <div className="hero-buttons">
                <button
                  className="hero-button primary"
                  onClick={onStartCreating}
                >
                  Start Creating Stories
                  <svg className="button-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z" />
                  </svg>
                </button>
                <button
                  className="hero-button secondary"
                  onClick={onOpenWorkshop}
                >
                  Throw Your Ideas ✨
                </button>
              </div>
              <div className="hero-stats">
                <div className="stat">
                  <span className="stat-number">1000+</span>
                  <span className="stat-label">Stories Created</span>
                </div>
                <div className="stat">
                  <span className="stat-number">5 min</span>
                  <span className="stat-label">Average Time</span>
                </div>
                <div className="stat">
                  <span className="stat-number">99%</span>
                  <span className="stat-label">Satisfaction</span>
                </div>
              </div>
            </div>
            <div className="hero-visual">
              <div className="floating-cards">
                <div className="story-card card-1">
                  <div className="card-image">🦄</div>
                  <div className="card-title">The Magic Unicorn</div>
                </div>
                <div className="story-card card-2">
                  <div className="card-image">🚀</div>
                  <div className="card-title">Space Adventure</div>
                </div>
                <div className="story-card card-3">
                  <div className="card-image">🐱</div>
                  <div className="card-title">Cat's Journey</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="features-container">
          <div className="section-header">
            <h2 className="section-title">Powerful Features</h2>
            <p className="section-description">
              Everything you need to create amazing stories with AI assistance
            </p>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3 className="feature-title">AI Story Generation</h3>
              <p className="feature-description">
                Advanced AI creates engaging, age-appropriate stories from your simple ideas and prompts.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎨</div>
              <h3 className="feature-title">Automatic Illustrations</h3>
              <p className="feature-description">
                Beautiful, high-quality illustrations generated automatically for each story scene.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📖</div>
              <h3 className="feature-title">Interactive Storybook</h3>
              <p className="feature-description">
                Read your stories in a beautiful, page-turning interface that feels like a real book.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">✨</div>
              <h3 className="feature-title">Quality Assurance</h3>
              <p className="feature-description">
                Built-in review system ensures every story is coherent, appropriate, and engaging.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3 className="feature-title">Lightning Fast</h3>
              <p className="feature-description">
                Generate complete illustrated stories in just a few minutes with our optimized AI pipeline.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3 className="feature-title">Privacy First</h3>
              <p className="feature-description">
                All processing happens locally on your device. Your stories and ideas stay private.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works-section">
        <div className="how-it-works-container">
          <div className="section-header">
            <h2 className="section-title">How It Works</h2>
            <p className="section-description">
              Creating your story is as simple as 1-2-3
            </p>
          </div>
          <div className="steps-container">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3 className="step-title">Share Your Idea</h3>
                <p className="step-description">
                  Simply type your story idea or prompt. It can be as simple as "a cat who learns to fly"
                  or as detailed as you want.
                </p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3 className="step-title">AI Creates Magic</h3>
                <p className="step-description">
                  Our AI agents work together to generate the story structure, write engaging content,
                  and create beautiful illustrations.
                </p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3 className="step-title">Enjoy Your Story</h3>
                <p className="step-description">
                  Read your personalized story in our beautiful interactive storybook interface,
                  complete with illustrations and smooth page transitions.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="about-section">
        <div className="about-container">
          <div className="about-content">
            <div className="about-text">
              <h2 className="section-title">About MyAIStorybook</h2>
              <p className="about-description">
                MyAIStorybook is a cutting-edge AI-powered platform that democratizes story creation.
                Built as a Final Year Project, it combines the latest in artificial intelligence,
                natural language processing, and image generation to create a seamless storytelling experience.
              </p>
              <p className="about-description">
                Our multi-agent architecture ensures that every story is not just generated, but crafted
                with care, reviewed for quality, and enhanced with beautiful illustrations. Whether you're
                a parent looking for bedtime stories, an educator creating learning materials, or simply
                someone who loves creative storytelling, MyAIStorybook brings your ideas to life.
              </p>
              <div className="about-features">
                <div className="about-feature">
                  <span className="about-feature-icon">🎓</span>
                  <span>Academic Project</span>
                </div>
                <div className="about-feature">
                  <span className="about-feature-icon">🤖</span>
                  <span>AI-Powered</span>
                </div>
                <div className="about-feature">
                  <span className="about-feature-icon">🔬</span>
                  <span>Research-Based</span>
                </div>
              </div>
            </div>
            <div className="about-visual">
              <h3 className="tech-title">Powered By</h3>
              <div className="tech-grid">
                <div className="tech-card">
                  <div className="tech-icon">⚡</div>
                  <div className="tech-name">FastAPI</div>
                  <div className="tech-desc">Lightning-fast backend</div>
                </div>
                <div className="tech-card">
                  <div className="tech-icon">⚛️</div>
                  <div className="tech-name">React</div>
                  <div className="tech-desc">Modern UI framework</div>
                </div>
                <div className="tech-card">
                  <div className="tech-icon">🦙</div>
                  <div className="tech-name">Ollama</div>
                  <div className="tech-desc">Local AI models</div>
                </div>
                <div className="tech-card">
                  <div className="tech-icon">🎨</div>
                  <div className="tech-name">Stable Diffusion</div>
                  <div className="tech-desc">AI image generation</div>
                </div>
                <div className="tech-card">
                  <div className="tech-icon">🐍</div>
                  <div className="tech-name">Python</div>
                  <div className="tech-desc">AI orchestration</div>
                </div>
                <div className="tech-card">
                  <div className="tech-icon">🤖</div>
                  <div className="tech-name">AI Agents</div>
                  <div className="tech-desc">Multi-agent system</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-container">
          <div className="cta-content">
            <h2 className="cta-title">Ready to Create Your First Story?</h2>
            <p className="cta-description">
              Join thousands of users who have already discovered the magic of AI-powered storytelling.
            </p>
            <div className="cta-buttons">
              <button
                className="cta-button primary"
                onClick={onStartCreating}
              >
                Start Creating Now
                <svg className="button-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z" />
                </svg>
              </button>
              <button
                className="cta-button secondary"
                onClick={onOpenWorkshop}
              >
                Throw Your Ideas ✨
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <ContactSection />
    </div>
  );
};

export default LandingPage;
