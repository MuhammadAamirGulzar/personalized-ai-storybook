'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSpeechToText } from '@/hooks/useSpeechToText';
import { VoiceInputButton } from '@/shared/components/VoiceInputButton';
import styles from './IdeaWorkshop.module.css';

interface IdeaWorkshopProps {
    isOpen: boolean;
    onClose: () => void;
    onModeSelected?: (mode: 'improvement' | 'new_idea') => void;
}

interface Message {
    role: 'user' | 'assistant';
    message: string;
    metadata?: any;
}

export const IdeaWorkshop: React.FC<IdeaWorkshopProps> = ({ isOpen, onClose, onModeSelected }) => {
    const [sessionId, setSessionId] = useState<number | null>(null);
    const [mode, setMode] = useState<'improvement' | 'new_idea' | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [userInput, setUserInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [readyToGenerate, setReadyToGenerate] = useState(false);
    const [generatedStory, setGeneratedStory] = useState<string | null>(null);
    const [storyVersion, setStoryVersion] = useState(1);
    const [wordCount, setWordCount] = useState(0);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const messagesContainerRef = useRef<HTMLDivElement>(null);

    // Speech-to-text hook
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

    // Scroll only the messages container (not the page)
    const scrollMessagesToBottom = useCallback(() => {
        const container = messagesContainerRef.current;
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }, []);

    // Scroll messages container to bottom whenever messages update
    useEffect(() => {
        scrollMessagesToBottom();
    }, [messages, scrollMessagesToBottom]);

    // Word count for improvement mode
    useEffect(() => {
        if (mode === 'improvement') {
            setWordCount(userInput.trim().split(/\s+/).filter(w => w.length > 0).length);
        }
    }, [userInput, mode]);

    const handleModeSelect = async (selectedMode: 'improvement' | 'new_idea') => {
        // If onModeSelected callback is provided, navigate to dedicated page
        if (onModeSelected) {
            onModeSelected(selectedMode);
            return;
        }

        // Fallback: Handle mode selection internally (legacy behavior)
        console.log('Mode selected:', selectedMode);
        setIsLoading(true);
        try {
            console.log('Making API call to start workshop...');
            const response = await fetch('http://127.0.0.1:8000/api/workshop/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: selectedMode })
            });

            console.log('Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('API error:', errorText);
                throw new Error(`Failed to start workshop: ${errorText}`);
            }

            const data = await response.json();
            console.log('Workshop started:', data);

            setSessionId(data.session_id);
            setMode(selectedMode);
            setMessages([{
                role: 'assistant',
                message: data.initial_message
            }]);
        } catch (error) {
            console.error('Error starting workshop:', error);
            alert(`Failed to start workshop. Error: ${error}\n\nMake sure the backend server is running on http://127.0.0.1:8000`);
            setIsLoading(false); // Reset loading on error
        } finally {
            setIsLoading(false);
        }
    };

    // Detect if the user explicitly wants to generate the story
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

    const handleSendMessage = async () => {
        if (!userInput.trim() || !sessionId || isLoading) return;

        const message = userInput.trim();

        // If all fields are collected AND the user explicitly asks to generate, trigger story generation
        if (readyToGenerate && isGenerateIntent(message)) {
            setUserInput('');
            setMessages(prev => [...prev, { role: 'user', message }]);
            handleGenerateStory();
            return;
        }

        // Otherwise always continue the conversation normally
        setUserInput('');
        setIsLoading(true);

        // Add user message optimistically
        setMessages(prev => [...prev, { role: 'user', message }]);

        try {
            const response = await fetch('http://127.0.0.1:8000/api/workshop/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    user_message: message
                })
            });

            if (!response.ok) throw new Error('Failed to send message');

            const data = await response.json();

            // Add assistant response
            setMessages(prev => [...prev, {
                role: 'assistant',
                message: data.response,
                metadata: data.metadata
            }]);

            setReadyToGenerate(data.ready_to_generate);
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateStory = async () => {
        if (!sessionId) return;

        setIsLoading(true);
        try {
            const response = await fetch('http://127.0.0.1:8000/api/workshop/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });

            if (!response.ok) throw new Error('Failed to generate story');

            const data = await response.json();
            setGeneratedStory(data.story_text);
            setStoryVersion(data.version);
        } catch (error) {
            console.error('Error generating story:', error);
            alert('Failed to generate story. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleImproveFurther = () => {
        setGeneratedStory(null);
        setReadyToGenerate(false);
        setMessages(prev => [...prev, {
            role: 'assistant',
            message: "What would you like to improve about the story?"
        }]);
    };

    const handleAcceptStory = () => {
        alert('Story saved! You can now close the workshop.');
        handleClose();
    };

    const handleClose = () => {
        setSessionId(null);
        setMode(null);
        setMessages([]);
        setUserInput('');
        setGeneratedStory(null);
        setReadyToGenerate(false);
        setStoryVersion(1);
        onClose();
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
        // Close when clicking on overlay background, not the modal content
        if (e.target === e.currentTarget) {
            handleClose();
        }
    };

    if (!isOpen) return null;

    return (
        <div className={styles.overlay} onClick={handleOverlayClick}>
            <div className={styles.modal}>
                <div className={styles.header}>
                    <h2 className={styles.title}>✨ Idea Workshop</h2>
                    <button className={styles.closeButton} onClick={handleClose} aria-label="Close">✕</button>
                </div>

                {!mode ? (
                    // Mode Selection Screen
                    <div className={styles.modeSelection}>
                        <p className={styles.prompt}>How would you like to start?</p>
                        {isLoading && <p className={styles.loadingText}>Starting workshop...</p>}
                        <div className={styles.modeCards}>
                            <div
                                className={`${styles.modeCard} ${isLoading ? styles.disabled : ''}`}
                                onClick={() => !isLoading && handleModeSelect('improvement')}
                            >
                                <div className={styles.modeIcon}>🔧</div>
                                <h3>Improve My Story</h3>
                                <p>I have a story and want to make it better</p>
                            </div>

                            <div
                                className={`${styles.modeCard} ${isLoading ? styles.disabled : ''}`}
                                onClick={() => !isLoading && handleModeSelect('new_idea')}
                            >
                                <div className={styles.modeIcon}>💡</div>
                                <h3>Share a New Idea</h3>
                                <p>I have an idea and want to build it together</p>
                            </div>
                        </div>
                    </div>
                ) : generatedStory ? (
                    // Story Display Screen
                    <div className={styles.storyDisplay}>
                        <div className={styles.storyHeader}>
                            <h3>Generated Story (Version {storyVersion})</h3>
                        </div>
                        <div className={styles.storyContent}>
                            {generatedStory}
                        </div>
                        <div className={styles.storyActions}>
                            <button
                                className={styles.acceptButton}
                                onClick={handleAcceptStory}
                            >
                                ✓ I Like It!
                            </button>
                            {mode === 'improvement' && (
                                <button
                                    className={styles.improveButton}
                                    onClick={handleImproveFurther}
                                >
                                    🔧 Improve Further
                                </button>
                            )}
                        </div>
                    </div>
                ) : (
                    // Chat Interface
                    <div className={styles.chatInterface}>
                        <div className={styles.modeIndicator}>
                            {mode === 'improvement' ? '🔧 Improvement Mode' : '💡 New Idea Mode'}
                        </div>

                        <div className={styles.messagesContainer} ref={messagesContainerRef}>
                            {messages.map((msg, index) => (
                                <div
                                    key={index}
                                    className={`${styles.message} ${msg.role === 'user' ? styles.userMessage : styles.assistantMessage
                                        }`}
                                >
                                    <div className={styles.messageBubble}>
                                        {msg.message}
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className={`${styles.message} ${styles.assistantMessage}`}>
                                    <div className={styles.messageBubble}>
                                        <span className={styles.typing}>Thinking...</span>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        <div className={styles.inputContainer}>
                            {mode === 'improvement' && wordCount > 0 && (
                                <div className={styles.wordCounter}>
                                    <span className={wordCount > 300 ? styles.wordCountError : ''}>
                                        {wordCount}/300 words
                                    </span>
                                </div>
                            )}
                            <div className={styles.inputWrapper}>
                                <textarea
                                    className={styles.input}
                                    value={isListening ? userInput + (userInput && interimTranscript ? ' ' : '') + interimTranscript : userInput}
                                    onChange={(e) => setUserInput(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder={readyToGenerate ? "Type 'generate' to create the story..." : "Type your message..."}
                                    rows={3}
                                    disabled={isLoading}
                                />
                                <VoiceInputButton
                                    isListening={isListening}
                                    isSupported={isSupported}
                                    onHoldStart={handleVoiceStart}
                                    onHoldEnd={handleVoiceEnd}
                                    disabled={isLoading}
                                    className={styles.voiceButton}
                                />
                            </div>
                            <button
                                className={styles.sendButton}
                                onClick={handleSendMessage}
                                disabled={!userInput.trim() || isLoading || (mode === 'improvement' && wordCount > 300)}
                            >
                                {readyToGenerate ? '✨ Send Message' : 'Send'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
