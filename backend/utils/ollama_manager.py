# backend/utils/ollama_manager.py
"""
OllamaManager — DISABLED FOR CLOUD DEPLOYMENT
=============================================
In the local setup, this class managed starting/stopping the Ollama process
to free GPU memory between LLM and image generation steps.

In cloud deployment:
  - LLM is handled by Amazon Bedrock (no local process to manage).
  - Image generation runs on a separate AWS EC2 GPU server.
  - There is NO Ollama process on the cloud backend server.

All methods are safe no-ops so that existing import/call sites in main.py
continue to work without any changes.
"""


class OllamaManager:
    """Stub OllamaManager — all methods are no-ops in cloud deployment."""

    @staticmethod
    def is_ollama_running() -> bool:
        """Always returns False — Ollama is not used in cloud deployment."""
        return False

    @staticmethod
    def pause_ollama() -> bool:
        """No-op — nothing to pause."""
        print("[OllamaManager] ℹ️ Cloud mode: pause_ollama() skipped (Ollama not used).")
        return False

    @staticmethod
    def resume_ollama() -> bool:
        """No-op — nothing to resume."""
        print("[OllamaManager] ℹ️ Cloud mode: resume_ollama() skipped (Ollama not used).")
        return False


def with_ollama_paused(func):
    """Decorator — in cloud mode, just runs the function directly without any Ollama management."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
