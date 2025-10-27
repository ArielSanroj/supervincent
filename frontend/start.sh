#!/bin/bash

# SuperVincent Finance Frontend Startup Script
echo "🚀 Starting SuperVincent Finance Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Navigate to frontend directory
cd "$(dirname "$0")"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check if SuperVincent API is running
echo "🔍 Checking SuperVincent API connection..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ SuperVincent API is running on port 8000"
else
    echo "⚠️  SuperVincent API not detected on port 8000"
    echo "   The frontend will use mock data"
fi

# Start the development server
echo "🌐 Starting development server..."
echo "   Frontend will be available at: http://localhost:3000"
echo "   Press Ctrl+C to stop the server"
echo ""

npm run dev
