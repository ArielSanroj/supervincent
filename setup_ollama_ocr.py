#!/usr/bin/env python3
"""
Setup script for Ollama-enhanced OCR system
"""

import subprocess
import sys
import os
import requests
import time
from pathlib import Path

def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_ollama():
    """Install Ollama"""
    print("🔧 Installing Ollama...")
    
    # Check if we're on macOS
    if sys.platform == "darwin":
        try:
            # Install using Homebrew
            subprocess.run(['brew', 'install', 'ollama'], check=True)
            print("✅ Ollama installed via Homebrew")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install via Homebrew, trying manual installation...")
            # Manual installation
            subprocess.run([
                'curl', '-fsSL', 'https://ollama.com/install.sh'
            ], check=True)
            print("✅ Ollama installed manually")
            return True
    else:
        # For Linux/other systems
        try:
            subprocess.run([
                'curl', '-fsSL', 'https://ollama.com/install.sh'
            ], check=True)
            print("✅ Ollama installed")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install Ollama")
            return False

def start_ollama_service():
    """Start Ollama service"""
    print("🚀 Starting Ollama service...")
    
    try:
        # Start Ollama in background
        subprocess.Popen(['ollama', 'serve'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # Wait for service to start
        for i in range(30):
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=1)
                if response.status_code == 200:
                    print("✅ Ollama service started successfully")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)
        
        print("❌ Ollama service failed to start")
        return False
        
    except Exception as e:
        print(f"❌ Error starting Ollama: {e}")
        return False

def download_llama_model():
    """Download Llama model for OCR"""
    print("📥 Downloading Llama model...")
    
    try:
        # Download llama3.2:latest model
        subprocess.run(['ollama', 'pull', 'llama3.2:latest'], check=True)
        print("✅ Llama model downloaded")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to download Llama model")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "data",
        "logs",
        "src/core/ocr",
        "src/core/database",
        "src/core/processors"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def install_python_dependencies():
    """Install additional Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    dependencies = [
        "opencv-python",
        "pytesseract",
        "Pillow",
        "requests",
        "sqlite3"
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                          check=True, capture_output=True)
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError:
            print(f"⚠️ Failed to install {dep}")

def test_ollama_connection():
    """Test Ollama connection"""
    print("🧪 Testing Ollama connection...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama connected, {len(models)} models available")
            return True
        else:
            print("❌ Ollama connection failed")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama connection error: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Ollama-enhanced OCR system...")
    print("=" * 50)
    
    # Step 1: Check if Ollama is installed
    if not check_ollama_installed():
        print("❌ Ollama not found, installing...")
        if not install_ollama():
            print("❌ Failed to install Ollama")
            return False
    else:
        print("✅ Ollama already installed")
    
    # Step 2: Start Ollama service
    if not start_ollama_service():
        print("❌ Failed to start Ollama service")
        return False
    
    # Step 3: Download model
    if not download_llama_model():
        print("❌ Failed to download model")
        return False
    
    # Step 4: Create directories
    create_directories()
    
    # Step 5: Install Python dependencies
    install_python_dependencies()
    
    # Step 6: Test connection
    if not test_ollama_connection():
        print("❌ Ollama connection test failed")
        return False
    
    print("=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run: python src/core/processors/enhanced_invoice_processor.py")
    print("2. Test with: python -c \"from src.core.processors.enhanced_invoice_processor import EnhancedInvoiceProcessor; print('Ready!')\"")
    print("3. Process invoices with improved OCR accuracy")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)