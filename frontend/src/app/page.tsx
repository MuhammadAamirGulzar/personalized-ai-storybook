'use client';

import { useState, useEffect } from 'react';
import { Navigation, Footer } from '@/layout';
import StoryHistorySidebar from '@/layout/StoryHistorySidebar';
import WorkshopLibrarySidebar from '@/layout/WorkshopLibrarySidebar';
import { LandingPage, ModeSelection, IdeaWorkshop, WorkshopPage } from '@/views/Home';
import { StoryInput, StoryDisplay } from '@/views/Story';
import { Login, Register } from '@/views/Auth';
import { LoadingExperience } from '@/shared/components';
import { API_BASE_URL } from '@/utils/constants';

// Story type definition
interface Story {
  title: string;
  setting: string;
  characters: string[];
  scenes: Array<{
    scene_number: number;
    text: string;
    image_description?: string;
    image_url?: string;
  }>;
  meta?: {
    prompt_type: string;
    enhanced_prompt: string;
  };
}

export default function Home() {
  const [story, setStory] = useState<Story | null>(null);
  const [storyId, setStoryId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showLanding, setShowLanding] = useState<boolean>(true);
  const [showModeSelection, setShowModeSelection] = useState<boolean>(false);
  const [selectedMode, setSelectedMode] = useState<'simple' | 'personalized'>('simple');
  const [showLogin, setShowLogin] = useState<boolean>(false);
  const [showRegister, setShowRegister] = useState<boolean>(false);
  const [showWorkshop, setShowWorkshop] = useState<boolean>(false);
  const [workshopMode, setWorkshopMode] = useState<'improvement' | 'new_idea' | null>(null);
  const [showWorkshopPage, setShowWorkshopPage] = useState<boolean>(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);
  const [isWorkshopLibraryOpen, setIsWorkshopLibraryOpen] = useState<boolean>(false);

  // Scroll to top when navigating to workshop page or mode selection
  useEffect(() => {
    if (showWorkshopPage || showModeSelection || !showLanding) {
      window.scrollTo(0, 0);
    }
  }, [showWorkshopPage, showModeSelection, showLanding]);

  const handleStartCreating = (): void => {
    setShowLanding(false);
    setShowModeSelection(true);
  };

  const handleModeSelected = (mode: 'simple' | 'personalized'): void => {
    setSelectedMode(mode);
    setShowModeSelection(false);
    setStory(null);
    setError(null);
  };

  const handleStoryGenerated = (newStory: Story, newStoryId?: number): void => {
    setStory(newStory);
    if (newStoryId) {
      setStoryId(newStoryId);
    }
    setError(null);
    setShowLanding(false);
  };

  const handleReset = (): void => {
    setStory(null);
    setStoryId(null);
    setError(null);
    setShowLanding(true);
    setShowWorkshopPage(false);
    setWorkshopMode(null);
  };

  const handleGoHome = (): void => {
    setStory(null);
    setStoryId(null);
    setError(null);
    setShowLanding(true);
    setShowModeSelection(false);
    setShowWorkshop(false);
    setShowWorkshopPage(false);
    setWorkshopMode(null);
  };

  const handleOpenWorkshop = (): void => {
    setShowWorkshop(true);
  };

  const handleWorkshopModeSelected = (mode: 'improvement' | 'new_idea'): void => {
    setWorkshopMode(mode);
    setShowWorkshop(false);
    setShowLanding(false);
    setShowWorkshopPage(true);
  };

  const handleBackFromWorkshop = (): void => {
    setShowWorkshopPage(false);
    setWorkshopMode(null);
    setShowLanding(true);
  };

  const handleLoadStoryFromHistory = async (id: number): Promise<void> => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/api/stories/${id}`, {

        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStory(data.story_data);
        setStoryId(data.id);
        setSelectedMode(data.mode);
        setShowLanding(false);
        setShowModeSelection(false);
        setShowWorkshopPage(false);
        setError(null);
      } else {
        setError('Failed to load story from history');
      }
    } catch (err) {
      console.error('Error loading story:', err);
      setError('Connection error while loading story');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <Navigation
        onReset={handleReset}
        showReset={story !== null}
        onGoHome={handleGoHome}
        onShowLogin={() => setShowLogin(true)}
        onShowRegister={() => setShowRegister(true)}
      />

      <StoryHistorySidebar
        isOpen={isHistoryOpen}
        onToggle={() => setIsHistoryOpen(!isHistoryOpen)}
        onLoadStory={handleLoadStoryFromHistory}
        onNewStory={handleReset}
        isWorkshopOpen={isWorkshopLibraryOpen}
        onWorkshopToggle={() => setIsWorkshopLibraryOpen(!isWorkshopLibraryOpen)}
      />

      <WorkshopLibrarySidebar
        isOpen={isWorkshopLibraryOpen}
        onToggle={() => setIsWorkshopLibraryOpen(!isWorkshopLibraryOpen)}
      />

      {loading && <LoadingExperience />}

      <main className="main-content">
        {/* Workshop Full Page */}
        {showWorkshopPage && workshopMode ? (
          <div className="story-input-section">
            <div className="story-input-container" style={{ maxWidth: '900px' }}>
              <WorkshopPage
                mode={workshopMode}
                onBack={handleBackFromWorkshop}
              />
            </div>
          </div>
        ) : showLanding && !story ? (
          <LandingPage
            onStartCreating={handleStartCreating}
            onOpenWorkshop={handleOpenWorkshop}
          />
        ) : showModeSelection ? (
          <ModeSelection
            onSelectMode={handleModeSelected}
            onClose={() => {
              setShowModeSelection(false);
              setShowLanding(true);
            }}
          />
        ) : !story ? (
          <div className="story-input-section">
            <div className="story-input-container">
              <StoryInput
                onStoryGenerated={handleStoryGenerated}
                setLoading={setLoading}
                setError={setError}
                onShowLogin={() => setShowLogin(true)}
                mode={selectedMode}
              />
            </div>
          </div>
        ) : (
          <div className="story-display-section">
            <StoryDisplay
              story={story}
              storyId={storyId}
              onReset={handleReset}
            />
          </div>
        )}
      </main>

      <Footer />

      <IdeaWorkshop
        isOpen={showWorkshop}
        onClose={() => setShowWorkshop(false)}
        onModeSelected={handleWorkshopModeSelected}
      />

      {showLogin && (
        <Login
          onClose={() => setShowLogin(false)}
          onSwitchToRegister={() => { setShowLogin(false); setShowRegister(true); }}
        />
      )}

      {showRegister && (
        <Register
          onClose={() => setShowRegister(false)}
          onSwitchToLogin={() => { setShowRegister(false); setShowLogin(true); }}
        />
      )}
    </div>
  );
}
