from asr.asr_memory import ASRMemory


def test_asr_memory_filters_duplicates_builds_prompt_and_clears() -> None:
    memory = ASRMemory(max_items=3)

    assert memory.add_if_new(" ") is False
    assert memory.add_if_new(" first   transcript ") is True
    assert memory.add_if_new("first transcript") is False
    assert memory.add_if_new("second transcript") is True
    assert memory.add_if_new("third transcript") is True
    assert memory.add_if_new("fourth transcript") is True

    assert memory.items == (
        "second transcript",
        "third transcript",
        "fourth transcript",
    )
    assert memory.initial_prompt(max_items=2) == "third transcript fourth transcript"

    memory.clear()

    assert memory.items == ()
    assert memory.initial_prompt() == ""
