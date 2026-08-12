"""
Engine module for loading and running HealthGPT-Pro-8B locally via mlx-vlm.
Optimized for Apple Silicon with 4-bit quantized model.
"""
import os
import time
import logging
import warnings

# Suppress harmless docstring validation warnings from transformers for
# unrelated model processors (DeepseekVL, Kimi, PaddleOCR, etc.)
logging.getLogger("transformers").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", message=".*is part of.*not documented.*")

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
    temperature: float = 0.1,
) -> tuple[str, float, int]:
    """
    Analyzes a medical image using the loaded HealthGPT-Pro model.

    Strict generation parameters are enforced for clinical determinism:
    - temp=0.1: Near-zero temperature forces highly deterministic output
    - top_p=0.85: Restricts to high-probability medical vocabulary
    - repetition_penalty=1.15: Prevents finding repetition across sections

    Args:
        model: The loaded MLX model.
        processor: The loaded processor.
        config: The loaded model config (model.config).
        image_path: Path to the image file to analyze.
        prompt: The clinical prompt/query for the image.
        max_tokens: Maximum number of tokens to generate (default 2048).
        temperature: Sampling temperature (default 0.1 for clinical determinism).

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
            top_p=0.85,
            repetition_penalty=1.15,
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


def chat_followup(
    model,
    processor,
    config,
    chat_history: list,
    user_message: str,
    report_context: str = "",
    image_path: str = None,
    max_tokens: int = 1024,
    temperature: float = 0.15,
) -> tuple[str, float]:
    """
    Handles a follow-up question in the clinical copilot chat.
    Builds a multi-turn conversation with prior report context.

    Args:
        model: Loaded MLX model.
        processor: Loaded processor.
        config: Model config (model.config).
        chat_history: List of {"role": "user"|"assistant", "content": str} dicts.
        user_message: The new user question.
        report_context: The original report text for grounding.
        image_path: Optional image path for visual grounding.
        max_tokens: Max tokens to generate.
        temperature: Sampling temperature.

    Returns:
        Tuple of (response_text, inference_time).
    """
    # Build conversation with system context
    messages = []
    if report_context:
        system_msg = (
            "You are a board-certified radiologist assistant AI. "
            "You previously analyzed a medical image and generated the following report:\n\n"
            f"{report_context}\n\n"
            "Answer follow-up questions based on this report. "
            "Be precise, professional, and helpful. "
            "If asked to simplify, use patient-friendly language."
        )
        messages.append({"role": "system", "content": system_msg})

    # Add chat history
    for msg in chat_history:
        messages.append(msg)

    # Add new user message
    messages.append({"role": "user", "content": user_message})

    # Format with chat template
    num_images = 1 if image_path else 0
    formatted_prompt = apply_chat_template(
        processor, config, messages, num_images=num_images
    )

    import time
    start_time = time.time()
    try:
        kwargs = {
            "max_tokens": max_tokens,
            "temp": temperature,
            "top_p": 0.85,
            "repetition_penalty": 1.15,
        }
        if image_path and os.path.exists(image_path):
            result = generate(model, processor, formatted_prompt, image=[image_path], **kwargs)
        else:
            result = generate(model, processor, formatted_prompt, **kwargs)
    except Exception as e:
        return f"Error: {str(e)}", 0.0

    inference_time = time.time() - start_time
    response_text = result.text if hasattr(result, "text") else str(result)
    return response_text, inference_time


def get_memory_usage() -> str:
    """
    Returns the current process memory usage as a human-readable string.
    Uses macOS-native resource module.

    Returns:
        Memory usage string like '4.2 GB'.
    """
    try:
        import resource
        # ru_maxrss is in bytes on macOS
        mem_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        mem_gb = mem_bytes / (1024 ** 3)
        if mem_gb >= 1.0:
            return f"{mem_gb:.1f} GB"
        else:
            return f"{mem_gb * 1024:.0f} MB"
    except Exception:
        return "N/A"
