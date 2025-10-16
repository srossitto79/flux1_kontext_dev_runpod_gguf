# Docker Build Instructions - Flux Kontext GGUF

This project builds a Runpod Serverless image for Flux Kontext image editing using GGUF quantized models.

## Quick Start

### Build the Docker Image

```bash
docker build -t flux-kontext-serverless .
```

The build process automatically:
1. Copies local models from `models/` directory (if present)
2. Runs `download_models.py` to fetch missing models from HuggingFace
3. Installs all Python dependencies
4. Configures the environment for offline operation

**Build time:** ~2-3 minutes (with cached/local models) to ~10-15 minutes (downloading models for first time)

### Run Locally for Testing

```bash
docker run --gpus all \
  -e RUNPOD_LOCAL_TEST=1 \
  -e RP_PORT=3000 \
  -p 3000:3000 \
  flux-kontext-serverless
```

This starts a FastAPI server on port 3000 for local testing.

### Run on Runpod Serverless

```bash
docker run --gpus all flux-kontext-serverless
```

This starts the Runpod serverless handler.

---

## Models

The project uses FLUX.1-Kontext in GGUF quantized format for efficient inference:

**Models Directory:**
```
models/
├── diffusion_models/
│   └── flux1-kontext-dev-Q5_K_M.gguf          # FLUX.1-Kontext GGUF (Q5_K_M quantization)
├── loras/                                       # LoRA adapters (optional)
└── models--black-forest-labs--FLUX.1-Kontext-Dev/  # Hugging Face cache
    └── snapshots/af58063aa431f4d2bbc11ae46f57451d4416a170/
        ├── transformer/                        # FLUX transformer config
        ├── text_encoder/                       # CLIP text encoder
        ├── text_encoder_2/                     # T5 text encoder
        ├── tokenizer/                          # CLIP tokenizer
        ├── tokenizer_2/                        # T5 tokenizer
        ├── vae/                                # VAE decoder
        ├── scheduler/                          # Diffusion scheduler
        └── model_index.json                    # Pipeline configuration
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODELS_DIR` | `/models` | Directory where models are stored |
| `FLUX_MODEL_PATH` | `./models/diffusion_models/flux1-kontext-dev-Q5_K_M.gguf` | Path to FLUX GGUF model |
| `DEFAULT_STEPS` | `20` | Default inference steps |
| `DEFAULT_SCALE` | `3.5` | Default guidance scale |
| `TRANSFORMERS_OFFLINE` | `1` | Force offline mode (prevents accidental downloads) |
| `HF_HUB_OFFLINE` | `1` | Disable HuggingFace Hub at runtime |
| `RUNPOD_LOCAL_TEST` | unset | Set to `1` for local FastAPI testing |
| `RP_PORT` | `3000` | Server port for local testing |
| `RP_HANDLER` | `handler` | Handler function name |
| `RP_NUM_WORKERS` | `1` | Number of worker threads |

---

## API Endpoint

### Request Format

```json
{
  "input": {
    "image": "base64-encoded-image-or-url",
    "prompt": "editing instruction",
    "negative_prompt": "optional unwanted content",
    "num_inference_steps": 20,
    "guidance_scale": 3.5,
    "width": 1248,
    "height": 832
  }
}
```

### Response Format

```json
{
  "image_base64": "base64-encoded-result-image"
}
```

### Example Request

```bash
curl -X POST http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image": "data:image/png;base64,iVBORw0KGgo...",
      "prompt": "enhance the lighting and make it look cinematic",
      "num_inference_steps": 20,
      "guidance_scale": 7.5
    }
  }'
```

---

## Supported Resolutions

FLUX.1-Kontext supports these resolutions (must have both dimensions divisible by 16 and each divided by 16 result even and divisible by 2):

```
(672, 1568), (688, 1504), (720, 1456), (752, 1392), (800, 1328), (832, 1248),
(880, 1184), (944, 1104), (1024, 1024), (1104, 944), (1184, 880), (1248, 832),
(1328, 800), (1392, 752), (1456, 720), (1504, 688), (1568, 672)
```

The handler automatically resizes input images to the closest supported resolution matching the aspect ratio.

---

## VRAM Requirements

- **Minimum:** 8GB VRAM
- **Recommended:** 12GB+ VRAM
- **Typical usage:** ~5-7GB (GGUF Q5_K_M model + inference tensors)

Optimizations applied:
- GGUF Q5_K_M quantization (~5GB model size)
- bfloat16 precision for computations
- Model CPU offload (components swap between CPU/GPU as needed)
- VAE and attention slicing (reduces peak VRAM)

---

## Troubleshooting

### Model not found error

**Problem:** `FileNotFoundError: Flux Kontext GGUF model file not found`

**Solution:**
1. Check that `models/diffusion_models/flux1-kontext-dev-Q5_K_M.gguf` exists
2. If missing, build the image without local models - they'll be downloaded automatically
3. Verify `download_models.py` ran successfully during build

### Build takes too long

**Problem:** First-time build takes 10-15 minutes

**Solution:** This is normal for the first build (downloading models from HuggingFace). Subsequent builds use cached layers and are fast (~2-3 min).

### VRAM usage too high

**Problem:** Container crashes with out-of-memory error

**Solution:**
- Ensure `enable_model_cpu_offload()` is enabled in `handler.py`
- Reduce `num_inference_steps` (lower = faster + less VRAM)
- Use smaller image resolutions
- Run on GPU with 12GB+ VRAM

### Image output looks corrupted

**Problem:** Generated image has artifacts or is blank

**Solution:**
- Check that all text encoders and VAE are properly loaded
- Verify the prompt is meaningful (empty/nonsense prompts may produce artifacts)
- Try increasing `guidance_scale` (higher = more adherence to prompt)
- Ensure input image is valid JPEG/PNG

---

## File Structure

```
flux1_kontext_dev_runpod_gguf/
├── Dockerfile                                  # Container build definition
├── handler.py                                  # Runpod serverless handler
├── download_models.py                          # Model download utility
├── requirements.txt                            # Python dependencies
├── test_local_http_endpoint.py                # Local testing script
├── BUILD_INSTRUCTIONS.md                      # This file
├── README.md                                   # Project overview
├── QUICK_START.md                             # Quick start guide
└── models/                                     # Model files directory
    ├── diffusion_models/
    ├── loras/
    └── models--black-forest-labs--FLUX.1-Kontext-Dev/
```

This project supports two build modes for model management:

## Mode 1: Download Models During Build (Default - for production)

This mode downloads models from HuggingFace during the Docker build process.

```bash
docker build -t qwen-image-edit:latest .
```

Or explicitly:

```bash
docker build --build-arg DOWNLOAD_MODELS=true -t qwen-image-edit:latest .
```

**Pros:**
- Self-contained image with all models
- No external dependencies at runtime
- Ready for cloud deployment

**Cons:**
- Longer build time (~10-15 minutes)
- Requires internet connection during build
- Larger image size

**Models downloaded:**
- Transformer: `Qwen-Image-Edit-2509-Q4_K_M.gguf` from `city96/Qwen-Image-Edit-GGUF`
- Text Encoder: `qwen_2.5_vl_7b_fp8_scaled.safetensors` from `SG161222/Qwen2.5-VL-7B-FP8-Scaled`
- LoRA: `Qwen-Image-Lightning-8steps-V2.0.safetensors` from `lightx2v/Qwen-Image-Lightning`
- Pipeline configs from `Qwen/Qwen-Image-Edit`

---

## Mode 2: Copy Local Models (for local testing/development)

This mode copies models from your local filesystem, skipping the download step.

### Prerequisites

1. **Create the models directory structure:**

```bash
mkdir -p models/diffusion_models
mkdir -p models/text_encoders
mkdir -p models/loras
```

2. **Download or copy the model files** to the appropriate directories:

   - `models/diffusion_models/Qwen-Image-Edit-2509-Q4_K_M.gguf`
     - From: https://huggingface.co/city96/Qwen-Image-Edit-GGUF/resolve/main/Qwen-Image-Edit-2509-Q4_K_M.gguf

   - `models/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors`
     - From: https://huggingface.co/SG161222/Qwen2.5-VL-7B-FP8-Scaled/resolve/main/qwen_2.5_vl_7b_fp8_scaled.safetensors

   - `models/loras/Qwen-Image-Lightning-8steps-V2.0.safetensors`
     - From: https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Lightning-8steps-V2.0.safetensors

3. **Remove `models/` from `.dockerignore`:**

Edit `.dockerignore` and comment out or remove the line:
```
# models/
```

### Build Command

```bash
docker build --build-arg DOWNLOAD_MODELS=false -t qwen-image-edit:dev .
```

**Pros:**
- Fast builds (~2-3 minutes)
- No internet required during build
- Useful for iterating on code changes

**Cons:**
- Requires manual model download first
- Larger Docker context (models are sent to Docker daemon)
- Must remember to restore `.dockerignore` for production builds

---

## Running the Container

### Local Testing with FastAPI

```bash
docker run --gpus all \
  -e RUNPOD_LOCAL_TEST=1 \
  -e RP_PORT=3000 \
  -p 3000:3000 \
  qwen-image-edit:latest
```

Test with curl:

```bash
curl -X POST http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image": "data:image/png;base64,...",
      "prompt": "make it sunny",
      "num_inference_steps": 8,
      "true_cfg_scale": 4.0
    }
  }'
```

### RunPod Serverless Deployment

```bash
docker run --gpus all qwen-image-edit:latest
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODELS_DIR` | `/models` | Directory where models are stored |
| `DEFAULT_STEPS` | `8` | Default inference steps |
| `DEFAULT_SCALE` | `4.0` | Default CFG scale |
| `TRANSFORMERS_OFFLINE` | `1` | Force offline mode (set at build time) |
| `HF_HUB_OFFLINE` | `1` | Disable HuggingFace Hub (set at build time) |
| `RUNPOD_LOCAL_TEST` | unset | Set to `1` for local FastAPI mode |
| `RP_PORT` | `3000` | Server port |

---

## Model URLs Reference

For manual downloads or reference:

1. **Transformer (GGUF quantized):**
   - https://huggingface.co/city96/Qwen-Image-Edit-GGUF/resolve/main/Qwen-Image-Edit-2509-Q4_K_M.gguf

2. **Text Encoder (FP8 quantized):**
   - https://huggingface.co/SG161222/Qwen2.5-VL-7B-FP8-Scaled/resolve/main/qwen_2.5_vl_7b_fp8_scaled.safetensors

3. **LoRA Weights (Lightning 8-step):**
   - https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Lightning-8steps-V2.0.safetensors

4. **Base Pipeline:**
   - https://huggingface.co/Qwen/Qwen-Image-Edit

---

## Troubleshooting

### COPY models/ fails during build

**Problem:** `COPY models/ ${MODELS_DIR}/` fails with "no such file or directory"

**Solution:** This is expected when `DOWNLOAD_MODELS=true` (default) and `models/` is in `.dockerignore`. The models are downloaded instead. If building with `DOWNLOAD_MODELS=false`, ensure:
1. `models/` directory exists with all required files
2. `models/` is NOT in `.dockerignore`

### Models not found at runtime

**Problem:** `FileNotFoundError: Transformer model file not found`

**Solution:**
- Check that models were either downloaded or copied successfully during build
- Verify the Docker build logs for "Downloading models from HuggingFace..." or "Copying models from local directory..."
- Ensure `MODELS_DIR` environment variable matches the build-time value

### VRAM usage too high

**Problem:** Container uses more than 13GB VRAM

**Solution:**
- The pipeline uses `enable_model_cpu_offload()` which should keep VRAM under 13GB
- Check that `enable_vae_slicing()` and `enable_attention_slicing()` are enabled in `handler.py`
- For GGUF models, avoid using `enable_sequential_cpu_offload()` as it's incompatible with quantized tensors

---

## File Structure

```
.
├── Dockerfile              # Main build file with DOWNLOAD_MODELS support
├── handler.py              # RunPod serverless handler (GGUF version)
├── download_models.py      # Model download utility
├── requirements.txt        # Python dependencies
├── .dockerignore          # Files to exclude from Docker context
├── BUILD_INSTRUCTIONS.md  # This file
└── models/                # Local models directory (for DOWNLOAD_MODELS=false)
    ├── diffusion_models/
    ├── text_encoders/
    └── loras/
```
