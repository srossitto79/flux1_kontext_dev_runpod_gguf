import base64
import io
import os
import time
from typing import Any, Dict
import runpod
from PIL import Image
import torch
from diffusers import FluxKontextPipeline, FluxTransformer2DModel, GGUFQuantizationConfig

# Set up model paths and config for Flux Kontext
MODELS_DIR = os.getenv("MODELS_DIR", "./models")
FLUX_MODEL_PATH = os.path.join(MODELS_DIR, "diffusion_models", "flux1-kontext-dev-Q5_K_M.gguf")
DEFAULT_STEPS = int(os.getenv("DEFAULT_STEPS", "20"))
DEFAULT_SCALE = float(os.getenv("DEFAULT_SCALE", "3.5"))

if not os.path.exists(FLUX_MODEL_PATH):
    raise FileNotFoundError(f"Flux Kontext GGUF model file not found at {FLUX_MODEL_PATH}")


def load_flux_pipeline():
    """
    Load Flux Kontext pipeline from GGUF model file.
    """
    print("Loading Flux Kontext pipeline from GGUF file...")
    transformer = FluxTransformer2DModel.from_single_file(
        FLUX_MODEL_PATH,
        quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
        torch_dtype=torch.bfloat16,
        local_files_only=True,    
        config="black-forest-labs/FLUX.1-Kontext-Dev",
        subfolder="transformer"       
    )
    pipe = FluxKontextPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-Kontext-Dev",
        transformer=transformer,
        torch_dtype=torch.bfloat16,
        cache_dir=MODELS_DIR,        
        local_files_only=True,
        #device_map="balanced"
    )        
    #pipe.to("cuda")
    #pipe.enable_attention_slicing()
    #pipe.enable_sequential_cpu_offload()
    pipe.enable_model_cpu_offload()
    pipe.set_progress_bar_config(disable=None)
    return pipe

def round_to_multiple(x, base=64):
    return base * round(x / base)

def read_image(source: str) -> Image.Image:
    # If it's a URL, let PIL load it; supports http(s)
    if source.startswith("http://") or source.startswith("https://"):
        import requests
        response = requests.get(source)
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
        return img
    
    # If it's base64 (optionally data URL)
    if source.startswith("data:image"):
        base64_str = source.split(",", 1)[1]
    else:
        base64_str = source
    try:
        data = base64.b64decode(base64_str)
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return img
    except Exception as e:
        raise ValueError(f"Failed to decode image input: {e}")


def encode_image(img: Image.Image, format: str = "PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=format)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


## Manual offload logic not needed for Flux Kontext pipeline
    
def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    inp = job.get("input") or {}
    image_in = inp.get("image")
    prompt = inp.get("prompt")
    negative_prompt = inp.get("negative_prompt", "")
    num_inference_steps = int(inp.get("num_inference_steps", DEFAULT_STEPS))
    guidance_scale = float(inp.get("guidance_scale", DEFAULT_SCALE))
    width = inp.get("width")
    height = inp.get("height")

    if not image_in or not prompt:
        return {"error": "Missing required fields: image, prompt"}

    start_time = time.time()

    print("Loading Flux Kontext pipeline...")
    pipe = load_flux_pipeline()

    print("Reading input image...")
    image = read_image(image_in)

    kwargs = {
        "image": image,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
    }
    if width:
        kwargs["width"] = int(width)
    if height:
        kwargs["height"] = int(height)

    print(f"Pipeline loading time: {time.time() - start_time:.2f} seconds")
    print("Generating image...")

    torch.cuda.empty_cache()
    out = pipe(**kwargs)
    out_img = out.images[0]
    b64 = encode_image(out_img)
    print(f"Total processing time: {time.time() - start_time:.2f} seconds")

    return {"image_base64": b64}

if __name__ == "__main__":
    if os.getenv("RUNPOD_LOCAL_TEST"):
        from fastapi import FastAPI
        import uvicorn

        app = FastAPI()

        @app.post("/")
        async def run_job(job: dict):
            return handler(job)

        port = int(os.getenv("RP_PORT", "3000"))
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # Start runpod serverless handler
        runpod.serverless.start({"handler": handler})
