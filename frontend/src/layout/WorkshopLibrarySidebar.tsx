import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../utils/constants';
import './WorkshopLibrarySidebar.css';

interface WorkshopStoryMeta {
    id: number;
    title: string;
    mode: string;
    story_text: string;
    created_at: string;
}

interface WorkshopLibrarySidebarProps {
    isOpen: boolean;
    onToggle: () => void;
}

const WorkshopLibrarySidebar: React.FC<WorkshopLibrarySidebarProps> = ({ isOpen, onToggle }) => {
    const [stories, setStories] = useState<WorkshopStoryMeta[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedStory, setSelectedStory] = useState<WorkshopStoryMeta | null>(null);

    useEffect(() => {
        if (isOpen) fetchSavedStories();
    }, [isOpen]);

    const fetchSavedStories = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('auth_token');
            if (!token) { setLoading(false); return; }

            const res = await fetch(`${API_BASE_URL}/api/workshop/saved`, {

                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setStories(data);
            } else {
                console.error('[Workshop Library] Fetch failed:', res.status);
            }
        } catch (err) {
            console.error('[Workshop Library] Error fetching workshop library:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString(undefined, {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    };

    const modeLabel = (mode: string) => {
        if (mode === 'new_idea') return '💡 New Idea';
        if (mode === 'improvement') return '🔧 Improved';
        return '✨ Workshop';
    };

    return (
        <>
            {/* Slide-out panel — no toggle button here, icon lives in StoryHistorySidebar */}
            <div className={`workshop-library-sidebar ${isOpen ? 'open' : ''}`}>
                <div className="wl-content">
                    <div className="wl-header">
                        <h3>Workshop Library</h3>
                        <p className="wl-subtitle">Stories you loved ❤️</p>
                        <button className="wl-close-btn" onClick={onToggle} title="Close">✕</button>
                    </div>

                    <div className="wl-list">
                        {loading ? (
                            <div className="wl-empty">Loading your creations...</div>
                        ) : stories.length === 0 ? (
                            <div className="wl-empty">
                                No saved stories yet.<br />
                                Generate a story in the Workshop and click <strong>"I Love It"</strong> to save it here.
                            </div>
                        ) : (
                            stories.map(story => (
                                <div
                                    key={story.id}
                                    className="wl-item"
                                    onClick={() => setSelectedStory(story)}
                                >
                                    <div className="wl-item-title">{story.title}</div>
                                    <div className="wl-item-meta">
                                        <span className="wl-item-mode">{modeLabel(story.mode)}</span>
                                        <span className="wl-item-date">{formatDate(story.created_at)}</span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* Story viewer modal */}
            {selectedStory && (
                <div className="wl-modal-overlay" onClick={() => setSelectedStory(null)}>
                    <div className="wl-modal" onClick={e => e.stopPropagation()}>
                        <div className="wl-modal-header">
                            <div>
                                <h3>{selectedStory.title}</h3>
                                <span className="wl-modal-badge">{modeLabel(selectedStory.mode)}</span>
                            </div>
                            <button className="wl-modal-close" onClick={() => setSelectedStory(null)}>✕</button>
                        </div>
                        <div className="wl-modal-body">{selectedStory.story_text}</div>
                        <div className="wl-modal-footer">
                            <span>{formatDate(selectedStory.created_at)}</span>
                            <button className="wl-modal-done" onClick={() => setSelectedStory(null)}>Close</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default WorkshopLibrarySidebar;
