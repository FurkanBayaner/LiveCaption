from ocr.ocr_memory import OCRMemory


def test_ocr_memory_filters_empty_duplicates_and_clears() -> None:
    memory = OCRMemory(max_items=3)

    assert memory.add_if_new("") is False
    assert memory.add_if_new("  hello   world  ") is True
    assert memory.add_if_new("hello world") is False
    assert memory.add_if_new("next line") is True

    assert memory.items == ("hello world", "next line")

    memory.clear()

    assert memory.items == ()
