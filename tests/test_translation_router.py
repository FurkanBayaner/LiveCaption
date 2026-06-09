from translation.model_registry import TranslationModelSpec
from translation.translation_router import TranslationRouter


class FakeBackend:
    def __init__(self, model_spec: TranslationModelSpec) -> None:
        self.model_spec = model_spec
        self.loaded = False
        self.unloaded = False
        self.translations: list[tuple[str, str]] = []

    @property
    def is_loaded(self) -> bool:
        return self.loaded

    def is_available(self) -> bool:
        return True

    def load(self) -> None:
        self.loaded = True

    def unload(self) -> None:
        self.unloaded = True
        self.loaded = False

    def translate(self, text: str, context: str | None = None) -> str:
        context = context or ""
        self.translations.append((text, context))
        return f"{self.model_spec.display_name}: {text} [{context}]"


def test_translation_router_switches_engines_and_uses_context() -> None:
    created: list[FakeBackend] = []

    def backend_factory(model_spec: TranslationModelSpec) -> FakeBackend:
        backend = FakeBackend(model_spec)
        created.append(backend)
        return backend

    router = TranslationRouter(backend_factory=backend_factory)

    assert router.active_engine_name == "Qwen3 1.7B"
    assert router.switch_engine("MarianMT") is True
    assert router.active_engine_name == "MarianMT"
    assert created[-1].loaded is True

    result = router.translate("hello", ["previous", "line"])

    assert result == "MarianMT: hello [previous\nline]"
    assert created[-1].translations == [("hello", "previous\nline")]


def test_translation_router_unloads_previous_backend_on_switch() -> None:
    created: list[FakeBackend] = []

    def backend_factory(model_spec: TranslationModelSpec) -> FakeBackend:
        backend = FakeBackend(model_spec)
        created.append(backend)
        return backend

    router = TranslationRouter(backend_factory=backend_factory)

    assert router.switch_engine("MarianMT") is True
    first_backend = created[-1]
    assert router.switch_engine("Gemma 3 1B") is True

    assert first_backend.unloaded is True
    assert created[-1].model_spec.display_name == "Gemma 3 1B"
