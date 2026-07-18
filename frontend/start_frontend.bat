@echo off
echo ==================================
echo  🎨 Setting up ^& Starting Next.js Frontend
echo ==================================

echo Checking for Node.js dependencies...
IF NOT EXIST node_modules (
    echo   -> node_modules folder not found. Installing dependencies now...
    echo   -> This might take a few minutes.
    npm install
    echo   -> Dependencies installed successfully.
) ELSE (
    echo   -> node_modules found.
)

:: 2. Start the Next.js development server
echo Starting Next.js app at http://localhost:3000
npm run dev