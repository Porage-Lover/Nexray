"""
Engine module for loading and running HealthGPT-Pro-8B locally via mlx-vlm.
Optimized for Apple Silicon with 4-bit quantized model.
"""
import os
import time
import streamlit as st
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template


DEFAULT_MODEL_PATH = "./models/HealthGPT-Pro-8B-4bit"


def load_model(model_path: str = DEFAULT_MODEL_PATH) -> tuple:
    """
    Loads the HealthGPT-Pro-8B model and its processor from a local directory.

    Args:
        model_path: The local path to the quantized model directory.

    Returns:
        A tuple of (model, processor, config).

    Raises:
        FileNotFoundError: If the model path does not exist.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at '{model_path}'.\n"
            "Please run the setup script to download and quantize the model:\n"
            "  chmod +x setup_model.sh && ./setup_model.sh\n\n"
            "This requires a one-time internet connection (~16GB download)."
        )

    print(f"[Hack4Health] Loading model from {model_path}...")
    model, processor = load(model_path)
    # Use model.config (not load_config) to match the mlx-vlm CLI pattern.
    # model.config contains the runtime config that apply_chat_template expects.
    config = model.config
    print("[Hack4Health] Model loaded successfully.")

    return model, processor, config


@st.cache_resource
def get_model():
    """
    Cached wrapper that loads the model once per Streamlit session.
    Subsequent calls return the cached model without reloading.

    Returns:
        A tuple of (model, processor, config).
    """
    return load_model()


def analyze_image(
    model,
    processor,
    config,
    image_path: str,
    prompt: str,
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> tuple[str, float, int]:
    """
    Analyzes a medical image using the loaded HealthGPT-Pro model.

    Args:
        model: The loaded MLX model.
        processor: The loaded processor.
        config: The loaded model config (model.config).
        image_path: Path to the image file to analyze.
        prompt: The clinical prompt/query for the image.
        max_tokens: Maximum number of tokens to generate (default 2048).
        temperature: Sampling temperature (default 0.3 for clinical accuracy).

    Returns:
        A tuple of (response_text, inference_time_seconds, token_count).
    """
    if not os.path.exists(image_path):
        return f"Error: Image not found at '{image_path}'", 0.0, 0

    # Format the prompt using the model's chat template
    formatted_prompt = apply_chat_template(processor, config, prompt, num_images=1)

    # Run inference and measure time
    start_time = time.time()
    try:
        result = generate(
            model,
            processor,
            formatted_prompt,
            image=[image_path],  # Must be a list of paths, not a bare string
            max_tokens=max_tokens,
            temp=temperature,
        )
    except Exception as e:
        return f"Error during model inference: {str(e)}", 0.0, 0

    inference_time = time.time() - start_time

    # Extract text and token count from GenerationResult
    response_text = result.text if hasattr(result, "text") else str(result)
    token_count = (
        result.generation_tokens
        if hasattr(result, "generation_tokens")
        else len(response_text.split())
    )

    return response_text, inference_time, token_count
