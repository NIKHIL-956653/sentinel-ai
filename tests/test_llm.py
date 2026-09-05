import pytest

from tools import llm


@pytest.mark.parametrize("raw,expected", [
    ('```json\n[{"a":1}]\n```', '[{"a":1}]'),
    ('```\n{"b":2}\n```', '{"b":2}'),
    ('Sure! ```json\n[1,2]``` hope this helps', '[1,2]'),
    ('[3]', '[3]'),
    ('  {"x": 1}  ', '{"x": 1}'),
])
def test_strip_fences(raw, expected):
    assert llm.strip_fences(raw) == expected


def test_chat_json_raises_llmerror_on_non_json(monkeypatch):
    monkeypatch.setattr(llm, "chat", lambda *a, **k: "I cannot answer that.")
    with pytest.raises(llm.LLMError):
        llm.chat_json("p")


def test_chat_without_key_raises(monkeypatch):
    monkeypatch.setattr(llm, "OPENROUTER_API_KEY", "")
    with pytest.raises(llm.LLMError):
        llm.chat("p")
