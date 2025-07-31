#!/bin/bash
# ELYZA Model Download Script

echo "🚀 Downloading ELYZA-japanese-Llama-2-7b model..."
echo "This may take several minutes (file size: ~4.1GB)"

# Create directory if it doesn't exist
mkdir -p models/elyza7b

# Download the model file
cd models/elyza7b

# Option 1: Using wget
if command -v wget &> /dev/null; then
    echo "Using wget to download..."
    wget -O ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf \
        "https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf/resolve/main/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf"

# Option 2: Using curl
elif command -v curl &> /dev/null; then
    echo "Using curl to download..."
    curl -L -o ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf \
        "https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf/resolve/main/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf"

else
    echo "❌ Neither wget nor curl found. Please install one of them."
    echo "   macOS: brew install wget"
    echo "   Or download manually from:"
    echo "   https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf"
    exit 1
fi

# Verify download
if [ -f "ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf" ]; then
    file_size=$(du -h ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf | cut -f1)
    echo "✅ Download completed! File size: $file_size"
    echo "🎉 ELYZA model is ready to use!"
else
    echo "❌ Download failed. Please try again or download manually."
    exit 1
fi
