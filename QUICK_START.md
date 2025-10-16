
# Quick Start Guide - Flux Kontext GGUF

Get up and running with Flux Kontext image editing in minutes.

## Prerequisites

- Docker with GPU support (NVIDIA GPU recommended)
- 8GB+ VRAM
- Internet connection (for first-time model downloads)

## 1. Build the Image

### Option A: Fast Build (with local models)

If you already have the GGUF model:

```bash
docker build -t flux-kontext-serverless .
```

**Build time:** ~2-3 minutes

### Option B: Automatic Download (first time)

If you don't have local models:

```bash
docker build -t flux-kontext-serverless .
```

**What happens:**
- `download_models.py` automatically downloads:
  - Flux Kontext GGUF model (~5GB)
  - Text encoders and VAE configs
  - Tokenizers
- **Build time:** ~10-15 minutes (one-time)
- **Next builds:** ~2-3 minutes (models cached in Docker layers)

## 2. Run Locally for Testing

Start the local development server:

```bash
docker run --gpus all \
  -e RUNPOD_LOCAL_TEST=1 \
  -p 3000:3000 \
  flux-kontext-serverless
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:3000
```

## 3. Test the API

### Using Python (Recommended)

```bash
python test_local_http_endpoint.py
```

The script:
1. Reads `test_input.jpg` from the current directory
2. Resizes it to optimal resolution
3. Sends it to the local API
4. Saves the result as `result.png`

### Using curl

```bash
curl -X POST http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image": "data:image/png;base64,/9j/4AAQSkZJ...",
      "prompt": "enhance the lighting and add cinematic color grading",
      "num_inference_steps": 20,
      "guidance_scale": 7.5,
      "width": 1248,
      "height": 832
    }
  }'
```

Response:
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAA..."
}
```

## 4. Configuration

### Key Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `image` | string | required | Base64 encoded image or URL |
| `prompt` | string | required | Editing instruction |
| `negative_prompt` | string | "" | What to avoid in output |
| `num_inference_steps` | int | 20 | Higher = better quality, slower |
| `guidance_scale` | float | 3.5 | Higher = more prompt adherence |
| `width` | int | auto | Output width (must be supported resolution) |
| `height` | int | auto | Output height (must be supported resolution) |

### Optimal Settings by Use Case

**Fast Preview (8-10s per image):**
```json
{
  "num_inference_steps": 15,
  "guidance_scale": 5.0
}
```

**Balanced Quality (15-20s per image):**
```json
{
  "num_inference_steps": 20,
  "guidance_scale": 7.5
}
```

**High Quality (25-35s per image):**
```json
{
  "num_inference_steps": 30,
  "guidance_scale": 10.0
}
```

## 5. Deploy to Runpod

### Push Image to Registry

```bash
docker tag flux-kontext-serverless your-registry/flux-kontext:latest
docker push your-registry/flux-kontext:latest
```

### Create Runpod Worker

1. Go to Runpod Serverless
2. Create new template
3. Docker image: `your-registry/flux-kontext:latest`
4. Environment:
   - `MODELS_DIR=/models`
   - `DEFAULT_STEPS=20`
   - `DEFAULT_SCALE=3.5`

## Troubleshooting

### "Model file not found"

```
FileNotFoundError: Flux Kontext GGUF model file not found
```

**Solution:** The model wasn't downloaded during build.
- Ensure internet connection during build
- Check `download_models.py` ran successfully (check Docker build logs)
- Try building again: `docker build --no-cache -t flux-kontext-serverless .`

### "CUDA out of memory"

```
RuntimeError: CUDA out of memory
```

**Solutions:**
- Reduce `num_inference_steps` (try 15 or 10)
- Use smaller image dimensions
- Run on GPU with more VRAM (12GB+)
- Close other GPU processes

### "Connection refused" on localhost:3000

**Solution:**
- Ensure you ran with `-e RUNPOD_LOCAL_TEST=1`
- Check Docker is running and container is still up: `docker ps`
- Verify port mapping: `-p 3000:3000`

### Slow image generation

**Expected times** (L40 GPU, 1248x832 resolution):
- 15 steps: ~8-10 seconds
- 20 steps: ~12-15 seconds
- 30 steps: ~20-25 seconds

If much slower:
- Check GPU is being used: `nvidia-smi` in container
- Reduce image resolution
- Check for CPU bottleneck (run fewer inference steps)

## Next Steps

- Read [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for advanced configuration
- Check [README.md](README.md) for project details
- See test script output for API response format

## Setup for Fast Local Development

### Step 1: Prepare Your Models

Place your Flux Kontext GGUF model in the `models/diffusion_models` folder. If not present, it will be downloaded automatically during build.

### Step 2: Build the Docker Image

```bash
docker build -t flux-kontext-serverless .
```

**What happens:**
- Docker copies the `models/` directory (if present)
- `download_models.py` detects existing files and skips downloads
- Pipeline config files are downloaded (small, ~few MB)
- **Build time: ~2-3 minutes** (if models are present; longer if downloading)

### Step 3: Test Locally

```bash
docker run --gpus all -e RUNPOD_LOCAL_TEST=1 -p 3000:3000 flux-kontext-serverless
```

Test with curl:

```bash
curl -X POST http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image": "data:image/png;base64,iVBORw0KG...",
      "prompt": "make it sunny",
      "num_inference_steps": 8,
      "guidance_scale": 4.0
    }
  }'
```

## If You Don't Have Local Models

Just build normally - models will be downloaded automatically:

```bash
docker build -t flux-kontext-serverless .
```

**What happens:**
- `models/` directory only contains .gitkeep files
- `download_models.py` downloads all missing models from HuggingFace
- **Build time: ~10-15 minutes** (one-time download)
- Subsequent builds are fast (models cached in Docker layers)

## Files Structure

```
flux1_kontext_dev_runpod_gguf/
├── handler.py              # Main handler (Flux Kontext GGUF)
├── download_models.py      # Model downloader for Flux Kontext
├── requirements.txt        # Python dependencies
├── Dockerfile              # Build configuration
├── .env                    # Environment variables
└── models/                 # Model files
    ├── diffusion_models/
    │   └── FLUX.1-Kontext-dev-Q5_K_M.gguf
```

## VRAM Usage

The handler is optimized for **8GB+ VRAM**:
- GGUF Q5_K_M quantized Flux Kontext model (~5GB)
- VAE and attention slicing enabled
- Model CPU offload (components move between CPU/GPU as needed)

## Troubleshooting

**Models not found during build:**
- Check that `models/diffusion_models/FLUX.1-Kontext-dev-Q5_K_M.gguf` exists or is downloaded

**Docker build is slow:**
- First time: Normal (downloading models)
- With models present: Should be fast (~2-3 min)
- Check `.dockerignore` doesn't exclude `models/`

## See Also

- [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) - Detailed build documentation
- [models/README.md](models/README.md) - Model directory structure and options
