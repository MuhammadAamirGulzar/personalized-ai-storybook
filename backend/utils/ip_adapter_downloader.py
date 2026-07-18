# backend/utils/ip_adapter_downloader.py
"""
IP-Adapter Model Downloader
Automatically downloads IP-Adapter-FaceID models and dependencies
"""
import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download, snapshot_download

from backend.model_config import IP_ADAPTER_BASE_MODEL, IP_ADAPTER_IMAGE_ENCODER

# Model paths
IP_ADAPTER_CHECKPOINT_DIR = os.path.join("backend", "ip_adapter_checkpoints")
IMAGE_ENCODER_DIR = os.path.join(IP_ADAPTER_CHECKPOINT_DIR, "image_encoder")


def ensure_checkpoints_dir():
    """Create checkpoints directory if it doesn't exist"""
    os.makedirs(IP_ADAPTER_CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(IMAGE_ENCODER_DIR, exist_ok=True)
    print(f"✅ Checkpoint directory: {IP_ADAPTER_CHECKPOINT_DIR}")


def download_ip_adapter_faceid():
    """
    Download IP-Adapter-FaceID checkpoint
    File: ip-adapter-faceid_sd15.bin (~23 MB)
    """
    print("\n📥 Downloading IP-Adapter-FaceID checkpoint...")
    
    checkpoint_path = os.path.join(IP_ADAPTER_CHECKPOINT_DIR, "ip-adapter-faceid_sd15.bin")
    
    if os.path.exists(checkpoint_path):
        print(f"✅ IP-Adapter-FaceID checkpoint already exists: {checkpoint_path}")
        return checkpoint_path
    
    try:
        downloaded_path = hf_hub_download(
            repo_id="h94/IP-Adapter-FaceID",
            filename="ip-adapter-faceid_sd15.bin",
            local_dir=IP_ADAPTER_CHECKPOINT_DIR,
            local_dir_use_symlinks=False
        )
        print(f"✅ Downloaded IP-Adapter-FaceID: {downloaded_path}")
        return downloaded_path
    except Exception as e:
        print(f"❌ Failed to download IP-Adapter-FaceID: {e}")
        raise


def download_ip_adapter_full_face():
    """
    Download IP-Adapter Full Face checkpoint
    File: ip-adapter-full-face_sd15.bin (~1.7 GB)
    This is the recommended checkpoint for full-face personalization
    """
    print("\n📥 Downloading IP-Adapter Full Face checkpoint (this may take a while)...")
    
    checkpoint_path = os.path.join(IP_ADAPTER_CHECKPOINT_DIR, "ip-adapter-full-face_sd15.bin")
    
    if os.path.exists(checkpoint_path):
        print(f"✅ IP-Adapter Full Face checkpoint already exists: {checkpoint_path}")
        return checkpoint_path
    
    try:
        downloaded_path = hf_hub_download(
            repo_id="h94/IP-Adapter",
            filename="models/ip-adapter-full-face_sd15.bin",
            local_dir=IP_ADAPTER_CHECKPOINT_DIR,
            local_dir_use_symlinks=False
        )
        print(f"✅ Downloaded IP-Adapter Full Face: {downloaded_path}")
        return downloaded_path
    except Exception as e:
        print(f"❌ Failed to download IP-Adapter Full Face: {e}")
        raise


def download_image_encoder():
    """
    Download CLIP Image Encoder
    Model: laion/CLIP-ViT-H-14-laion2B-s32B-b79K (~2.5 GB)
    Required for IP-Adapter Full Face (1280-dim)
    """
    print("\n📥 Downloading CLIP Image Encoder (this may take a few minutes)...")
    
    # Check if already downloaded
    model_file = os.path.join(IMAGE_ENCODER_DIR, "pytorch_model.bin")
    if os.path.exists(model_file):
        print(f"✅ Image encoder already exists: {IMAGE_ENCODER_DIR}")
        return IMAGE_ENCODER_DIR
    
    try:
        snapshot_download(
            repo_id=IP_ADAPTER_IMAGE_ENCODER,
            local_dir=IMAGE_ENCODER_DIR,
            local_dir_use_symlinks=False
        )
        print(f"✅ Downloaded image encoder to: {IMAGE_ENCODER_DIR}")
        return IMAGE_ENCODER_DIR
    except Exception as e:
        print(f"❌ Failed to download image encoder: {e}")
        raise


def download_insightface_models():
    """
    Download InsightFace models for face analysis
    Required for IP-Adapter-FaceID
    """
    print("\n📥 Downloading InsightFace models...")
    
    insightface_dir = os.path.join(IP_ADAPTER_CHECKPOINT_DIR, "insightface_models")
    os.makedirs(insightface_dir, exist_ok=True)
    
    # Check if already downloaded
    antelopev2_path = os.path.join(insightface_dir, "models", "antelopev2")
    if os.path.exists(antelopev2_path):
        print(f"✅ InsightFace models already exist: {insightface_dir}")
        return insightface_dir
    
    try:
        # Download antelopev2 (face recognition model)
        print("   Downloading antelopev2 model...")
        snapshot_download(
            repo_id="DIAMONIK7777/antelopev2",
            local_dir=os.path.join(insightface_dir, "models", "antelopev2"),
            local_dir_use_symlinks=False
        )
        print(f"✅ Downloaded InsightFace models to: {insightface_dir}")
        return insightface_dir
    except Exception as e:
        print(f"❌ Failed to download InsightFace models: {e}")
        print("⚠️  You may need to download manually from: https://github.com/deepinsight/insightface/tree/master/python-package")
        raise


def download_realistic_vision():
    """
    Download Realistic Vision V4.0 model
    This is the recommended base model for IP-Adapter-FaceID
    """
    print("\n📥 Downloading Realistic Vision V4.0 model (this may take a while)...")
    
    model_dir = os.path.join("backend", "pretrained")
    os.makedirs(model_dir, exist_ok=True)
    
    filename = "Realistic_Vision_V4.0.safetensors"
    model_path = os.path.join(model_dir, filename)
    
    if os.path.exists(model_path):
        print(f"✅ Realistic Vision model already exists: {model_path}")
        return model_path
    
    try:
        downloaded_path = hf_hub_download(
            repo_id=IP_ADAPTER_BASE_MODEL,
            filename=filename,
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )
        print(f"✅ Downloaded Realistic Vision: {downloaded_path}")
        return downloaded_path
    except Exception as e:
        print(f"❌ Failed to download Realistic Vision: {e}")
        raise


def download_all_models():
    """Download all required models for IP-Adapter-FaceID"""
    print("="*60)
    print("🚀 IP-Adapter-FaceID Model Downloader")
    print("="*60)
    
    ensure_checkpoints_dir()
    
    try:
        # Download models
        checkpoint_path = download_ip_adapter_faceid()
        full_face_checkpoint = download_ip_adapter_full_face()
        encoder_path = download_image_encoder()
        insightface_path = download_insightface_models()
        rv_path = download_realistic_vision()
        
        print("\n" + "="*60)
        print("✅ All models downloaded successfully!")
        print("="*60)
        print(f"IP-Adapter FaceID checkpoint: {checkpoint_path}")
        print(f"IP-Adapter Full Face checkpoint: {full_face_checkpoint}")
        print(f"Image encoder: {encoder_path}")
        print(f"InsightFace models: {insightface_path}")
        print(f"Realistic Vision: {rv_path}")
        print("="*60)
        
        return {
            "ip_adapter_checkpoint": checkpoint_path,
            "ip_adapter_full_face": full_face_checkpoint,
            "image_encoder": encoder_path,
            "insightface_models": insightface_path,
            "realistic_vision": rv_path
        }
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ Model download failed!")
        print("="*60)
        print(f"Error: {e}")
        print("\nYou can download models manually:")
        print("1. IP-Adapter: https://huggingface.co/h94/IP-Adapter-FaceID")
        print("2. CLIP Encoder: https://huggingface.co/openai/clip-vit-large-patch14")
        print("3. InsightFace: https://github.com/deepinsight/insightface")
        print("="*60)
        raise


def verify_models():
    """Verify that all required models are present"""
    checkpoint_path = os.path.join(IP_ADAPTER_CHECKPOINT_DIR, "ip-adapter-faceid_sd15.bin")
    full_face_checkpoint = os.path.join(IP_ADAPTER_CHECKPOINT_DIR, "ip-adapter-full-face_sd15.bin")
    encoder_path = os.path.join(IMAGE_ENCODER_DIR, "pytorch_model.bin")
    insightface_path = os.path.join(IP_ADAPTER_CHECKPOINT_DIR, "insightface_models", "models", "antelopev2")
    
    all_present = True
    
    if not os.path.exists(checkpoint_path):
        print(f"❌ Missing: IP-Adapter checkpoint at {checkpoint_path}")
        all_present = False
    else:
        print(f"✅ Found: IP-Adapter FaceID checkpoint")
    
    if not os.path.exists(full_face_checkpoint):
        print(f"❌ Missing: IP-Adapter Full Face checkpoint at {full_face_checkpoint}")
        all_present = False
    else:
        print(f"✅ Found: IP-Adapter Full Face checkpoint")
    
    if not os.path.exists(encoder_path):
        print(f"❌ Missing: Image encoder at {encoder_path}")
        all_present = False
    else:
        print(f"✅ Found: Image encoder")
    
    if not os.path.exists(insightface_path):
        print(f"❌ Missing: InsightFace models at {insightface_path}")
        all_present = False
    else:
        print(f"✅ Found: InsightFace models")

    # Check for Realistic Vision
    # Check for Realistic Vision
    rv_path = os.path.join("backend", "pretrained", "Realistic_Vision_V4.0.safetensors")
    if not os.path.exists(rv_path):
        print(f"❌ Missing: Realistic Vision model at {rv_path}")
        all_present = False
    else:
        print(f"✅ Found: Realistic Vision model")
    
    return all_present


if __name__ == "__main__":
    """Run as standalone script to download models"""
    try:
        # Check if models already exist
        if verify_models():
            print("\n✅ All models are already downloaded!")
            sys.exit(0)
        
        # Download missing models
        download_all_models()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        sys.exit(1)
