# backend/utils/tts_manager.py
import os
import wave
import json
import time
from typing import Optional

class TTSManager:
    """
    Manages Text-to-Speech generation using Piper (local ONNX model).
    Handles caching of generated audio files.
    """
    
    def __init__(self):
        # Resolve absolute paths relative to project root
        project_root = os.getcwd()
        self.models_dir = os.path.join(project_root, "backend", "pretrained", "tts")
        
        # Voice mapping: name -> filename (without extension)
        self.voices = {
            "female": "en_US-lessac-medium",
            "male": "en_US-ryan-medium"
        }
        
        # Ensure audio directory exists
        self.audio_dir = os.path.join(project_root, "generated", "audio")
        os.makedirs(self.audio_dir, exist_ok=True)
        
    def generate_audio(self, text: str, story_id: int, scene_number: int, voice: str = "female") -> str:
        """
        Generates audio for a given scene and returns the relative path.
        If the audio already exists, returns the cached path.
        """
        voice_model = self.voices.get(voice, "en_US-lessac-medium")
        model_path = os.path.join(self.models_dir, f"{voice_model}.onnx")
        config_path = os.path.join(self.models_dir, f"{voice_model}.onnx.json")
        
        # Cache filename includes voice to allow switching
        filename = f"story_{story_id}_scene_{scene_number}_{voice}.wav"
        output_path = os.path.join(self.audio_dir, filename)
        relative_path = f"/generated/audio/{filename}"
        
        # Check cache
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return relative_path
            
        # Generate audio using subprocess (CLI is more reliable)
        import subprocess
        import sys
        
        # Get python path from venv if possible
        python_exe = sys.executable
        
        start_time = time.time()
        print(f"[TTS] Generating audio for story {story_id}, scene {scene_number} using voice: {voice}...")
        
        try:
            abs_python = os.path.abspath(python_exe)
            abs_model = os.path.abspath(model_path)
            abs_config = os.path.abspath(config_path)
            abs_output = os.path.abspath(output_path)
            
            # Use a temporary file for input to avoid stdin/shell escaping issues on Windows
            temp_input_path = os.path.join(self.audio_dir, f"temp_{story_id}_{scene_number}_{voice}.txt")
            abs_temp_input = os.path.abspath(temp_input_path)
            
            with open(abs_temp_input, "w", encoding="utf-8") as f:
                f.write(text)
                
            # Construct a robust powershell command using absolute paths
            cmd = f'powershell.exe -Command "Get-Content -Path \'{abs_temp_input}\' -Raw | & \'{abs_python}\' -m piper --model \'{abs_model}\' --config \'{abs_config}\' --output_file \'{abs_output}\'"'
            
            print(f"[TTS] Running command: {cmd}")
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                check=False
            )
            
            # Cleanup temp file
            if os.path.exists(abs_temp_input):
                os.remove(abs_temp_input)
            
            if result.returncode != 0:
                print(f"[TTS] Error generating audio: {result.stderr.decode('utf-8', errors='replace')}")
                if not os.path.exists(abs_output) or os.path.getsize(abs_output) == 0:
                    return ""
                
        except Exception as e:
            print(f"[TTS] Exception during synthesis: {e}")
            return ""
            
        duration = time.time() - start_time
        print(f"[TTS] Audio generated in {duration:.2f}s: {output_path}")
        
        return relative_path

# Singleton instance
_tts_instance = None

def get_tts_manager() -> TTSManager:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TTSManager()
    return _tts_instance
