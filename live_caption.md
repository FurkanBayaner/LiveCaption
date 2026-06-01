## LIVE CAPTION ##

# HARDWARE
Graphics Card: Nvidia GeForce RTX 5070 Laptop GPU 8GB VRAM
Processor: AMD Ryzen 7 AI
Monitor: 2560x1440 QHD 165Hz (The project will be specifically optimized for this setup)
Python: 3.11.9

# TECHNOLOGY
Screen Capture: dxcam
Audio Capture: pyaudiowpatch
Image Processing: opencv-python, numpy
Voice Activity Detection: silero-vad, onnxruntime-gpu
OCR Engine: Windows.Media.Ocr
ASR Engine: faster-whisper (Using CTranslate2 infrastructure)
Translation: Qwen3 1.7B, Qwen3.5 2B, Gemma 2 2B, Qwen2.5 Coder 1.5B, Gemma 3 1B, Llama 3.2 1B, MarianMT (Helsinki-NLP/opus-mt-en-tr)
ML Backend: torch (CUDA), transformers, huggingface-hub, bitsandbytes, accelerate
GUI Layer: PyQt5

# VERSIONS
numpy==1.26.4 (CRITICAL: numpy 2.x conflicts with dxcam/OpenCV; version 1.26.x must strictly be used)
opencv-python==4.11.0.86 (CRITICAL: opencv 4.12+ requires numpy>=2; version 4.11.x must strictly be used)
dxcam==0.0.5
PyQt5==5.15.11
winrt-runtime==3.2.1
winrt-Windows.Media.Ocr==3.2.1
pyaudiowpatch==0.2.12.8
silero-vad==6.2.1
onnxruntime-gpu==1.21.1
ctranslate2==4.7.1
faster-whisper==1.2.1
transformers==4.51.3
huggingface-hub==0.31.4
bitsandbytes==0.45.5
accelerate==1.6.0
# All LLM translation models run in INT8 quantization (load_in_8bit=True)
# VRAM breakdown: faster-whisper medium ~3.0GB + LLM int8 max ~3.1GB + VAD ~0.1GB = ~6.2GB / 8GB
# Required by bitsandbytes for device_map="auto" support
