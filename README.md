# 📖 personalized-ai-storybook

**AI-powered children's storybook generator** with personalized character images using facial recognition.  
Built with **FastAPI backend** + **Next.js frontend** + **Stable Diffusion WebUI** for professional-quality illustrations.

---

## ✨ Key Features

- 🎨 **Personalized Stories** - Upload your photo and become the story's main character
- 🤖 **AI Story Generation** - Powered by Ollama (Llama 3.1)
- 🖼️ **Professional Image Generation** - Uses Stable Diffusion WebUI with IP-Adapter FaceID Plus v2
# Personalized AI Storybook — Technical Overview

An engineer-oriented, production-ready platform for generating personalized children's storybooks with photorealistic character likenesses. The system couples high-quality narrative generation (LLMs) with adapter-conditioned image synthesis for photorealistic scenes, and a safety-first content pipeline designed for age-appropriate outputs.

Maintained by: muhammadaamirgulzar

This repository packages a modular microservice architecture intended for reproducible experiments and production deployment. The implementation focuses on three non-trivial engineering problems:

- Reliable, privacy-preserving face conditioning for image generation (adapter-based conditioning + face embedding pipelines).
- Low-latency, GPU-efficient inference across heterogeneous model types (LLMs + diffusion models) with deterministic artifact management.
- A content-safety pipeline that enforces age-appropriate constraints at both the prompt and image levels.

Core technologies
- Orchestration: FastAPI (backend) + Next.js (frontend)
- LLMs: Ollama (Llama 3.1 family) for controllable narrative generation and refinement
- Image synthesis: Stable Diffusion WebUI with IP-Adapter FaceID Plus v2 for personalized likeness
- Face embedding / detection: InsightFace (adapter conditioning) for identity-aware rendering
- Media tooling: FFmpeg for audio/video processing and PDF exports
- Packaging & deployment: Docker / docker-compose for service isolation; model artifacts stored outside the repository (S3-compatible object storage)

Design highlights (engineering decisions)

- Adapter-conditioned personalization: We condition diffusion generation via IP-Adapter variants rather than fine-tuning large checkpoints. This minimizes checkpoint proliferation and enables rapid per-user likeness adaptation while preserving base-model capabilities.

- GPU memory management: Ollama and diffusion processes run as persistent services. During high-volume image generation we briefly suspend LLM workers, free CUDA caches, and resume LLMs after the job—this avoids OOMs and reduces cold-start overhead.

- Safety-first prompts: The writer agent emits two prompt layers — a canonical creative prompt for LLM creativity and a hardened execution prompt that enforces safety (negative prompts, blocked tokens, and a post-generation image classifier). This two-stage approach separates creativity from constraints and simplifies auditing.

- Deterministic artifact pipeline: Generated assets (images, JSON story manifests, PDFs) are assigned content-based identifiers and stored in object storage. This enables idempotent job retries and efficient caching across services.

Architecture (high-level)

- Frontend (Next.js): User flows for onboarding, photo upload, story creation, job status, and downloads.
- API Gateway (FastAPI): Validation, authentication, job submission, and lightweight orchestration.
- Writer Agent (LLM): Multi-stage prompt engineering, iterative refinement, and structured JSON story output.
- Image Agent (Diffusion): Adapter-conditioned calls to Stable Diffusion WebUI (local or remote WebUI API).
- Worker / Orchestrator: Manages long-running jobs, model loading, GPU affinity and retries; writes artifacts to object storage.

Operational considerations

- Models are not included in this repository. Use documented, vendor-supplied checkpoints and store them on a secured artifact store; keep model checksums in metadata files.
- For development, a single 24–48 GB GPU (A10 / A100) is sufficient to host Ollama + a WebUI instance with constrained batch sizes. Production scaling should split LLM and diffusion services to dedicated GPU pools.
- Use a queue (Redis / RQ or Celery) for job orchestration in production to decouple frontend latency from heavy compute jobs.

Security & privacy

- Consent-first workflows: explicit user consent is required for using personal photos. The system exposes deletion endpoints and a retention policy for uploaded images.
- Image access: all uploaded images and derived assets are stored encrypted at rest when configured with cloud providers. Serve ephemeral signed URLs for downloads.

Reproducibility & developer setup

Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) CUDA-enabled NVIDIA GPU and matching drivers
- Ollama (for local LLM hosting) and a Stable Diffusion WebUI instance for adapter-based generation

Local quick start (developer)

1. Copy the environment template and populate secrets (API keys, object storage credentials, Ollama endpoint):

```bash
cp backend/.env.example backend/.env
# populate OLLAMA_MODEL, WEBUI_URL, and storage credentials
```

2. Install Python dependencies and start the backend (uses virtualenv):

```bash
python -m venv .venv
source .venv/bin/activate      # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

3. Start the frontend:

```bash
cd frontend
pnpm install
pnpm dev
```

Model assets
- Follow the architecture documentation to provision model artifacts. Store large weights outside the git repo and reference them via environment-driven paths or object storage.

API surface (representative)
- `POST /api/v1/generate-story` — Submit user inputs, language, tone, and optional face_id; returns job id.
- `GET /api/v1/jobs/{id}` — Job status and artifact URIs.
- `POST /api/v1/image/{job_id}/render` — Trigger adapter-conditioned image synthesis for a panel/scene.

Testing and benchmarks
- Unit tests for agents live in `backend/tests`. Integration tests validate the end-to-end job flow using mocked model endpoints.
- Benchmarks: measure end-to-end latency for typical short-story job (8–12 panels): LLM generation (120–600 ms/token depending on model) + per-image synthesis (3–12s/image on A10-class GPU) — tune by batching and asynchronous generation.

Attribution & model licensing
- Respect upstream model licenses. This repository contains orchestration and integration code; model checkpoints and commercial use may be subject to separate licensing.

License
- This project is published under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0). See `LICENSE` for details.

Maintainer
- `muhammadaamirgulzar` — reach out via GitHub issues for support and discussion.
