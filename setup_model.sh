#!/bin/bash
# ============================================
# Hack4Health — Model Setup Script
# Downloads and quantizes HealthGPT-Pro-8B
# for local offline inference on Apple Silicon
# ============================================

set -e

echo "========================================"
echo "  Hack4Health — Model Setup"
echo "========================================"
echo ""
echo "This script will:"
echo "  1. Download HealthGPT-Pro-8B from Hugging Face"
echo "  2. Quantize to 4-bit for Apple Silicon"
echo "  3. Save to ./models/HealthGPT-Pro-8B-4bit/"
echo ""
echo "Requirements: ~16GB disk space for download, ~5GB final"
echo "Requires internet connection (one-time only)"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed."
    exit 1
fi

# Check if mlx-vlm is installed
if ! python3 -c "import mlx_vlm" 2>/dev/null; then
    echo "ERROR: mlx-vlm is not installed."
    echo "Install it with: pip install mlx-vlm"
    exit 1
fi

# Create output directory
mkdir -p ./models

# Download and quantize
echo "Downloading and quantizing HealthGPT-Pro-8B..."
echo "This may take 15-30 minutes depending on your connection."
echo ""

python3 -m mlx_vlm convert \
    --hf-path lintw/HealthGPT-Pro-8B \
    --mlx-path ./models/HealthGPT-Pro-8B-4bit \
    -q

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo "Model saved to: ./models/HealthGPT-Pro-8B-4bit/"
echo "You can now run: streamlit run app.py"
echo "All subsequent runs will be 100% offline."
