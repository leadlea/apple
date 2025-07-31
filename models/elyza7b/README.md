# ELYZA Model Directory

This directory should contain the ELYZA-japanese-Llama-2-7b model file.

## Required Model File

Download the following model file and place it in this directory:

**File:** `ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf`

**Download Sources:**
- Hugging Face: https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf
- Direct download: https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf/resolve/main/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf

## Download Instructions

### Option 1: Using wget
```bash
cd models/elyza7b
wget https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf/resolve/main/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf
```

### Option 2: Using curl
```bash
cd models/elyza7b
curl -L -o ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf/resolve/main/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf
```

### Option 3: Using Hugging Face Hub
```bash
pip install huggingface_hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf', filename='ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf', local_dir='models/elyza7b')"
```

## Model Information

- **Model Size:** ~4.1GB (Q4_0 quantization)
- **Context Length:** 2048 tokens
- **Language:** Japanese
- **Base Model:** Llama 2 7B
- **Optimization:** Quantized for efficient inference

## M1 Mac Optimization

This model is optimized for Apple M1/M2 chips using:
- Metal GPU acceleration via llama-cpp-python
- Optimized memory mapping
- Efficient batch processing

## Verification

After downloading, verify the file:
```bash
ls -la models/elyza7b/
# Should show: ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf (~4.1GB)
```

## Troubleshooting

If you encounter issues:
1. Ensure you have sufficient disk space (~5GB free)
2. Check your internet connection for large file downloads
3. Verify the file integrity after download
4. Make sure the filename matches exactly: `ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf`