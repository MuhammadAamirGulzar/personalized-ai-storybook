# backend/agents/evaluation_agent.py
import sys
import os
import json
import traceback
from typing import Optional

# Add project root to path so we can import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.utils.evaluation_manager import get_evaluation_manager

def main():
    """Main execution block, called when the script is run directly."""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_story_json_file> [story_id]")
        sys.exit(1)

    json_file_path = sys.argv[1]
    story_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    print(f"\n[EvaluationAgent] Starting evaluation for: {json_file_path}")
    
    try:
        if not os.path.exists(json_file_path):
            print(f"[EvaluationAgent] Error: File not found at {json_file_path}")
            sys.exit(1)
            
        with open(json_file_path, 'r', encoding='utf-8') as f:
            story_dict = json.load(f)
        
        # Read mode directly from the story JSON (set by main.py from the request)
        # Fall back to checking image paths as secondary signal
        mode = story_dict.get("mode", "simple")
        if mode not in ("simple", "personalized"):
            mode = "simple"
        print(f"[EvaluationAgent] Story mode: {mode}")
        
        # Get image paths
        image_paths = []
        for scene in story_dict.get("scenes", []):
            img_path = scene.get("image_path")
            if img_path:
                # Handle relative paths if necessary
                if not os.path.isabs(img_path):
                    # Try to resolve relative to project root
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    img_path = os.path.join(base_dir, img_path)
                
                if os.path.exists(img_path):
                    image_paths.append(img_path)
                else:
                    print(f"[EvaluationAgent] Warning: Image file not found at {img_path}")
        
        if not image_paths:
            print("[EvaluationAgent] Warning: No valid image paths found in story JSON.")
        
        # Use EvaluationManager
        eval_manager = get_evaluation_manager()
        
        # If story_id was not provided, use timestamp from filename as a fallback unique ID
        if story_id == 0:
            try:
                # Extract timestamp from filename like "title_123456789.json"
                base_name = os.path.splitext(os.path.basename(json_file_path))[0]
                parts = base_name.split('_')
                if parts[-1].isdigit():
                    story_id = int(parts[-1])
            except:
                import time
                story_id = int(time.time())

        # Perform comprehensive evaluation
        results = eval_manager.evaluate_story(
            story_id=story_id,
            story_dict=story_dict,
            image_paths=image_paths,
            mode=mode
        )
        
        print(f"[EvaluationAgent] ✅ Evaluation completed successfully!")
        print(f"[EvaluationAgent] Overall Score: {results.get('overall_score')}")
        
    except Exception as e:
        print(f"[EvaluationAgent] ❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        # Aggressive Total Memory Cleanup after Evaluation Finishes!
        print("\n[EvaluationAgent] 🧹 Evaluation complete. Initiating total GPU wipe...")
        try:
            import requests
            # Unload the main WebUI checkpoint AND ControlNet cache to totally liberate the GPU!
            requests.post("http://127.0.0.1:7861/sdapi/v1/options", json={"control_net_model_cache_size": 0}, timeout=10)
            response = requests.post("http://127.0.0.1:7861/sdapi/v1/unload-checkpoint", timeout=10)
            if response.status_code == 200:
                print("[EvaluationAgent] ✅ WebUI models and ControlNet fully flushed from VRAM")
        except Exception as e:
            print(f"[EvaluationAgent] ⚠️ WebUI unload skipped (may be offline): {e}")

        try:
            import torch
            import gc
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
                gc.collect()
                print("[EvaluationAgent] ✅ Local PyTorch GPU cache destroyed.")
        except Exception:
            pass

if __name__ == "__main__":
    main()