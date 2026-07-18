'use client';

import React from 'react';
import styles from './ModeSelection.module.css';

interface ModeSelectionProps {
  onSelectMode: (mode: 'simple' | 'personalized') => void;
  onClose: () => void;
}

export const ModeSelection: React.FC<ModeSelectionProps> = ({ onSelectMode, onClose }) => {
  const handleModeSelect = (mode: 'simple' | 'personalized') => {
    onSelectMode(mode);
    // Don't call onClose() here - onSelectMode handles the navigation
  };

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // Close when clicking on overlay background, not the modal content
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className={styles.overlay} onClick={handleOverlayClick}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 className={styles.title}>✨ Choose Your Story Mode ✨</h2>
          <button className={styles.closeButton} onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        <p className={styles.subtitle}>How would you like to create your story?</p>

        <div className={styles.modeCards}>
          {/* Simple Story Mode */}
          <div
            className={styles.modeCard}
            onClick={() => handleModeSelect('simple')}
          >
            <div className={styles.icon}>📖</div>
            <h3 className={styles.cardTitle}>Simple Story</h3>
            <p className={styles.cardDescription}>
              Create a magical story with beautiful illustrations.
              Just describe your idea and let AI bring it to life!
            </p>
            <button className={styles.selectButton}>
              Create Simple Story
            </button>
          </div>

          {/* Personalized Story Mode */}
          <div
            className={styles.modeCard}
            onClick={() => handleModeSelect('personalized')}
          >
            <div className={styles.icon}>🎨</div>
            <h3 className={styles.cardTitle}>Personalized Story</h3>
            <p className={styles.cardDescription}>
              Create a unique story with personalized characters and themes.
              Your imagination, your adventure!
            </p>
            <button className={styles.selectButton}>
              Create Personalized Story
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
