'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useSpeechToText } from '@/hooks/useSpeechToText';
import { VoiceInputButton } from '@/shared/components/VoiceInputButton';
import styles from './Chatbot.module.css';

interface ChatbotProps {
    storyId: number | null;
    storyData: any;
}

interface Message {
    role: 'user' | 'character';
    message: string;
}

export const Chatbot: React.FC<ChatbotProps> = ({ storyId, storyData }) => {
    const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [userInput, setUserInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
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

    const characters = storyData?.characters || [];

    // Safely scroll ONLY the chat container, not the whole page window
    useEffect(() => {
        if (messagesContainerRef.current) {
            messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const handleCharacterSelect = (character: string) => {
        setSelectedCharacter(character);
        setMessages([]); // Clear messages when selecting character (stateless)
    };

    const handleSendMessage = async () => {
        if (!userInput.trim() || !selectedCharacter || !storyId) return;

        const userMessage = userInput.trim();
        setUserInput('');
        setIsLoading(true);

        // Add user message optimistically (temporary - only in React state)
        const newUserMessage: Message = {
            role: 'user',
            message: userMessage
        };
        setMessages(prev => [...prev, newUserMessage]);

        try {
            const response = await fetch('http://127.0.0.1:8000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    story_id: storyId,
                    character_name: selectedCharacter,
                    user_message: userMessage
                })
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            const data = await response.json();

            // Add character response (temporary - only in React state)
            const characterMessage: Message = {
                role: 'character',
                message: data.response
            };
            setMessages(prev => [...prev, characterMessage]);
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    if (!storyId) {
        return null; // Don't show chatbot if no story is generated
    }

    return (
        <div className={styles.chatbotContainer}>
            <h2 className={styles.title}>💬 Talk to Your Story Characters!</h2>

            {!selectedCharacter ? (
                <div className={styles.characterSelection}>
                    <p className={styles.prompt}>Which character would you like to talk to?</p>
                    <div className={styles.characterButtons}>
                        {characters.map((character: string) => (
                            <button
                                key={character}
                                className={styles.characterButton}
                                onClick={() => handleCharacterSelect(character)}
                            >
                                {character}
                            </button>
                        ))}
                    </div>
                </div>
            ) : (
                <div className={styles.chatInterface}>
                    <div className={styles.chatHeader}>
                        <h3>Chatting with: {selectedCharacter}</h3>
                        <button
                            className={styles.changeCharacterButton}
                            onClick={() => {
                                setSelectedCharacter(null);
                                setMessages([]);
                            }}
                        >
                            Change Character
                        </button>
                    </div>

                    <div className={styles.messagesContainer} ref={messagesContainerRef}>
                        {messages.length === 0 && (
                            <p className={styles.welcomeMessage}>
                                👋 Hi! I'm {selectedCharacter}. Ask me anything about our adventure!
                            </p>
                        )}
                        {messages.map((msg, index) => (
                            <div
                                key={index}
                                className={`${styles.message} ${msg.role === 'user' ? styles.userMessage : styles.characterMessage
                                    }`}
                            >
                                <div className={styles.messageBubble}>
                                    <strong>{msg.role === 'user' ? 'You' : selectedCharacter}:</strong>{' '}
                                    {msg.message}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className={`${styles.message} ${styles.characterMessage}`}>
                                <div className={styles.messageBubble}>
                                    <span className={styles.typing}>Typing...</span>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className={styles.inputContainer}>
                        <div className={styles.inputWrapper}>
                            <textarea
                                className={styles.input}
                                value={isListening ? userInput + (userInput && interimTranscript ? ' ' : '') + interimTranscript : userInput}
                                onChange={(e) => setUserInput(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={`Say something to ${selectedCharacter}...`}
                                rows={2}
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
                            disabled={!userInput.trim() || isLoading}
                        >
                            Send
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};
