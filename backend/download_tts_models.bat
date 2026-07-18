@echo off
REM Setup script for downloading Piper TTS voice models

echo ========================================
echo Downloading Piper TTS Voice Models
echo ========================================
echo.

REM Create directory
if not exist "pretrained\tts" mkdir pretrained\tts

echo [1/4] Downloading female voice (lessac) - model file...
powershell -Command "Invoke-WebRequest -Uri 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx' -OutFile 'pretrained\tts\en_US-lessac-medium.onnx'"

echo [2/4] Downloading female voice (lessac) - config file...
powershell -Command "Invoke-WebRequest -Uri 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json' -OutFile 'pretrained\tts\en_US-lessac-medium.onnx.json'"

echo [3/4] Downloading male voice (ryan) - model file...
powershell -Command "Invoke-WebRequest -Uri 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx' -OutFile 'pretrained\tts\en_US-ryan-medium.onnx'"

echo [4/4] Downloading male voice (ryan) - config file...
powershell -Command "Invoke-WebRequest -Uri 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json' -OutFile 'pretrained\tts\en_US-ryan-medium.onnx.json'"

echo.
echo ========================================
echo TTS models downloaded successfully!
echo ========================================
pause
