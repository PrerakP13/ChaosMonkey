"""
Model Manager for Llama - handles automatic downloading and caching of models
"""
import os
import json
from pathlib import Path
from typing import Optional
import hashlib

# Model registry: model_name -> (huggingface_repo, filename, size_mb)
AVAILABLE_MODELS = {
    "mistral-7b": {
        "repo": "TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
        "file": "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        "size_mb": 4900,
        "description": "Mistral 7B (4-bit quantized) - Fast, good quality"
    },
    "llama2-7b": {
        "repo": "TheBloke/Llama-2-7B-Chat-GGUF",
        "file": "llama-2-7b-chat.Q4_K_M.gguf",
        "size_mb": 4900,
        "description": "Llama 2 7B Chat (4-bit quantized) - Balanced"
    },
    "neural-chat-7b": {
        "repo": "TheBloke/neural-chat-7B-v3-1-GGUF",
        "file": "neural-chat-7b-v3-1.Q4_K_M.gguf",
        "size_mb": 5000,
        "description": "Neural Chat 7B - Optimized for chat/recommendations"
    }
}


def get_models_cache_dir() -> Path:
    """Get the directory where models are cached."""
    cache_dir = Path(__file__).resolve().parents[2] / "models" / "llama"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_model_path(model_name: str = "mistral-7b") -> Optional[Path]:
    """
    Get or download a model. Returns the path to the GGUF file if successful, None otherwise.
    
    Args:
        model_name: Name of the model (key from AVAILABLE_MODELS)
    
    Returns:
        Path to the model file, or None if model is not available
    """
    if model_name not in AVAILABLE_MODELS:
        print(f"⚠️  Unknown model: {model_name}. Available models: {list(AVAILABLE_MODELS.keys())}")
        return None
    
    cache_dir = get_models_cache_dir()
    model_info = AVAILABLE_MODELS[model_name]
    model_file = cache_dir / model_info["file"]
    
    # Check if model already exists
    if model_file.exists():
        print(f"✓ Model found in cache: {model_file}")
        return model_file
    
    # Model doesn't exist, attempt download
    print(f"📥 Downloading {model_name}... ({model_info['size_mb']}MB)")
    print(f"   This is a one-time download. Future runs will use the cached copy.")
    
    try:
        from huggingface_hub import hf_hub_download
        
        downloaded_path = hf_hub_download(
            repo_id=model_info["repo"],
            filename=model_info["file"],
            local_dir=str(cache_dir),
            local_dir_use_symlinks=False
        )
        print(f"✓ Successfully downloaded to: {downloaded_path}")
        return Path(downloaded_path)
        
    except ImportError:
        print("⚠️  huggingface_hub not installed. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "huggingface-hub"])
        
        # Retry after installation
        from huggingface_hub import hf_hub_download
        downloaded_path = hf_hub_download(
            repo_id=model_info["repo"],
            filename=model_info["file"],
            local_dir=str(cache_dir),
            local_dir_use_symlinks=False
        )
        print(f"✓ Successfully downloaded to: {downloaded_path}")
        return Path(downloaded_path)
        
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        return None


def list_available_models() -> dict:
    """List all available models with descriptions."""
    return {
        name: info["description"]
        for name, info in AVAILABLE_MODELS.items()
    }


def get_cached_models() -> dict:
    """List models already cached locally."""
    cache_dir = get_models_cache_dir()
    cached = {}
    
    for model_name, model_info in AVAILABLE_MODELS.items():
        model_file = cache_dir / model_info["file"]
        if model_file.exists():
            size_mb = model_file.stat().st_size / (1024 * 1024)
            cached[model_name] = {
                "path": str(model_file),
                "size_mb": round(size_mb, 2)
            }
    
    return cached


def init_model(preferred_model: str = "mistral-7b") -> Optional[Path]:
    """
    Initialize model - download if needed, return path.
    
    Args:
        preferred_model: Which model to use/download
    
    Returns:
        Path to model file, or None if initialization failed
    """
    print(f"\n🚀 Initializing Llama model: {preferred_model}")
    model_path = get_model_path(preferred_model)
    
    if model_path:
        print(f"✓ Model ready: {model_path}\n")
        return model_path
    else:
        print(f"❌ Failed to initialize model.\n")
        return None
