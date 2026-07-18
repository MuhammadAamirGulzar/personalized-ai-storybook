'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface UseSpeechToTextOptions {
    language?: string;
    continuous?: boolean;
    onTranscript?: (transcript: string) => void;
}

interface UseSpeechToTextReturn {
    isListening: boolean;
    transcript: string;
    interimTranscript: string;
    error: string | null;
    isSupported: boolean;
    startListening: () => void;
    stopListening: () => void;
    resetTranscript: () => void;
}

// Extend Window type for browser Speech API
declare global {
    interface Window {
        SpeechRecognition: any;
        webkitSpeechRecognition: any;
    }
}

// ─── Hook ───────────────────────────────────────────────────────────

export const useSpeechToText = (options: UseSpeechToTextOptions = {}): UseSpeechToTextReturn => {
    const {
        language = 'en-US',
        continuous = false,
        onTranscript
    } = options;

    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [interimTranscript, setInterimTranscript] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isSupported, setIsSupported] = useState(false);

    const recognitionRef = useRef<any>(null);

    // Check browser support on mount
    useEffect(() => {
        const SpeechRecognitionAPI =
            typeof window !== 'undefined' &&
            (window.SpeechRecognition || window.webkitSpeechRecognition);
        setIsSupported(!!SpeechRecognitionAPI);
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            recognitionRef.current?.stop();
        };
    }, []);

    const startListening = useCallback(() => {
        const SpeechRecognitionAPI =
            window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognitionAPI) {
            setError('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
            return;
        }

        try {
            setError(null);
            if (!continuous) setTranscript('');
            setInterimTranscript('Listening...');

            const recognition = new SpeechRecognitionAPI();
            recognitionRef.current = recognition;

            recognition.lang = language;
            recognition.continuous = continuous;
            recognition.interimResults = true;
            recognition.maxAlternatives = 1;

            recognition.onresult = (event: any) => {
                let interim = '';
                let final = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const result = event.results[i];
                    if (result.isFinal) {
                        final += result[0].transcript;
                    } else {
                        interim += result[0].transcript;
                    }
                }

                if (interim) setInterimTranscript(interim);

                if (final) {
                    const updated = continuous ? `${transcript} ${final}`.trim() : final;
                    setTranscript(updated);
                    setInterimTranscript('');
                    if (onTranscript) onTranscript(updated);
                }
            };

            recognition.onerror = (event: any) => {
                console.error('Speech recognition error:', event.error);
                if (event.error === 'no-speech') {
                    setError('No speech detected. Please try again.');
                } else if (event.error === 'not-allowed') {
                    setError('Microphone permission denied. Please allow microphone access.');
                } else {
                    setError(`Speech recognition error: ${event.error}`);
                }
                setIsListening(false);
                setInterimTranscript('');
            };

            recognition.onend = () => {
                setIsListening(false);
                setInterimTranscript('');
            };

            recognition.start();
            setIsListening(true);

        } catch (err) {
            console.error('Error starting speech recognition:', err);
            setError('Failed to start speech recognition');
            setIsListening(false);
            setInterimTranscript('');
        }
    }, [continuous, language, onTranscript, transcript]);

    const stopListening = useCallback(() => {
        recognitionRef.current?.stop();
        setIsListening(false);
        setInterimTranscript('');
    }, []);

    const resetTranscript = useCallback(() => {
        setTranscript('');
        setInterimTranscript('');
        setError(null);
    }, []);

    return {
        isListening,
        transcript,
        interimTranscript,
        error,
        isSupported,
        startListening,
        stopListening,
        resetTranscript
    };
};

export default useSpeechToText;
