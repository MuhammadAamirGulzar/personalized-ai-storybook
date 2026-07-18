'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSpeechToText } from '@/hooks/useSpeechToText';
import { VoiceInputButton } from '@/shared/components/VoiceInputButton';
import { API_BASE_URL } from '@/utils/constants';
import './WorkshopPage.css';

interface Message {
    role: 'user' | 'assistant';
    message: string;
    metadata?: any;
}

interface WorkshopPageProps {
    mode: 'improvement' | 'new_idea';
    onBack: () => void;
    onStoryGenerated?: (story: string) => void;
}

export const WorkshopPage: React.FC<WorkshopPageProps> = ({ mode, onBack, onStoryGenerated }) => {
    const [sessionId, setSessionId] = useState<number | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [userInput, setUserInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [readyToGenerate, setReadyToGenerate] = useState(false);
    const [generatedStory, setGeneratedStory] = useState<string | null>(null);
    const [generatedStoryId, setGeneratedStoryId] = useState<number | null>(null);
    const [wordCount, setWordCount] = useState(0);
    const [isInitializing, setIsInitializing] = useState(true);
    const [connectionError, setConnectionError] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const messagesAreaRef = useRef<HTMLDivElement>(null);

    const {
        isListening,
        isSupported,
        interimTranscript,
        startListening,
        stopListening,
    } = useSpeechToText({
        onTranscript: (transcript) => {
            setUserInput((prev) => prev + (prev ? ' ' : '') + transcript);
        }
    });

    const handleVoiceStart = () => {
        if (!isListening) startListening();
    };
    const handleVoiceEnd = () => {
        if (isListening) stopListening();
    };

    const scrollMessagesToBottom = useCallback(() => {
        const area = messagesAreaRef.current;
        if (area) area.scrollTop = area.scrollHeight;
    }, []);

    // ── Initialize / re-initialize session ──────────────────────────────────
    const initSession = useCallback(async () => {
        setIsInitializing(true);
        setConnectionError(null);
        setMessages([]);
        setReadyToGenerate(false);
        setGeneratedStory(null);
        setGeneratedStoryId(null);
        setSessionId(null);
        try {
            const response = await fetch(`${API_BASE_URL}/api/workshop/start`, {

                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });
            if (!response.ok) throw new Error('Failed to start workshop');
            const data = await response.json();
            setSessionId(data.session_id);
            setMessages([{ role: 'assistant', message: data.initial_message }]);
        } catch (error) {
            console.error('Error starting workshop:', error);
            setConnectionError('Unable to connect to the workshop server. Please make sure the backend is running.');
            setMessages([{
                role: 'assistant',
                message: 'Welcome! I\'m here to help you craft your story. Please share your ideas and let\'s create something magical together! ✨'
            }]);
        } finally {
            setIsInitializing(false);
        }
    }, [mode]);

    useEffect(() => { initSession(); }, [initSession]);

    useEffect(() => {
        scrollMessagesToBottom();
    }, [messages, scrollMessagesToBottom]);

    useEffect(() => {
        if (mode === 'improvement') {
            setWordCount(userInput.trim().split(/\s+/).filter(w => w.length > 0).length);
        }
    }, [userInput, mode]);

    // ── Generate intent detection ────────────────────────────────────────────
    const isGenerateIntent = (text: string): boolean => {
        const lower = text.toLowerCase().trim();
        const patterns = [
            'generate story', 'generate the story', 'create story', 'create the story',
            'generate now', 'create now', 'make the story', 'make story',
            'build the story', 'build story', 'write the story', 'write story',
            'yes, generate', 'yes generate', 'go ahead', 'generate it',
            'create it', 'yes, create', 'yes create', 'proceed', 'generate please',
        ];
        return patterns.some(p => lower.includes(p));
    };

    // ── Send Message ─────────────────────────────────────────────────────────
    const handleSendMessage = async () => {
        if (!userInput.trim() || isLoading) return;
        const message = userInput.trim();

        if (readyToGenerate && isGenerateIntent(message)) {
            setUserInput('');
            setMessages(prev => [...prev, { role: 'user', message }]);
            handleGenerateStory();
            return;
        }

        setUserInput('');
        setIsLoading(true);
        setMessages(prev => [...prev, { role: 'user', message }]);

        if (!sessionId) {
            setTimeout(() => {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    message: 'Thank you for sharing! Let me help you develop this idea further. What other details would you like to add?'
                }]);
                setIsLoading(false);
            }, 1000);
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/workshop/chat`, {

                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, user_message: message })
            });
            if (!response.ok) throw new Error('Failed to send message');
            const data = await response.json();
            setMessages(prev => [...prev, { role: 'assistant', message: data.response, metadata: data.metadata }]);
            setReadyToGenerate(data.ready_to_generate);
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                message: 'I\'m having trouble connecting right now. Please try again in a moment.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    // ── Generate Story ───────────────────────────────────────────────────────
    const handleGenerateStory = async () => {
        if (!sessionId) {
            alert('Session not initialized. Please refresh and try again.');
            return;
        }
        setIsLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/workshop/generate`, {

                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            if (!response.ok) throw new Error('Failed to generate story');
            const data = await response.json();
            setGeneratedStory(data.story_text);
            setGeneratedStoryId(data.story_id ?? null);
            if (onStoryGenerated) onStoryGenerated(data.story_text);
        } catch (error) {
            console.error('Error generating story:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                message: 'Unable to generate the story right now. Please try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    // ── I Love It → save to workshop library + go home ────────────────────
    const handleLoveIt = async () => {
        setIsSaving(true);
        try {
            const token = localStorage.getItem('auth_token');
            const res = await fetch(`${API_BASE_URL}/api/workshop/save`, {

                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    story_id: generatedStoryId,
                    story_text: generatedStory,
                    mode,
                    session_id: sessionId
                })
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                console.error('[Workshop Save] Failed:', res.status, err);
            } else {
                const result = await res.json();
                console.log('[Workshop Save] Success:', result);
            }
        } catch (err) {
            console.error('[Workshop Save] Network error:', err);
        } finally {
            setIsSaving(false);
            onBack();
        }
    };

    // ── Start Over → discard, fresh session ──────────────────────────────────
    const handleStartOver = () => {
        setGeneratedStory(null);
        setGeneratedStoryId(null);
        initSession();          // re-initialize a brand-new session
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const getModeDetails = () => {
        if (mode === 'improvement') {
            return {
                icon: '🔧',
                title: 'Improve My Story',
                subtitle: 'Share your story and let\'s make it even better together.',
                placeholder: 'Paste your story here or describe what you want to improve...'
            };
        }
        return {
            icon: '💡',
            title: 'Share a New Idea',
            subtitle: 'Whisper your idea, and let\'s build a magical story together.',
            placeholder: 'Describe your story idea, characters, or theme...'
        };
    };

    const modeDetails = getModeDetails();

    if (isInitializing) {
        return (
            <div className="workshop-wrapper">
                <div className="workshop-loading">
                    <div className="workshop-spinner"></div>
                    <p>Setting up your creative workshop...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="workshop-wrapper">
            <div className="workshop-header">
                <button className="back-button" onClick={onBack}>← Back to Home</button>
                <div className="mode-badge">
                    <span className="mode-icon">{modeDetails.icon}</span>
                    <span>{modeDetails.title}</span>
                </div>
            </div>

            <div className="workshop-card">
                <div className="workshop-card-header">
                    <h2>{modeDetails.title}</h2>
                    <p>{modeDetails.subtitle}</p>
                </div>

                {connectionError && (
                    <div className="connection-warning">
                        <span>⚠️</span>
                        <p>{connectionError}</p>
                    </div>
                )}

                <div className="chat-container">
                    <div className="messages-area" ref={messagesAreaRef}>
                        {messages.map((msg, index) => (
                            <div
                                key={index}
                                className={`message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}
                            >
                                <div className="message-bubble">{msg.message}</div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="message assistant-message">
                                <div className="message-bubble typing">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="input-area">
                        {mode === 'improvement' && wordCount > 0 && (
                            <div className={`word-count ${wordCount > 300 ? 'error' : ''}`}>
                                {wordCount}/300 words
                            </div>
                        )}
                        <div className="input-row">
                            <textarea
                                className="message-input"
                                value={isListening ? userInput + (userInput && interimTranscript ? ' ' : '') + interimTranscript : userInput}
                                onChange={(e) => setUserInput(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={modeDetails.placeholder}
                                rows={3}
                                disabled={isLoading}
                            />
                            <VoiceInputButton
                                isListening={isListening}
                                isSupported={isSupported}
                                onHoldStart={handleVoiceStart}
                                onHoldEnd={handleVoiceEnd}
                                disabled={isLoading}
                                className="voice-button"
                            />
                        </div>
                        <div className="button-row">
                            <button
                                className="send-message-button"
                                onClick={handleSendMessage}
                                disabled={!userInput.trim() || isLoading || (mode === 'improvement' && wordCount > 300)}
                            >
                                {readyToGenerate ? '✨ Send Message' : 'Send Message'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Story Result Popup Modal ─────────────────────────────────────── */}
            {generatedStory && (
                <div className="story-popup-overlay">
                    <div className="story-popup-modal">
                        <div className="story-popup-header">
                            <h2>✨ Your Generated Story</h2>
                        </div>
                        <div className="story-popup-content">
                            {generatedStory}
                        </div>
                        <div className="story-popup-actions">
                            <button
                                className="popup-btn popup-btn-love"
                                onClick={handleLoveIt}
                                disabled={isSaving}
                            >
                                {isSaving ? 'Saving...' : '❤️ I Love It'}
                            </button>
                            <button
                                className="popup-btn popup-btn-restart"
                                onClick={handleStartOver}
                                disabled={isSaving}
                            >
                                🔄 Start Over
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default WorkshopPage;
