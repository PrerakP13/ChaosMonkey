#!/usr/bin/env python3
"""
Setup script for Llama model initialization in ChaosMonkey backend.
Run this once to download and cache the model locally.

Usage:
    python setup_llama.py                  # Downloads default model (mistral-7b)
    python setup_llama.py --model llama2-7b   # Download specific model
    python setup_llama.py --list           # List available models
    python setup_llama.py --check          # Check what's cached
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path so imports work
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from app.services.model_manager import (
    init_model,
    list_available_models,
    get_cached_models,
    AVAILABLE_MODELS
)


def main():
    parser = argparse.ArgumentParser(
        description="Setup Llama models for ChaosMonkey backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_llama.py                    # Setup default model
  python setup_llama.py --model llama2-7b  # Setup specific model  
  python setup_llama.py --list             # Show available models
  python setup_llama.py --check            # Check cached models
        """
    )
    
    parser.add_argument(
        "--model",
        default="mistral-7b",
        help="Model to download (default: mistral-7b)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available models"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check what models are already cached"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("ChaosMonkey Llama Model Setup")
    print("="*60 + "\n")
    
    if args.list:
        print("📦 Available models:\n")
        for model_name, description in list_available_models().items():
            model_info = AVAILABLE_MODELS[model_name]
            print(f"  • {model_name}")
            print(f"    → {description}")
            print(f"    → Size: ~{model_info['size_mb']}MB")
            print()
        return
    
    if args.check:
        cached = get_cached_models()
        if cached:
            print("✓ Cached models:\n")
            for model_name, info in cached.items():
                print(f"  • {model_name}")
                print(f"    Path: {info['path']}")
                print(f"    Size: {info['size_mb']}MB\n")
        else:
            print("❌ No models cached yet.\n")
        return
    
    # Default: initialize model
    model_name = args.model
    if model_name not in AVAILABLE_MODELS:
        print(f"❌ Unknown model: {model_name}")
        print(f"Available models: {', '.join(AVAILABLE_MODELS.keys())}\n")
        return 1
    
    print(f"🔧 Setting up {model_name}...\n")
    model_path = init_model(model_name)
    
    if model_path:
        print("✅ Setup complete!\n")
        print(f"Model is ready at: {model_path}\n")
        print("📝 The backend will automatically use this model for recommendations.\n")
        
        # Show how to use
        print("Next steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Start the backend: python -m app.main")
        print("  3. Call /recommend endpoint to generate AI-powered reports\n")
        return 0
    else:
        print("❌ Setup failed. Check your internet connection and try again.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
