'use client';

import React from 'react';
import { useLoadingMessages } from '@/hooks/useLoadingMessages';
import './LoadingExperience.css';

const LoadingExperience: React.FC = () => {
  const message = useLoadingMessages();

  return (
    <div className="loading-overlay">
      <div className="loading-animation"></div>
      <p className="loading-text">{message}</p>
    </div>
  );
};

export default LoadingExperience;
