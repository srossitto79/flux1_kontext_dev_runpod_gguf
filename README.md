# Flux Kontext Serverless on Runpod

A production-ready Runpod Serverless worker for high-quality image editing using FLUX.1-Kontext with GGUF quantization for efficient inference.

## Overview

**Model:** FLUX.1-Kontext (GGUF Q5_K_M quantized, ~5GB)
- Efficient diffusion model for photorealistic image editing
- GGUF quantization for reduced memory footprint
- Optimized for 8GB+ VRAM

**Runtime:** Python with Runpod serverless framework

**Input/Output:**
- **Input:** Image (URL or base64) + text prompt for editing
- **Output:** Base64-encoded edited image

## Features

✅ **Production Ready**
- Runpod Serverless integration
- Automatic model downloads on first build
- Offline operation (no internet required at runtime)
- GPU memory optimizations

✅ **Local Development**
- FastAPI test server for local debugging
- Simple Python test script included
- Docker-based reproducible environment

✅ **Flexible Configuration**
- Adjustable inference steps (15-30 recommended)
- Configurable guidance scale for prompt adherence
- Support for multiple image resolutions
- Optional negative prompts

## Quick Start

### 1. Build

```bash
docker build -t flux-kontext-serverless .
```

### 2. Test Locally

```bash
docker run --gpus all -e RUNPOD_LOCAL_TEST=1 -p 3000:3000 flux-kontext-serverless
```

### 3. Send Request

```bash
python test_local_http_endpoint.py
```

For detailed setup instructions, see [QUICK_START.md](QUICK_START.md).

## API Reference

### Endpoint

`POST /` (Runpod Serverless) or `POST http://localhost:3000/` (local testing)

### Request Payload

```json
{
  "input": {
    "image": "base64_encoded_image_or_url",
    "prompt": "editing instruction",
    "negative_prompt": "optional, what to avoid",
    "num_inference_steps": 20,
    "guidance_scale": 7.5,
    "width": 1248,
    "height": 832
  }
}
```

### Response

```json
{
  "image_base64": "base64_encoded_result_image"
}
```

### Parameters

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `image` | string | Yes | - | URL (http/https) or base64 PNG/JPEG |
| `prompt` | string | Yes | - | Image editing instruction |
| `negative_prompt` | string | No | "" | Content to avoid in output |
| `num_inference_steps` | int | No | 20 | Quality vs speed (15-30 recommended) |
| `guidance_scale` | float | No | 3.5 | Prompt adherence (3.0-10.0 typical) |
| `width` | int | No | auto | Must be supported resolution |
| `height` | int | No | auto | Must be supported resolution |

## Supported Resolutions

```
(672×1568), (688×1504), (720×1456), (752×1392), (800×1328), (832×1248),
(880×1184), (944×1104), (1024×1024), (1104×944), (1184×880), (1248×832),
(1328×800), (1392×752), (1456×720), (1504×688), (1568×672)
```

Input images are automatically resized to the closest supported resolution.

## Example Requests

### Example 1: Enhance Outdoor Lighting

```json
{
  "input": {
    "image": "https://example.com/outdoor-photo.jpg",
    "prompt": "enhance the lighting and add golden hour warmth, make it cinematic",
    "num_inference_steps": 20,
    "guidance_scale": 7.5
  }
}
```

### Example 2: Style Transfer

```json
{
  "input": {
    "image": "data:image/png;base64,iVBORw0KGgoAAAANSU...",
    "prompt": "transform into oil painting style with impressionist strokes",
    "negative_prompt": "photograph, realistic, modern",
    "num_inference_steps": 25,
    "guidance_scale": 8.0
  }
}
```

### Example 3: Color Correction

```json
{
  "input": {
    "image": "https://example.com/faded-photo.jpg",
    "prompt": "increase saturation and add vibrant colors while maintaining natural tones",
    "num_inference_steps": 15,
    "guidance_scale": 5.0
  }
}
```

## Performance

**Inference times** (L40 GPU, 1248×832 resolution):
- 15 steps: ~8-10 seconds
- 20 steps: ~12-15 seconds
- 30 steps: ~20-25 seconds

**Memory usage:**
- Model: ~5GB (GGUF Q5_K_M)
- Peak inference: ~6-7GB total
- Recommended: 8GB+ VRAM

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MODELS_DIR` | `/models` | Model storage directory |
| `DEFAULT_STEPS` | `20` | Default inference steps |
| `DEFAULT_SCALE` | `3.5` | Default guidance scale |
| `RUNPOD_LOCAL_TEST` | unset | Set to `1` for FastAPI mode |
| `RP_PORT` | `3000` | Server port (local testing) |

## Deployment

### Local Development

See [QUICK_START.md](QUICK_START.md) for setup and testing.

### Runpod Serverless

1. Push image to container registry
2. Create Runpod Serverless template with your image
3. Deploy and receive HTTP endpoint
4. Send requests with job payloads

For detailed build options, see [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md).

## Troubleshooting

### Common Issues

**"Model not found" error**
- Solution: Rebuild without `--no-cache` flag, ensure internet connection during build

**"CUDA out of memory" error**
- Reduce `num_inference_steps` to 15
- Use smaller image dimensions
- Ensure no other GPU processes are running

**Slow inference (>30 seconds)**
- Expected for high step counts (>25)
- Check GPU utilization with `nvidia-smi`
- Consider reducing `num_inference_steps`

**Output image quality issues**
- Increase `guidance_scale` (7.5-10.0 for stronger adherence)
- Improve prompt clarity and specificity
- Try more inference steps (20-30)
- Ensure input image is clear and well-composed

## File Structure

```
.
├── handler.py                      # Main Runpod handler
├── download_models.py              # Model downloader
├── test_local_http_endpoint.py    # Local testing script
├── Dockerfile                      # Container build definition
├── requirements.txt                # Python dependencies
├── BUILD_INSTRUCTIONS.md           # Build documentation
├── QUICK_START.md                 # Getting started guide
├── README.md                       # This file
└── models/                         # Model directory
    ├── diffusion_models/           # FLUX GGUF model
    ├── loras/                      # Optional LoRA adapters
    └── models--black-forest-labs--FLUX.1-Kontext-Dev/  # HF cache
```

## Architecture

The pipeline architecture:

```
Input Image → Resize to Supported Resolution
           → CLIP Text Encoder (prompt)
           → T5 Text Encoder (prompt)
           → FLUX Transformer (GGUF, with CPU offload)
           → VAE Decoder
           → Output Image
```

## Optimizations

- **Model Quantization:** GGUF Q5_K_M reduces model size from ~23GB to ~5GB
- **Mixed Precision:** bfloat16 computations for speed
- **Memory Management:** CPU offloading keeps GPU VRAM usage minimal
- **Efficient VAE:** Attention slicing for reduced peak memory

## Dependencies

- PyTorch 2.7.1
- Diffusers (main branch)
- Transformers 4.44.0+
- CUDA 12.8 compatible
- See `requirements.txt` for complete list

## Acknowledgments

Built with:
- **FLUX.1-Kontext** by Black Forest Labs
- **Hugging Face** Transformers and Diffusers
- **QuantStack** GGUF format
- **Runpod** Serverless infrastructure
- **PyTorch** and CUDA ecosystem
- **FastAPI** and **Uvicorn** for local testing

## Author

Made with passion by **Salvatore Rossitto**

---

**Last Updated:** October 16, 2025

## Quick local run (Docker)

You can run locally using FastAPI to sanity-check the handler:

1. Build the image (downloads and embeds weights):

```cmd
docker build -t flux-kontext-serverless .
```

2. Run container locally with a simple HTTP API (FastAPI) by setting RUNPOD_LOCAL_TEST=1:

```cmd
docker run --gpus all -p 3000:3000 -e RUNPOD_LOCAL_TEST=1 flux-kontext-serverless
```

3. Send a test job (replace URL as needed):

```cmd
curl -X POST http://localhost:3000/ -H "Content-Type: application/json" -d "{
  \"input\": {
    \"image\": \"https://your-image-url.com/image.png\",
    \"prompt\": \"change the text to read 'Hello Runpod'\",
    \"num_inference_steps\": 20,
    \"guidance_scale\": 3.5
  }
}"
```

The response will contain a base64 field with the edited image.

## Notes

- The Flux Kontext GGUF model is loaded from Hugging Face at build time and baked into `/models` inside the image.
- CUDA 12.x base image with PyTorch is used for broad GPU support.

## Local test script

A small helper script `test_local_http_endpoint.py` posts a request to the local API (when RUNPOD_LOCAL_TEST=1 is used at container start):

1) Ensure the container is running locally:

```cmd
docker run --gpus all -p 3000:3000 -e RUNPOD_LOCAL_TEST=1 flux-kontext-serverless
```

2) On your host, install Python requests if needed and run the test:

```cmd
python -m pip install requests
python test_local_http_endpoint.py
```

The script reads `test_input.jpg` and writes `result.png`.

## Acknowledgments

This project stands on the shoulders of fantastic open-source work:
- FLUX.1-Kontext by Black Forest Labs
- Hugging Face Transformers and Diffusers
- QuantStack for GGUF quantization
- Runpod Serverless
- FastAPI and Uvicorn
- PyTorch and the broader ecosystem

## Author / Contact

Made with passion by Salvatore Rossitto.