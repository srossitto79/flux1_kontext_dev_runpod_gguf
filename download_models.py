"""
Model download utility for FLUX.1-Kontext with GGUF quantization.
This script downloads the necessary model files for Flux Kontext and can be run during Docker build.
"""
import os
from huggingface_hub import snapshot_download, hf_hub_download


def assure_pipeline_files(model_id: str = "black-forest-labs/FLUX.1-Kontext-Dev", cache_dir: str = None):
    """
    Download only the small config files from the HF repo for Flux Kontext.
    Avoids downloading large model weights since we use local GGUF files.

    Args:
        model_id: HuggingFace model ID (default: "black-forest-labs/FLUX.1-Kontext-Dev")
        cache_dir: Optional cache directory for downloads
    """
    print(f"Downloading pipeline config files from {model_id}...")

    allow = [
        "model_index.json",
        "scheduler/*",
        "scheduler/**",
        "vae/*",
        "vae/**",
        "tokenizer/*",
        "tokenizer/**",
        "image_processor/*",
        "image_processor/**",
        "processor/*",
        "processor/**",
        "text_encoder/*",
        "text_encoder/**",
        "text_encoder_2/*",
        "text_encoder_2/**",
        "*.json",
        "*.txt",
    ]

    snapshot_download(
        repo_id=model_id,
        repo_type="model",
        allow_patterns=allow,
        local_dir_use_symlinks=False,
        cache_dir=cache_dir,
    )
    print(f"Pipeline config files downloaded successfully")


def download_flux_gguf(
    output_path: str,
    repo_id: str = "QuantStack/FLUX.1-Kontext-dev-GGUF",
    filename: str = "flux1-kontext-dev-Q5_K_M.gguf"
):
    """
    Download GGUF quantized Flux Kontext model.

    URL: https://huggingface.co/QuantStack/FLUX.1-Kontext-dev-GGUF/resolve/main/flux1-kontext-dev-Q5_K_M.gguf

    Args:
        output_path: Where to save the downloaded file
        repo_id: HuggingFace repo ID
        filename: Filename in the repo
    """
    if os.path.exists(output_path):
        print(f"✓ Flux Kontext GGUF already exists at {output_path}, skipping download")
        return output_path

    print(f"Downloading Flux Kontext GGUF from {repo_id}/{filename}...")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    downloaded_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=os.path.dirname(output_path),
        local_dir_use_symlinks=False
    )

    print(f"✓ Flux Kontext GGUF downloaded to {downloaded_path}")
    return downloaded_path





def download_all_models(models_dir: str = "./models"):
    """
    Download all required models for the FLUX.1-Kontext pipeline.
    Skips files that already exist (e.g., from local copies or symlinks).
    Always ensures pipeline config files are present.

    Args:
        models_dir: Base directory for storing models
    """
    print(f"\n{'='*60}")
    print(f"Ensuring models are present in {models_dir}")
    print(f"{'='*60}\n")

    # Set HuggingFace cache directories to models_dir
    os.environ["HF_HOME"] = models_dir
    os.environ["HUGGINGFACE_HUB_CACHE"] = models_dir
    os.environ["TRANSFORMERS_CACHE"] = models_dir

    # Always download pipeline configs (small files, ensures correct setup)
    print("1. Ensuring pipeline config files...")
    assure_pipeline_files(cache_dir=models_dir)

    # Download Flux Kontext GGUF (skips if exists)
    print("\n2. Checking Flux Kontext GGUF model...")
    flux_gguf_path = os.path.join(models_dir, "diffusion_models", "flux1-kontext-dev-Q5_K_M.gguf")
    download_flux_gguf(flux_gguf_path)

    print(f"\n{'='*60}")
    print(f"✓ All models ready!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import sys

    models_dir = sys.argv[1] if len(sys.argv) > 1 else "./models"
    download_all_models(models_dir)
