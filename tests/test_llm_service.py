"""Unit tests for LLM provider selection and Gemini/OpenAI chat helpers."""

from unittest.mock import MagicMock, patch

from app.services.llm_service import LLMService


def test_provider_none_without_keys(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    monkeypatch.delenv('LLM_PROVIDER', raising=False)
    assert LLMService.provider() is None
    assert LLMService.is_configured() is False


def test_provider_prefers_gemini_when_both_set(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test')
    monkeypatch.setenv('GEMINI_API_KEY', 'gem-test')
    monkeypatch.delenv('LLM_PROVIDER', raising=False)
    assert LLMService.provider() == 'gemini'


def test_provider_openai_when_only_openai(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test')
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    monkeypatch.delenv('LLM_PROVIDER', raising=False)
    assert LLMService.provider() == 'openai'


def test_provider_forced_openai(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test')
    monkeypatch.setenv('GEMINI_API_KEY', 'gem-test')
    assert LLMService.provider() == 'openai'


def test_google_api_key_alias(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.setenv('GOOGLE_API_KEY', 'google-studio-key')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('LLM_PROVIDER', raising=False)
    assert LLMService.provider() == 'gemini'


def test_retired_gemini_model_alias(monkeypatch):
    monkeypatch.setenv('GEMINI_MODEL', 'gemini-1.5-flash')
    models = LLMService._resolve_gemini_models()
    assert models[0] == 'gemini-3.5-flash'


@patch('requests.post')
def test_gemini_chat_parses_response(mock_post, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'gem-test')
    monkeypatch.setenv('GEMINI_MODEL', 'gemini-3.5-flash')
    mock_post.return_value = MagicMock(
        status_code=200,
        ok=True,
        text='{}',
        json=lambda: {
            'candidates': [
                {'content': {'parts': [{'text': 'Rephrased bullet with Python'}]}}
            ]
        },
    )
    text = LLMService._gemini_chat([{'role': 'user', 'content': 'hello'}])
    assert 'Python' in text
    args, kwargs = mock_post.call_args
    assert 'generativelanguage.googleapis.com' in args[0]
    assert 'gemini-3.5-flash' in args[0]
    assert kwargs['headers']['x-goog-api-key'] == 'gem-test'
    assert 'params' not in kwargs or not kwargs.get('params')
    assert kwargs['json']['generationConfig']['temperature'] == 0.2


@patch('requests.post')
def test_gemini_falls_back_on_404(mock_post, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'gem-test')
    monkeypatch.setenv('GEMINI_MODEL', 'gemini-3.5-flash')

    not_found = MagicMock(status_code=404, ok=False, text='not found')
    ok = MagicMock(
        status_code=200,
        ok=True,
        text='{}',
        json=lambda: {
            'candidates': [{'content': {'parts': [{'text': 'fallback ok'}]}}]
        },
    )
    mock_post.side_effect = [not_found, ok]
    text = LLMService._gemini_chat([{'role': 'user', 'content': 'hello'}])
    assert text == 'fallback ok'
    assert mock_post.call_count == 2


@patch('requests.post')
def test_gemini_429_raises_clear_error(mock_post, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'gem-test')
    monkeypatch.setenv('GEMINI_MODEL', 'gemini-3.5-flash')
    mock_post.return_value = MagicMock(status_code=429, ok=False, text='quota')
    try:
        LLMService._gemini_chat([{'role': 'user', 'content': 'hello'}])
        assert False, 'expected RuntimeError'
    except RuntimeError as exc:
        assert '429' in str(exc)
        assert 'gem-test' not in str(exc)


def test_redact_strips_key(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'secret-key-xyz')
    msg = 'url?key=secret-key-xyz failed'
    assert 'secret-key-xyz' not in LLMService._redact(msg)
    assert '[REDACTED]' in LLMService._redact(msg)


@patch('requests.post')
def test_rephrase_uses_gemini(mock_post, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'gem-test')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    mock_post.return_value = MagicMock(
        status_code=200,
        ok=True,
        text='{}',
        json=lambda: {
            'candidates': [
                {'content': {'parts': [{'text': 'Built APIs with Python and Flask'}]}}
            ]
        },
    )
    out = LLMService.rephrase_bullet('Built APIs with Flask', 'Python', 'Engineer')
    assert 'Python' in out
