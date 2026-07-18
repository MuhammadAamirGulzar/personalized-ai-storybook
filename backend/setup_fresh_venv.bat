@echo off
REM ============================================================================
REM Fresh VEnv Setup Script for MyAIStorybook
REM Python 3.10.6 with CUDA 12.8 Support
REM ============================================================================

echo.
echo ============================================================================
echo Creating Fresh Virtual Environment for MyAIStorybook
echo ============================================================================
echo.

cd /d "%~dp0"

REM Step 1: Remove old venv if it exists
if exist "venv" (
    echo [1/6] Removing old virtual environment...
    rmdir /s /q venv
    echo       Old venv removed.
) else (
    echo [1/6] No old venv found, skipping removal.
)

REM Step 2: Create new venv with Python 3.10.6
echo.
echo [2/6] Creating new virtual environment with Python 3.10.6...
py -3.10 -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create venv. Make sure Python 3.10.6 is installed.
    pause
    exit /b 1
)
echo       VEnv created successfully.

REM Step 3: Activate venv
echo.
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat

REM Step 4: Upgrade pip
echo.
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip

REM Step 5: Install PyTorch with CUDA 12.8
echo.
echo [5/6] Installing PyTorch (latest) with CUDA 12.8 support...
echo       This may take a few minutes...
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 (
    echo ERROR: Failed to install PyTorch.
    pause
    exit /b 1
)
echo       PyTorch installed successfully.

REM Step 6: Install all other requirements
echo.
echo [6/6] Installing all other requirements from root requirements.txt...
echo       This may take several minutes...
pip install -r ..\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements.
    pause
    exit /b 1
)

REM Verification
echo.
echo ============================================================================
echo Installation Complete! Verifying...
echo ============================================================================
echo.
python -c "import torch; import diffusers; print('Python Version:', __import__('sys').version); print('PyTorch:', torch.__version__); print('CUDA Available:', torch.cuda.is_available()); print('Diffusers:', diffusers.__version__)"

echo.
echo ============================================================================
echo Setup Complete!
echo ============================================================================
echo.
echo Your virtual environment is ready with:
echo   - Python 3.10.6
echo   - PyTorch (latest) with CUDA 12.8
echo.
echo To activate the venv in the future, run:
echo   venv\Scripts\activate
echo.
echo ============================================================================
pause
