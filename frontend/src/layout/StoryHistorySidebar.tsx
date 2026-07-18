import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../utils/constants';
import './StoryHistorySidebar.css';

interface StoryHistorySidebarProps {
    onLoadStory: (storyId: number) => void;
    onNewStory: () => void;
    isOpen: boolean;
    onToggle: () => void;
    // Workshop library icon — sits below the 📜 icon on the same panel
    isWorkshopOpen: boolean;
    onWorkshopToggle: () => void;
}

interface StoryMetadata {
    id: number;
    title: string;
    mode: string;
    created_at: string;
}

const StoryHistorySidebar: React.FC<StoryHistorySidebarProps> = ({
    onLoadStory,
    onNewStory,
    isOpen,
    onToggle,
    isWorkshopOpen,
    onWorkshopToggle,
}) => {
    const [stories, setStories] = useState<StoryMetadata[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchStories();
        }
    }, [isOpen]);

    const fetchStories = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('auth_token');
            if (!token) {
                setLoading(false);
                return;
            }

            const response = await fetch(`${API_BASE_URL}/api/stories`, {

                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                setStories(data);
            }
        } catch (error) {
            console.error('Error fetching stories:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        const options: Intl.DateTimeFormatOptions = {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString(undefined, options);
    };

    return (
        <div className={`story-history-sidebar ${isOpen ? 'open' : ''}`}>
            {/* ── Icon 1: Story Library (📜) ── */}
            <button
                className="sidebar-toggle"
                onClick={onToggle}
                title="Story Library"
            >
                {isOpen ? '✕' : '📜'}
            </button>

            {/* ── Icon 2: Workshop Library (💡) — sits right below 📜 ── */}
            <button
                className="sidebar-toggle sidebar-toggle--workshop"
                onClick={onWorkshopToggle}
                title="Workshop Library"
            >
                {isWorkshopOpen ? '✕' : '💡'}
            </button>

            <div className="sidebar-content">
                <div className="sidebar-header">
                    <h3>Your Library</h3>
                    <button className="new-story-btn" onClick={() => { onNewStory(); onToggle(); }}>
                        + New Story
                    </button>
                </div>

                <div className="stories-list">
                    {loading ? (
                        <div className="sidebar-loading">Loading your tales...</div>
                    ) : stories.length === 0 ? (
                        <div className="no-stories">No stories yet. Create some magic!</div>
                    ) : (
                        stories.map((story) => (
                            <div
                                key={story.id}
                                className="history-item"
                                onClick={() => { onLoadStory(story.id); onToggle(); }}
                            >
                                <div className="item-title">{story.title}</div>
                                <div className="item-meta">
                                    <span className="item-mode">{story.mode}</span>
                                    <span className="item-date">{formatDate(story.created_at)}</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default StoryHistorySidebar;
