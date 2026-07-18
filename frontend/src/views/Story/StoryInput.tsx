'use client';

import React, { useState } from "react";
import { API_ENDPOINTS } from "@/utils/constants";
import { useAuth } from "@/contexts/AuthContext";
import { useSpeechToText } from "@/hooks/useSpeechToText";
import { VoiceInputButton } from "@/shared/components/VoiceInputButton";
import "./StoryInput.css";

interface StoryInputProps {
  onStoryGenerated: (story: any, storyId?: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  onShowLogin?: () => void;
  mode?: 'simple' | 'personalized';
}

// ─── Face-Not-Found Modal ─────────────────────────────────────────────────────
interface FaceCheckModalProps {
  onReupload: () => void;
  onContinue: () => void;
}
const FaceCheckModal: React.FC<FaceCheckModalProps> = ({ onReupload, onContinue }) => (
  <div className="face-modal-overlay">
    <div className="face-modal">
      <div className="face-modal-icon">🔍</div>
      <h3 className="face-modal-title">No Face Detected</h3>
      <p className="face-modal-body">
        We couldn't detect a clear face in your photo. For best results, use a
        well-lit, front-facing photo without sunglasses or heavy filters.
      </p>
      <div className="face-modal-tip">
        💡 <strong>Tip:</strong> The character in your story will still look
        consistent — we'll use the first generated scene as a reference.
      </div>
      <div className="face-modal-actions">
        <button className="face-modal-btn face-modal-btn--secondary" onClick={onReupload}>
          📸 Re-upload Photo
        </button>
        <button className="face-modal-btn face-modal-btn--primary" onClick={onContinue}>
          ✨ Continue Anyway
        </button>
      </div>
    </div>
  </div>
);
// ─────────────────────────────────────────────────────────────────────────────

const StoryInput: React.FC<StoryInputProps> = ({ onStoryGenerated, setLoading, setError, onShowLogin, mode = 'simple' }) => {
  const { isAuthenticated, token } = useAuth();
  const [prompt, setPrompt] = useState<string>("");
  const [generateImages, setGenerateImages] = useState<boolean>(isAuthenticated);
  const [usePersonalizedImages, setUsePersonalizedImages] = useState<boolean>(false);
  const [userPhoto, setUserPhoto] = useState<string | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [showLoginMessage, setShowLoginMessage] = useState<boolean>(false);

  // Face-check modal state
  const [showFaceModal, setShowFaceModal] = useState<boolean>(false);
  const [useFirstFrameAsReference, setUseFirstFrameAsReference] = useState<boolean>(false);
  const [faceCheckLoading, setFaceCheckLoading] = useState<boolean>(false);

  // Genre and page count state
  const [genre, setGenre] = useState<string>("Fantasy");
  const [numPages, setNumPages] = useState<number>(3);

  // Genre options curated for best LLM and Image Quality
  const genreOptions = [
    "Fantasy",
    "Fairy Tale",
    "Adventure",
    "Sci-Fi",
  ];

  // Page count options (3-4)
  const pageOptions = [3, 4];

  // Speech-to-text hook
  const {
    isListening,
    isSupported,
    interimTranscript,
    startListening,
    stopListening,
  } = useSpeechToText({
    onTranscript: (transcript) => {
      setPrompt((prev) => prev + (prev ? ' ' : '') + transcript);
      setLocalError(null);
    }
  });

  const handleVoiceStart = () => {
    if (!isListening) startListening();
  };

  const handleVoiceEnd = () => {
    if (isListening) stopListening();
  };

  // ── Internal: actually fire the generate request ────────────────────────────
  const fireGenerate = async (firstFrameRef: boolean): Promise<void> => {
    setLoading(true);
    setLocalError(null);
    setError(null);
    setShowLoginMessage(false);

    try {
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      console.log('🎭 Generating:', { usePersonalizedImages, hasPhoto: userPhoto !== null, firstFrameRef });

      const res = await fetch(API_ENDPOINTS.GENERATE, {
        method: "POST",
        headers,
        body: JSON.stringify({
          prompt,
          generate_images: mode === 'personalized' ? true : generateImages,
          use_personalized_images: usePersonalizedImages && userPhoto !== null,
          user_photo: userPhoto,
          use_first_frame_as_reference: firstFrameRef,
          mode,
          genre,
          num_pages: numPages,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        if (res.status === 401 && errorData.detail?.includes("login")) {
          setShowLoginMessage(true);
          throw new Error("Please login to generate images. Guest users can only create text stories.");
        }
        throw new Error(errorData.detail || `The magic faltered. Please try a different idea.`);
      }

      const data = await res.json();
      if (data?.story) {
        onStoryGenerated(data.story, data.story_id);
      } else {
        throw new Error("Received a confusing scroll from the server.");
      }
    } catch (err) {
      console.error("Generation failed:", err);
      const errorMessage = err instanceof Error ? err.message : "An unexpected error occurred";
      setLocalError(errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // ── Submit handler ──────────────────────────────────────────────────────────
  const handleSubmit = async (): Promise<void> => {
    if (!prompt.trim()) {
      setLocalError("Please provide an idea to spark the magic!");
      return;
    }

    if (generateImages && !isAuthenticated) {
      setShowLoginMessage(true);
      setLocalError("Please login to generate images. Guest users can only create text stories.");
      return;
    }

    if (mode === 'personalized' && !userPhoto) {
      setLocalError("Please upload a clear frontal photo for your personalized story.");
      return;
    }

    // In personalized mode with a photo, the face check already ran on upload.
    // If modal was dismissed with "Continue Anyway", useFirstFrameAsReference is already true.
    // Just fire generation with whatever flags are set.
    await fireGenerate(useFirstFrameAsReference);
  };

  const handleImageToggle = (checked: boolean): void => {
    if (checked && !isAuthenticated) {
      setShowLoginMessage(true);
      if (onShowLogin) onShowLogin();
      return;
    }
    setGenerateImages(checked);
    setShowLoginMessage(false);
    setLocalError(null);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // ── Photo upload + face check ───────────────────────────────────────────────
  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setLocalError('Please upload an image file (JPEG or PNG)');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setLocalError('Image too large. Please upload an image smaller than 5MB.');
      return;
    }

    const reader = new FileReader();
    reader.onload = async (event) => {
      const base64Data = event.target?.result as string;
      setUserPhoto(base64Data);
      setPhotoPreview(base64Data);
      setLocalError(null);
      setUseFirstFrameAsReference(false); // reset on new upload

      if (mode === 'personalized') {
        setUsePersonalizedImages(true);

        // Run face check immediately after upload
        setFaceCheckLoading(true);
        try {
          const res = await fetch('/api/check-face', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: base64Data }),
          });
          if (res.ok) {
            const result = await res.json();
            console.log('🔍 Face check result:', result);
            if (!result.face_detected) {
              setShowFaceModal(true);
            }
            // If face detected — silently proceed (green badge already shows)
          }
        } catch (err) {
          console.warn('Face check failed (network/server error) — proceeding optimistically:', err);
        } finally {
          setFaceCheckLoading(false);
        }
      }
    };
    reader.onerror = () => {
      setLocalError('Failed to read the image file');
    };
    reader.readAsDataURL(file);
  };

  const handleRemovePhoto = (): void => {
    setUserPhoto(null);
    setPhotoPreview(null);
    setUsePersonalizedImages(false);
    setUseFirstFrameAsReference(false);
    setShowFaceModal(false);
  };

  const handleFaceModalReupload = (): void => {
    setShowFaceModal(false);
    handleRemovePhoto();
    // Trigger file picker
    document.getElementById('photo-upload')?.click();
  };

  const handleFaceModalContinue = (): void => {
    setShowFaceModal(false);
    setUseFirstFrameAsReference(true);
  };

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="story-input-wrapper">
      {/* Face-not-found modal */}
      {showFaceModal && (
        <FaceCheckModal
          onReupload={handleFaceModalReupload}
          onContinue={handleFaceModalContinue}
        />
      )}

      <div className="story-input-header">
        <h2>Begin Your Adventure</h2>
        <p>Whisper an idea, and watch a world unfold.</p>
      </div>

      <div className="input-field-container">
        <textarea
          className="main-prompt-input"
          placeholder="A cat who learns to sail the seas..."
          value={isListening ? prompt + (prompt && interimTranscript ? ' ' : '') + interimTranscript : prompt}
          onChange={(e) => {
            setPrompt(e.target.value);
            setLocalError(null);
          }}
          onKeyPress={handleKeyPress}
          rows={3}
        />
        <VoiceInputButton
          isListening={isListening}
          isSupported={isSupported}
          onHoldStart={handleVoiceStart}
          onHoldEnd={handleVoiceEnd}
        />
      </div>

      {/* Genre and Page Count Selection */}
      <div className="story-options">
        <div className="option-group">
          <label htmlFor="genre-select">Genre</label>
          <select
            id="genre-select"
            className="option-select"
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
          >
            {genreOptions.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>

        <div className="option-group">
          <label htmlFor="pages-select">Pages</label>
          <select
            id="pages-select"
            className="option-select"
            value={numPages}
            onChange={(e) => setNumPages(parseInt(e.target.value))}
          >
            {pageOptions.map((p) => (
              <option key={p} value={p}>{p} {p === 1 ? 'page' : 'pages'}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="input-controls">
        {/* Simple mode: Illustrate My Story toggle */}
        {mode !== 'personalized' && (
          <div className={`toggle-switch ${!isAuthenticated ? 'disabled' : ''}`}>
            <label className="switch">
              <input
                type="checkbox"
                checked={generateImages && isAuthenticated}
                onChange={(e) => handleImageToggle(e.target.checked)}
                disabled={!isAuthenticated}
              />
              <span className={`slider ${!isAuthenticated ? 'disabled' : ''}`}></span>
            </label>
            <span
              className={!isAuthenticated ? 'disabled-text' : ''}
              title={!isAuthenticated ? 'Please login first to enable image generation' : ''}
            >
              Illustrate My Story
            </span>
            {!isAuthenticated && (
              <div className="illustrate-tooltip">Please login first</div>
            )}
          </div>
        )}

        {/* Personalized mode: photo upload is the primary action */}
        {mode === 'personalized' && (
          <>
            {!isAuthenticated ? (
              <div className="login-prompt">
                <p>Please <button type="button" className="login-link" onClick={onShowLogin}>login</button> to generate personalized story images</p>
              </div>
            ) : (
              <div className="photo-upload-section">
                {!photoPreview ? (
                  <div className="upload-area">
                    <label htmlFor="photo-upload" className="upload-label">
                      <span className="upload-icon">📸</span>
                      <span>Upload Your Photo</span>
                      <input
                        id="photo-upload"
                        type="file"
                        accept="image/jpeg,image/png,image/jpg"
                        onChange={handlePhotoUpload}
                        style={{ display: 'none' }}
                      />
                    </label>
                    <p className="upload-hint">Upload a clear frontal photo — your face will appear in the story!</p>
                  </div>
                ) : (
                  <div className="photo-preview-container">
                    <img src={photoPreview} alt="Your photo" className="photo-preview" />
                    {faceCheckLoading ? (
                      <div className="photo-checking-badge">🔍 Checking for face…</div>
                    ) : useFirstFrameAsReference ? (
                      <div className="photo-fallback-badge">⚠️ No face found — using scene 1 as reference</div>
                    ) : (
                      <div className="photo-ready-badge">✓ Photo ready — generating your story!</div>
                    )}
                    <button
                      type="button"
                      className="remove-photo-btn"
                      onClick={handleRemovePhoto}
                      title="Remove photo"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Simple mode login prompt */}
        {mode !== 'personalized' && showLoginMessage && (
          <div className="login-prompt">
            <p>Please <button type="button" className="login-link" onClick={onShowLogin}>login</button> to enable image generation</p>
          </div>
        )}
      </div>

      <button className="generate-button" onClick={handleSubmit}>
        Weave Magic
      </button>

      {localError && <p className="error-message">{localError}</p>}
    </div>
  );
};

export default StoryInput;
