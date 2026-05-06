from unittest.mock import MagicMock, patch
import jupyterMagicCommands.extensions.ai_ext as ai_ext
from jupyterMagicCommands.extensions.ai_ext import OpenAIBackend, AzureOpenAIBackend


def _make_openai_backend(response_content="reply"):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = response_content
    with patch("openai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response
        backend = OpenAIBackend("fake_key", "gpt-3.5-turbo")
    backend.client.chat.completions.create.return_value = mock_response
    return backend


def _make_azure_backend(response_content="azure reply", raise_exc=None):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = response_content
    with patch("openai.AzureOpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        backend = AzureOpenAIBackend("https://endpoint", "key", "deployment")
    if raise_exc:
        backend.client.chat.completions.create.side_effect = raise_exc
    else:
        backend.client.chat.completions.create.return_value = mock_response
    return backend


class TestOpenAIBackendRoles:

    def setup_method(self):
        ai_ext.history.clear()

    def test_user_message_uses_user_role(self):
        backend = _make_openai_backend()
        backend.conversation("hello")
        assert ai_ext.history[0]["role"] == "user"
        assert ai_ext.history[0]["content"] == "hello"

    def test_assistant_message_uses_assistant_role(self):
        backend = _make_openai_backend("reply")
        backend.conversation("hello")
        assert ai_ext.history[1]["role"] == "assistant"
        assert ai_ext.history[1]["content"] == "reply"

    def test_no_bot_or_system_roles_used(self):
        backend = _make_openai_backend()
        backend.conversation("hello")
        roles = {m["role"] for m in ai_ext.history}
        assert "bot" not in roles
        assert "system" not in roles


class TestAzureOpenAIBackendRoles:

    def setup_method(self):
        ai_ext.history.clear()

    def test_user_message_uses_user_role(self):
        backend = _make_azure_backend()
        backend.conversation("hi")
        assert ai_ext.history[0]["role"] == "user"

    def test_assistant_message_uses_assistant_role(self):
        backend = _make_azure_backend("azure reply")
        backend.conversation("hi")
        assert ai_ext.history[1]["role"] == "assistant"

    def test_history_rolled_back_on_api_error(self):
        backend = _make_azure_backend(raise_exc=Exception("API error"))
        backend.conversation("hi")
        # On API failure, the user message is popped back
        assert len(ai_ext.history) == 0
