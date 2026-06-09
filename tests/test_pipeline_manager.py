from core.app_state import AppState
from core.pipeline_manager import PipelineManager


class FakeMemory:
    def __init__(self) -> None:
        self.cleared = False

    def clear(self) -> None:
        self.cleared = True


class FakePipeline:
    def __init__(self, *, memory: FakeMemory | None = None) -> None:
        self.memory = memory
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True
        if self.memory is not None:
            self.memory.clear()


def test_pipeline_manager_prevents_ocr_and_asr_from_running_together() -> None:
    manager = PipelineManager()
    ocr_pipeline = FakePipeline()
    asr_pipeline = FakePipeline()

    assert manager.start_ocr(ocr_pipeline) is True
    assert manager.state is AppState.OCR_RUNNING

    assert manager.start_asr(asr_pipeline) is False
    assert asr_pipeline.started is False
    assert manager.state is AppState.OCR_RUNNING


def test_pipeline_manager_stop_returns_to_idle_and_clears_active_memory() -> None:
    memory = FakeMemory()
    manager = PipelineManager()
    pipeline = FakePipeline(memory=memory)

    assert manager.start_asr(pipeline) is True
    assert manager.state is AppState.ASR_RUNNING

    assert manager.stop_active() is True

    assert pipeline.stopped is True
    assert memory.cleared is True
    assert manager.state is AppState.IDLE
    assert manager.active_mode is None


def test_pipeline_manager_rejects_same_mode_restart_while_active() -> None:
    manager = PipelineManager()
    first_pipeline = FakePipeline()
    second_pipeline = FakePipeline()

    assert manager.start_ocr(first_pipeline) is True
    assert manager.start_ocr(second_pipeline) is False

    assert first_pipeline.started is True
    assert second_pipeline.started is False
