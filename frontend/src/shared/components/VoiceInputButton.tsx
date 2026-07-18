'use client';

import React, { useCallback, useRef } from 'react';
import './VoiceInputButton.css';

interface VoiceInputButtonProps {
    isListening: boolean;
    isSupported: boolean;
    onHoldStart: () => void;
    onHoldEnd: () => void;
    disabled?: boolean;
    className?: string;
}

export const VoiceInputButton: React.FC<VoiceInputButtonProps> = ({
    isListening,
    isSupported,
    onHoldStart,
    onHoldEnd,
    disabled = false,
    className = ''
}) => {
    const isHoldingRef = useRef(false);

    // Don't render if speech recognition is not supported
    if (!isSupported) {
        return null;
    }

    const handlePointerDown = (e: React.PointerEvent) => {
        e.preventDefault();
        if (disabled) return;
        isHoldingRef.current = true;
        onHoldStart();
    };

    const handlePointerUp = (e: React.PointerEvent) => {
        e.preventDefault();
        if (!isHoldingRef.current) return;
        isHoldingRef.current = false;
        onHoldEnd();
    };

    const handlePointerLeave = (e: React.PointerEvent) => {
        // If user drags pointer away from button while holding, stop recording
        if (isHoldingRef.current) {
            isHoldingRef.current = false;
            onHoldEnd();
        }
    };

    // Prevent context menu on long press (mobile)
    const handleContextMenu = (e: React.MouseEvent) => {
        e.preventDefault();
    };

    return (
        <button
            type="button"
            className={`voice-input-button ${isListening ? 'listening' : ''} ${className}`}
            onPointerDown={handlePointerDown}
            onPointerUp={handlePointerUp}
            onPointerLeave={handlePointerLeave}
            onPointerCancel={handlePointerUp}
            onContextMenu={handleContextMenu}
            disabled={disabled}
            title={isListening ? 'Release to stop' : 'Hold to speak'}
            aria-label={isListening ? 'Release to stop recording' : 'Hold to speak'}
            style={{ touchAction: 'none', userSelect: 'none' }}
        >
            {/* Sound wave animation rings (visible when recording) */}
            {isListening && (
                <div className="wave-rings">
                    <span className="ring ring-1"></span>
                    <span className="ring ring-2"></span>
                    <span className="ring ring-3"></span>
                </div>
            )}

            {/* Microphone SVG Icon */}
            <svg
                className="mic-svg-icon"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
            >
                <path
                    d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z"
                    fill="currentColor"
                />
                <path
                    d="M17 12C17 14.76 14.76 17 12 17C9.24 17 7 14.76 7 12H5C5 15.53 7.61 18.43 11 18.93V22H13V18.93C16.39 18.43 19 15.53 19 12H17Z"
                    fill="currentColor"
                />
            </svg>

            {/* Audio bars animation (visible when recording) */}
            {isListening && (
                <div className="audio-bars">
                    <span className="bar"></span>
                    <span className="bar"></span>
                    <span className="bar"></span>
                    <span className="bar"></span>
                </div>
            )}

            {/* Hold hint text */}
            {!isListening && (
                <span className="hold-hint">Hold</span>
            )}
        </button>
    );
};

export default VoiceInputButton;
