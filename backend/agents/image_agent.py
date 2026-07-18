# backend/agents/image_agent.py
import os
from PIL import Image
from backend.model_config import SD_CHECKPOINT_PATH

class ImageAgent:
    """
    Image Agent: Generates illustrations using a local Stable Diffusion model,
    including a high-resolution fix.
    NOTE: This agent is only used in LOCAL mode. On cloud, image generation is
    handled by the Stable Diffusion WebUI running on AWS EC2.
    """
    def __init__(
        self,
        model_path: str = None
    ):
        # Lazy import — diffusers is only needed locally (not on Render cloud)
        try:
            import torch
            from diffusers import StableDiffusionPipeline, AutoPipelineForImage2Image, DPMSolverMultistepScheduler
        except ImportError as e:
            raise ImportError(
                f"ImageAgent requires diffusers and torch. "
                f"These are not available in the cloud environment. "
                f"Use PersonalizedImageAgentWebUIAPI instead. Error: {e}"
            )

        # Get model path from environment variable or use default
        if model_path is None:
            model_path = os.getenv(
                "SD_CHECKPOINT_PATH", 
                SD_CHECKPOINT_PATH
            )
        
        # Check if it's a directory (old format) or file (new format)
        if os.path.isdir(model_path):
            # Look for .safetensors files in the directory
            safetensors_files = [f for f in os.listdir(model_path) if f.endswith('.safetensors')]
            if safetensors_files:
                model_path = os.path.join(model_path, safetensors_files[0])
                print(f"[ImageAgent] Found model file: {model_path}")
            else:
                raise FileNotFoundError(
                    f"No .safetensors files found in directory '{model_path}'. "
                    "Please ensure you have a Stable Diffusion model file."
                )
        elif not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model checkpoint not found at '{model_path}'. "
                "Please set SD_CHECKPOINT_PATH environment variable or place model in backend/pretrained/"
            )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.generator = torch.Generator(device=self.device)
        print(f"[ImageAgent] Using device: {self.device}")

        # --- Model Loading ---
        print("[ImageAgent] Loading Stable Diffusion model... This may take a moment.")
        
        # 1. Use StableDiffusionPipeline to load the local .safetensors file
        self.pipeline = StableDiffusionPipeline.from_single_file(
            model_path,
            torch_dtype=torch.float16,
            use_safetensors=True,
        )

        # 2. Use a high-quality scheduler
        self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipeline.scheduler.config, use_karras_sigmas=True
        )

        # 3. Move pipeline to the GPU and create the img2img pipeline for the hires-fix
        self.pipeline.to(self.device)
        self.img2img_pipeline = AutoPipelineForImage2Image.from_pipe(self.pipeline)
        
        print("[ImageAgent] Model loaded successfully.")

        # Create output folder
        self.output_dir = os.path.join("generated", "images")
        os.makedirs(self.output_dir, exist_ok=True)


    def generate_image(self, prompt_text: str, filename: str = "output.png"):
        print(f"[ImageAgent] Generating image for prompt: '{prompt_text}'...")
    
        # Apply content safety filter with storybook aesthetic reinforcements
        from backend.utils.content_safety import enhance_prompt_for_children
        
        enhanced_prompt, safe_negative, is_safe = enhance_prompt_for_children(prompt_text, mode="simple")
        
        if not is_safe:
            raise ValueError(f"Prompt rejected for child safety: {prompt_text}")
        
        print(f"[ImageAgent] ✅ Content safety filter applied")
    
        # Safety truncation for CLIP
        prompt_words = enhanced_prompt.split()
        if len(prompt_words) > 77:
            enhanced_prompt = " ".join(prompt_words[:77])
            print(f"[ImageAgent] ⚠️ Truncated prompt to 77 tokens for CLIP compatibility.")
    
        # Advanced prompting with safety enhancements and anatomy quality
        positive_prompt = f"masterpiece, best quality, ultra-detailed, photorealistic illustration, clear facial features, {enhanced_prompt}"
        negative_prompt = safe_negative
    
        # Pass 1: txt2img
        print("[ImageAgent] Running Pass 1 (txt2img)...")
        low_res_image = self.pipeline(
            prompt=positive_prompt,
            negative_prompt=negative_prompt,
            width=512,
            height=512,
            num_inference_steps=30,
            guidance_scale=7,
            generator=self.generator,
        ).images[0]
    
        # Pass 2: img2img (Hires fix)
        print("[ImageAgent] Running Pass 2 (img2img for Hires. fix)...")
        high_res_image = self.img2img_pipeline(
            prompt=positive_prompt,
            negative_prompt=negative_prompt,
            image=low_res_image,
            num_inference_steps=35,
            strength=0.5,
            guidance_scale=7,
            generator=self.generator,
        ).images[0]
    
        # Save
        filepath = os.path.join(self.output_dir, filename)
        try:
            high_res_image.save(filepath)
            print(f"✅ Image saved successfully as {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Error saving image: {e}")
            return None


# --- Example of how to use the class ---
if __name__ == "__main__":
    try:
        image_agent = ImageAgent()
        image_agent.generate_image(
            prompt_text="A brave dog in a space suit exploring a vibrant alien planet",
            filename="space_dog.png"
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")