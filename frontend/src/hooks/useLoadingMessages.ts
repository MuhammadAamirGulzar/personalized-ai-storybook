'use client';

import { useState, useEffect } from 'react';
import { LOADING_MESSAGES } from '../utils/constants';

export const useLoadingMessages = (): string => {
  const [message, setMessage] = useState<string>(LOADING_MESSAGES[0]);

  useEffect(() => {
    let messageIndex = 0;
    const interval = setInterval(() => {
      messageIndex = (messageIndex + 1) % LOADING_MESSAGES.length;
      setMessage(LOADING_MESSAGES[messageIndex]);
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  return message;
};
