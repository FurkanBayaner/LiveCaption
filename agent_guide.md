# Agent Guide

This document is intended to help new AI agents quickly understand the LiveCaption project boundaries, git rules, GitHub target, and technical documentation sources within this workspace. Before making any changes, run `git status --short` in the repository root.

## Workspace Map

Workspace and repository root:

```text
C:\Users\furka\OneDrive\Desktop\LiveCaption
```

Active project:

| Project     | Location                                      | Git Root | GitHub                      |
| :---------- | :-------------------------------------------- | :------- | :-------------------------- |
| LiveCaption | `C:\Users\furka\OneDrive\Desktop\LiveCaption` | `.git`   | `FurkanBayaner/LiveCaption` |

Remote:

```text
https://github.com/FurkanBayaner/LiveCaption.git
```

Important: The only authorized project in this workspace is LiveCaption. Commit, diff, status, log, issue, PR, and workflow operations must never target any other repository.

## Commit Boundaries

* All commits must be made only to the `FurkanBayaner/LiveCaption` repository.
* Do not create commits unless the user explicitly requests it.
* If a commit is requested, first run `git status --short` in the repository root and separate user/agent-unrelated changes.
* Stage only files related to the current task.
* Do not clean, revert, or include unrelated dirty-state files in commits.
* Never revert user or previous-agent changes without explicit permission.
* Large model files, runtime logs, cache files, and virtual environments must never be committed.

## GitHub and Issue Boundaries

Authorized GitHub repository:

```text
FurkanBayaner/LiveCaption
```

* GitHub CLI (`gh`) commands may only be used for `FurkanBayaner/LiveCaption`.
* Read-only `gh` commands may be executed without additional user approval. Listing/viewing issues, milestones, labels, runs, and logs are considered read-only.
* Mutating `gh` commands require explicit user approval before execution.
* Creating/updating/closing/rerunning issues, milestones, labels, PRs, workflows, releases, or repository settings are considered mutating actions.
* When creating issues, include related commit SHAs, documentation files, or technical decision references whenever possible.
* Never perform issue, PR, workflow, release, or repository-setting actions on any other GitHub repository.

## Project Overview

LiveCaption is a Python-based live subtitle and translation application for Windows. The application supports two main modes:

* OCR mode: Reads subtitle regions from the screen, translates the text, and displays it as an overlay.
* ASR mode: Captures system audio using WASAPI loopback, converts speech to text, translates it, and displays it as an overlay.

OCR and ASR must never run at the same time. This rule is centrally enforced in `core/pipeline_manager.py`.

## Technology and Runtime

* Python 3.11.9
* GUI: PyQt5
* Screen capture: dxcam
* Audio capture: pyaudiowpatch
* Image processing: opencv-python, numpy
* OCR engine: Windows.Media.Ocr
* Voice activity detection: silero-vad, onnxruntime-gpu
* ASR engine: faster-whisper, CTranslate2
* Translation: MarianMT and INT8 LLM models
* ML backend: torch CUDA, transformers, huggingface-hub, bitsandbytes, accelerate

Target hardware:

* Nvidia GeForce RTX 5070 Laptop GPU, 8GB VRAM
* AMD Ryzen 7 AI
* 2560x1440 QHD 165Hz monitor

## Critical Dependency Rules

* `numpy==1.26.4` must be preserved. NumPy 2.x may break dxcam/OpenCV compatibility.
* `opencv-python==4.11.0.86` must be preserved. OpenCV 4.12+ may require NumPy 2.x.
* LLM translation models operate with INT8 quantization.
* Only one LLM may remain loaded in VRAM at a time.
* `models/` is a large local model cache directory and must never be committed.
* `logs/*.log`, runtime logs, `__pycache__/`, virtual environments, and temporary files must never be committed.

## Documentation Sources

Before making code or architecture decisions, read the relevant documentation:

* `live_caption.md`: hardware, technologies, dependency rules, and VRAM decisions
* `project_structure.md`: target folder structure and module responsibilities
* `system_pipeline.md`: OCR, ASR, stop flow, and translation router rules
* `ui_design_spec.md`: PyQt5 control panel, selection screens, overlays, and style rules

These documents are considered the project memory. If your code changes affect documented architectural decisions, evaluate whether the related documentation should also be updated.

## Target Project Structure

Expected main structure:

```text
LiveCaption/
  main.py
  config.py
  logging_config.py
  requirements.txt
  core/
    pipeline_manager.py
  ocr/
  asr/
  translation/
  ui/
  models/
  logs/
  tests/
```

Core responsibilities:

* `main.py`: Application entry point; must not contain business logic.
* `config.py`: Constants and default settings.
* `core/pipeline_manager.py`: Manages OCR/ASR startup, shutdown, state, and locking decisions.
* `ocr/`: Screen capture, OCR engine, OCR pipeline, and OCR memory.
* `asr/`: Audio capture, VAD, Whisper ASR, ASR pipeline, and ASR memory.
* `translation/`: Model registry, LLM, MarianMT, router, and context preparation.
* `ui/`: PyQt5 control panel, selection screen, overlays, and QSS styles.

## Pipeline Rules

* OCR and ASR must never run simultaneously.
* The UI must not make decisions; it only sends signals/events.
* Start, stop, state, and mode-locking decisions must remain inside `core/pipeline_manager.py`.
* In OCR mode, the user selects the subtitle region; the translation overlay region is automatically created above it.
* In ASR mode, the user selects only the translation overlay region.
* OCR and ASR must use separate memory systems.
* The translation router must not need to know whether text came from OCR or ASR.
* When the pipeline stops, the related memory must be cleared, overlays closed, and state set to `idle`.
* The translation engine may remain loaded in memory; it does not need to reload after every stop.
* Pipeline failures must not terminate the entire application; errors should be logged and the flow should continue in a controlled manner whenever possible.

## UI and Design Rules

* Read `ui_design_spec.md` before making PyQt5 UI decisions.
* Style changes should be made inside `ui/styles/theme.qss` whenever possible.
* `.py` files should only contain behavior or required widget logic changes.
* The control panel must preserve its fixed-size layout, dark theme, and two-column settings structure.
* Overlay windows must preserve frameless, always-on-top, transparent, and click-through behavior.
* 2K DPI drift fixes based on `QScreen.devicePixelRatio()` must be preserved.
* Overlay settings must apply instantly without restarting the active pipeline.
* While OCR is running, `START ASR` must be disabled; while ASR is running, `START OCR` must be disabled.
* The selection screen confirm/cancel flow must remain intact.

## Workflow

1. Run `git status --short` in the repository root.
2. Read the documentation related to the current task.
3. Make minimal, testable changes that align with the existing architecture.
4. Preserve dependency pins, model cache rules, and the OCR/ASR mutual exclusion rule.
5. If code changes were made, run the appropriate checks:

```text
python -m pytest
```

Run any additional project-defined lint/check commands if necessary.

6. If documentation was modified, use `rg` to ensure no outdated project references or inconsistent naming remain.
7. If a commit is requested, stage only task-related changes and use a commit message scoped to LiveCaption.

## Agent and Subagent Usage

* The main Codex agent acts as the leader/reviewer.
* Subagent output must never be accepted blindly; architecture compatibility, scope, tests, documentation, and git diffs must be reviewed by the main agent.
* If the user requests subagents or the task is highly segmented, divide work into limited and clearly defined subtasks.
* By default, economical models and medium reasoning are sufficient; stronger models should only be used when genuinely necessary.
* Final architecture, scope, and quality decisions remain the responsibility of the main agent.

## Common Mistakes

* Using AGENTS files, roadmaps, or GitHub rules from unrelated projects.
* Creating issues, PRs, or commits in the wrong GitHub repository.
* Creating commits without explicit user approval.
* Reverting user or previous-agent changes without permission.
* Committing large model files, runtime logs, or cache directories.
* Breaking `numpy` or `opencv-python` dependency pins.
* Adding flows that allow OCR and ASR to run simultaneously.
* Changing Python behavior code unnecessarily for UI styling.
* Designing overlay settings that require pipeline restarts.
