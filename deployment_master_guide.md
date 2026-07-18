# personalized-ai-storybook: Master Deployment Guide

This guide covers the exact step-by-step process to take your local personalized-ai-storybook project and deploy it to the cloud for your Final Year Project, keeping your $100 AWS credit intact and paying $0 out of pocket.

---

## 🏗️ Architecture Overview

*   **Frontend (Next.js):** Hosted on Vercel (Free forever)
*   **Database (PostgreSQL):** Hosted on Neon.tech (Free forever)
*   **Backend (FastAPI):** Hosted on Render.com (Free tier)
*   **Text AI (LLM):** Amazon Bedrock API (Billed to AWS Credit)
*   **Image AI (SD WebUI + IP-Adapter):** AWS EC2 `g4dn.xlarge` Server (Billed to AWS Credit)

---

## Phase 1: The Database (10 minutes)

We are moving your local PostgreSQL database to the cloud.

1.  Go to [Neon.tech](https://neon.tech/) and sign up for a free account.
2.  Create a new project. Name it `personalized-ai-storybook`.
3.  On your project dashboard, find the **Connection String** (it starts with `postgresql://`).
4.  Copy this string. In your local backend `.env` file (or `backend/auth/database.py`), replace your local `localhost:5432` connection string with this new Neon string.
5.  Your database is now in the cloud. You don't need to change a single line of your database code!

---

## Phase 2: Backend Code Migration (Local Ollama → Amazon Bedrock)

Before uploading your backend, you must change it so it stops trying to talk to the local `Ollama` app and instead talks to the `Amazon Bedrock` API.

**Step 1: Install AWS Dependencies**
In your backend folder, run:
```bash
pip install langchain-aws boto3
```
Add `langchain-aws` and `boto3` to your `requirements.txt` file.

**Step 2: Update the Agents**
Open files like `prompt_agent.py`, `writer_agent.py`, etc. 
Find where you initialize the LLM. It currently looks something like this:
```python
from langchain_community.chat_models import ChatOllama
llm = ChatOllama(model="mistral-nemo:12b")
```

Replace it entirely with the Bedrock version:
```python
import os
from langchain_aws import ChatBedrock

llm = ChatBedrock(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0", # Or any model you enabled in AWS
    region_name="us-east-1",
    model_kwargs={"temperature": 0.7}
)
```

**Step 3: Remove Ollama Manager**
Open `backend/main.py`. Delete or comment out any code related to `OllamaManager`. The cloud backend doesn't need to start or stop any local apps.

---

## Phase 3: Deploy the Backend (FastAPI)

1.  Upload your entire project to a GitHub repository.
2.  Go to [Render.com](https://render.com) and create a free account.
3.  Click **New +** and select **Web Service**.
4.  Connect your GitHub repo.
5.  Configure the service:
    *   **Root Directory:** `backend`
    *   **Environment:** `Python`
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
6.  **Environment Variables:** Add the following inside the Render dashboard:
    *   `AWS_ACCESS_KEY_ID` (Get this from your AWS console)
    *   `AWS_SECRET_ACCESS_KEY` (Get this from your AWS console)
    *   `AWS_DEFAULT_REGION` (e.g., `us-east-1`)
    *   `DATABASE_URL` (Your Neon connection string)
7.  Click **Deploy**. Render will give you a URL (e.g., `https://personalized-ai-storybook-backend.onrender.com`).

*(Note: Render free tier puts the server to sleep after 15 mins of inactivity. It takes ~50 seconds to wake up when someone visits).*

---

## Phase 4: Deploy the Frontend (Next.js)

1.  Go to [Vercel.com](https://vercel.com) and log in with GitHub.
2.  Click **Add New Project** and select your GitHub repo.
3.  Vercel will ask for the "Root Directory". Click Edit and select the `frontend` folder.
4.  **Environment Variables:** 
    *   Add `NEXT_PUBLIC_API_URL` and set it to your Render backend URL (e.g., `https://personalized-ai-storybook-backend.onrender.com`).
5.  Click **Deploy**. Vercel will give you a live website URL.

---

## Phase 5: The Image Generation Server (AWS EC2)

This is where you host your exact `stable-diffusion-webui` folder to keep your IP-Adapter face consistency.

**Step 1: Create the Server**
1. Log into your AWS Console (ensure your $100 credits are active).
2. Go to **EC2** -> **Instances** -> **Launch Instance**.
3. Name it `Storybook-GPU`.
4. Choose an **Ubuntu** Deep Learning AMI (This comes with PyTorch and NVIDIA drivers pre-installed!).
5. For Instance Type, select **`g4dn.xlarge`** (NVIDIA T4 GPU, 16GB VRAM, ~$0.52/hr).
6. Under Network Settings, allow **HTTP/HTTPS** and open **Custom TCP port 7861** (or 7860).
7. Launch the instance and connect to it via SSH.

**Step 2: Upload Your WebUI Folder**
You can zip your local `stable-diffusion-webui` folder (without the heavy models to save upload time) and send it to the server using `scp` or an FTP client like FileZilla.
Alternatively, `git clone` the official A1111 repo on the server and use `wget` to download your `.safetensors` model and IP-adapter weights directly from HuggingFace to the server.

**Step 3: Run the WebUI**
Connect to the server and run:
```bash
./webui.sh --api --listen
```
*(The `--listen` flag is critical! It allows the API to be accessed from the internet, not just locally).*

**Step 4: Connect the Backend**
1. Get the Public IP Address of your AWS EC2 instance.
2. Go back to Render.com and update your backend Environment Variables.
3. Add: `WEBUI_URL = http://<YOUR_AWS_PUBLIC_IP>:7860`

---

## 🚨 The Golden Rule to Save Your Credits

Whenever you are NOT actively demonstrating the project or writing code:
1. Go to the AWS EC2 Dashboard.
2. Right-click your `Storybook-GPU` instance.
3. Select **Stop Instance**. (Billing pauses immediately).

When you need it again, click **Start Instance**. Note that your Public IP address *might* change when you restart it. If it does, just update the `WEBUI_URL` variable in Render!
