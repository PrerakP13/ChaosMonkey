# Llama Local Model Setup Guide

## Overview

ChaosMonkey now uses **Llama** - a powerful open-source language model - to generate intelligent vulnerability recommendations. All processing happens **locally on your machine**, keeping your code and analysis private without stressing Azure cloud resources.

## Key Features

✅ **No external API calls** - Models run on your computer  
✅ **One-time download** - Models are cached after first run  
✅ **Lightweight models** - 7B parameter models optimized for fast inference  
✅ **GPU support** - Automatically uses GPU if available  
✅ **Fallback mode** - Works without AI if model unavailable  

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `llama-cpp-python==0.3.0` - Runtime for Llama models
- `huggingface-hub==0.23.0` - For automatic model downloading

### 2. Download Model (One-time setup)

```bash
python setup_llama.py
```

This will:
- Check available models
- Download Mistral 7B (default, ~5GB) on first run
- Cache it in `backend/models/llama/`
- Future runs use the cache

**Alternative: Choose a different model**

```bash
python setup_llama.py --model llama2-7b
python setup_llama.py --model neural-chat-7b
```

### 3. Verify Setup

```bash
python setup_llama.py --check
```

Shows which models are cached locally.

### 4. Start Backend

```bash
python -m app.main
```

The backend now automatically uses the Llama model for the `/recommend` endpoint.

---

## Available Models

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **Mistral 7B** | 4.9GB | Fast | Excellent | Recommendations (default) |
| **Llama 2 7B** | 4.9GB | Fast | Good | Chat-style analysis |
| **Neural Chat 7B** | 5.0GB | Medium | Excellent | Detailed explanations |

All are quantized to 4-bit for speed and storage efficiency.

---

## How It Works

### Architecture

```
Extension (TypeScript)
    ↓
Backend API (Python FastAPI)
    ↓
Scan Engines (Local)
    ↓
Analyzer + Llama Model (Local)
    ↓
chaos-report.txt
```

### /recommend Endpoint Flow

1. **Request**: Scan results, dependencies, vulnerabilities → Backend
2. **Process**: 
   - Build analysis context
   - Generate prompt from findings
   - Run through Llama model
   - Generate recommendations
3. **Output**: `chaos-report.txt` with:
   - Summary
   - Causes (root causes of vulnerabilities)
   - Effects (potential impact)
   - Solutions (actionable fixes)
   - Recommended next steps

---

## Configuration

### Default Settings (config.env)

```env
LLAMA_CPP_MODEL_PATH=backend/models/llama/7B/your-model.gguf
```

The system automatically finds and uses the cached model.

### Advanced: GPU Acceleration

On systems with NVIDIA GPUs, the model automatically uses GPU acceleration (n_gpu_layers=-1). To manually set:

Edit `backend/app/services/analyzer.py`:
```python
llm = Llama(
    model_path=model_path,
    n_threads=min(4, os.cpu_count() or 1),
    n_gpu_layers=-1,  # Use GPU
    temperature=0.2
)
```

---

## Usage Examples

### Example 1: Generate Recommendation Report

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/path/to/project",
    "analysis": { "cycles": [], "hotspots": [] },
    "services": ["auth", "api", "db"],
    "dependencies": [["auth", "api"], ["api", "db"]],
    "vulnerabilities": [
      {
        "id": "vuln-1",
        "kind": "WEAK_CRYPTO",
        "severity": "HIGH",
        "message": "Uses MD5 for hashing"
      }
    ],
    "chains": []
  }'
```

Response:
```json
{
  "report_path": "/path/to/project/chaos-report.txt",
  "report_text": "Chaos Monkey Vulnerability Report\n..."
}
```

### Example 2: Check Model Status

```bash
python setup_llama.py --check
```

---

## Troubleshooting

### Model Download Fails

**Problem**: "Failed to download model"

**Solutions**:
1. Check internet connection
2. Try a smaller model: `python setup_llama.py --model llama2-7b`
3. Manually download from: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF
4. Place in: `backend/models/llama/`

### Slow Generation (First Run)

**Normal**: First run can take 30-60 seconds while model loads to memory  
**Subsequent runs**: ~5-10 seconds

### Model Not Found Error

**Solution**: Run setup again
```bash
python setup_llama.py
```

### High Memory Usage

**Normal**: 7B models use ~6-8GB RAM (quantized)  
**If your system has <8GB RAM**: Use smaller model or CPU only (slower)

### GPU Not Being Used

**Check**: Run with verbose output
```python
# In analyzer.py, change temperature line to:
print(f"GPU layers being used: {llm.n_gpu_layers}")
```

---

## Performance Notes

### CPU Only (Typical)
- First generation: 30-60 seconds
- Subsequent: 5-10 seconds per report

### With GPU (NVIDIA)
- First generation: 10-20 seconds
- Subsequent: 1-3 seconds per report

### Memory Usage
- Model load: ~6GB (RAM or VRAM)
- Generation overhead: ~1-2GB
- Total: Plan for ~8GB available memory

---

## Architecture Decision: Why Local?

1. **Cost**: No API calls = no subscription
2. **Privacy**: Your analysis stays on your machine
3. **Speed**: No network latency
4. **Reliability**: Works offline
5. **No Azure stress**: Free tier won't throttle

---

## What's Next

- Models are automatically used in `/recommend` endpoint
- If model unavailable, fallback to rule-based recommendations
- Extension shows recommendations in UI automatically
- Check `chaos-report.txt` for full AI-generated analysis

---

## Support

For issues:
1. Run `python setup_llama.py --check` to verify model status
2. Check backend logs for errors
3. Ensure sufficient disk space (~6GB) and RAM (~8GB)
4. Try different model: `python setup_llama.py --model llama2-7b`

---

**Questions?** Check the model status and logs. The system is designed to gracefully fall back if AI processing isn't available.
