LiveCaption/
├── main.py
├── config.py
├── logging_config.py
├── requirements.txt
├── .gitignore
│
├── core/
│   ├── __init__.py
│   ├── app_state.py
│   ├── pipeline_manager.py
│   ├── signals.py
│   └── types.py
│
├── ocr/
│   ├── __init__.py
│   ├── screen_capture.py
│   ├── ocr_engine.py
│   ├── ocr_pipeline.py
│   └── ocr_memory.py
│
├── asr/
│   ├── __init__.py
│   ├── audio_capture.py
│   ├── vad_engine.py
│   ├── asr_engine.py
│   ├── asr_pipeline.py
│   └── asr_memory.py
│
├── translation/
│   ├── __init__.py
│   ├── model_registry.py
│   ├── llm_engine.py
│   ├── marian_engine.py
│   ├── translation_router.py
│   └── translation_memory.py
│
├── ui/
│   ├── __init__.py
│   ├── control_panel.py
│   ├── overlay_base.py
│   ├── selection_base.py
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── ocr_selection_screen.py
│   │   └── ocr_overlay.py
│   ├── asr/
│   │   ├── __init__.py
│   │   ├── asr_selection_screen.py
│   │   └── asr_overlay.py
│   └── styles/
│       └── theme.qss
│
├── models/
│   ├── whisper/
│   └── translation/
│       ├── llm/
│       └── marian/
│
├── logs/
│   └── .gitkeep
│
└── tests/
    ├── test_ocr_memory.py
    ├── test_asr_memory.py
    ├── test_translation_router.py
    └── test_pipeline_manager.py

**Root Files**
main.py: The single entry point of the application. Creates the QApplication, loads config.py, initializes the logging system, and starts the pipeline_manager and control_panel. Contains no business logic; only wires components together.

config.py: Stores constant settings and default values. FPS, model paths, VAD threshold, Whisper model, default font, colors, overlay settings, and translation engine options are loaded from here.

logging_config.py: Configures log formatting, log levels, and writing behavior for logs/app.log. Standardizes pipeline errors, model loading durations, OCR/ASR latency logs, and unexpected exception handling.

requirements.txt: Contains pinned Python dependencies for the project. Especially numpy==1.26.4 and opencv-python==4.11.0.86 must remain fixed.

.gitignore: Prevents models/, logs/*.log, __pycache__/, virtual environments, and temporary files from being committed to git.

**Core**
core/app_state.py: Stores the central application state. States such as idle, ocr_running, asr_running, and loading_model are defined here.

core/pipeline_manager.py: The main controller that guarantees OCR and ASR pipelines cannot run simultaneously. Receives start/stop signals from the UI, launches the correct pipeline, locks the other mode, and clears memories during stop operations.

core/signals.py: Contains shared PyQt signal definitions. Standardizes communication between the control panel, overlays, and pipelines.

core/types.py: Defines shared data structures. Screen coordinates, overlay settings, color selections, and active pipeline modes are represented here.

**OCR**
ocr/screen_capture.py: Captures the selected screen region using dxcam. Converts frames into OCR-ready RGBA format and scales them according to SCREEN_SCALE.

ocr/ocr_engine.py: Wraps the Windows.Media.Ocr engine. Receives RGBA images and returns plain text OCR results.

ocr/ocr_pipeline.py: Manages the OCR workflow. Captures screen frames, runs OCR, filters duplicate or empty text, stores memory entries, sends text to translation, and updates the OCR overlay.

ocr/ocr_memory.py: Stores recent OCR texts using FIFO logic. Prevents repeated duplicate entries and provides context for translation.

**ASR**
asr/audio_capture.py: Captures system audio through WASAPI loopback using pyaudiowpatch. Listens to computer output audio instead of the microphone.

asr/vad_engine.py: Detects speech segments using Silero VAD. Prevents music, sound effects, or silence from being processed by Whisper.

asr/asr_engine.py: Wraps the faster-whisper model. Converts speech segments into English transcripts.

asr/asr_pipeline.py: Manages the ASR workflow. Runs audio capture, VAD, Whisper transcription, memory updates, translation, and ASR overlay updates sequentially.

asr/asr_memory.py: Stores recent ASR transcripts. Used for Whisper initial_prompt generation and translation context.

**Translation**
translation/model_registry.py: Centrally defines supported translation engines. Stores model names, engine types, local model paths, and default engine information.

translation/llm_engine.py: Manages LLM-based translation models such as Qwen, Gemma, and Llama. Handles model loading, unloading, INT8 quantization, and prompt formatting.

translation/marian_engine.py: Handles MarianMT-based fast CPU translation. Provides lower VRAM usage compared to LLMs but with less contextual awareness.

translation/translation_router.py: Selects the active translation engine and routes text to the correct backend. Unloads previous models and loads new ones during engine switching.

translation/translation_memory.py: Converts OCR or ASR history into context formats suitable for translation models. Does not store raw memory directly; acts as a context preparation layer.

**UI**
ui/control_panel.py: The main control window. Contains controls for font, colors, letter spacing, line spacing, translation engine selection, background transparency, and OCR/ASR start-stop actions.

ui/overlay_base.py: Shared technical foundation for OCR and ASR overlays. Handles transparent windows, always-on-top behavior, click-through support, DPI correction, and text rendering.

ui/selection_base.py: Shared foundation for OCR and ASR selection screens. Handles fullscreen dimming, mouse dragging, selection box rendering, and confirm/cancel behavior.

ui/ocr/ocr_selection_screen.py: Allows the user to select the subtitle region for OCR. Automatically places the translation overlay above the selected subtitle box.

ui/ocr/ocr_overlay.py: Displays OCR translations on screen. Uses overlay_base.py infrastructure while implementing OCR-specific positioning and update behavior.

ui/asr/asr_selection_screen.py: Allows the user to select only the translation overlay area for ASR. Does not include subtitle region selection because no on-screen text is read.

ui/asr/asr_overlay.py: Displays ASR translations on screen. Technically based on the same overlay foundation as OCR but receives text from the ASR pipeline.

ui/styles/theme.qss: Visual style configuration for the control panel and selection screens. Manages colors, buttons, comboboxes, sliders, and disabled states.

**Runtime Files**
models/: Local cache directory for Whisper, LLM, and Marian model files. Contains large assets and should not be committed to git.

logs/: Stores runtime log files. app.log is generated during execution; only .gitkeep is included in the repository to preserve the folder structure.

tests/: Contains tests for small but critical behaviors. Includes memory duplicate filtering, router engine switching, and pipeline manager state transition tests.
