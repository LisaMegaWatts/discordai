import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import discord_bot

class DummyAsyncSession:
    async def __aenter__(self): return self
    async def __aexit__(self, *a): pass

@pytest.mark.asyncio
async def test_valid_prompt_generates_image(monkeypatch):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "https://example.com/image.png"}}]
    }
    mock_response.raise_for_status.return_value = None
    monkeypatch.setattr("requests.post", lambda *a, **kw: mock_response)

    class MockResp:
        status = 200
        async def read(self): return b"fake_image_bytes"
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
    class MockSession:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def get(self, url): return MockResp()
    monkeypatch.setattr("aiohttp.ClientSession", lambda: MockSession())

    message = MagicMock()
    message.channel = MagicMock()
    message.channel.send = AsyncMock()

    with patch("db.AsyncSessionLocal", lambda: DummyAsyncSession()), \
         patch("crud.create_generated_image", AsyncMock(return_value=True)):
        result = await discord_bot.generate_image_from_prompt("A sunset over mountains", "user123", message)
    assert "I've generated an image for" in result

@pytest.mark.asyncio
async def test_invalid_prompt(monkeypatch):
    message = MagicMock()
    message.channel = MagicMock()
    message.channel.send = AsyncMock()
    result = await discord_bot.generate_image_from_prompt("", "user123", message)
    assert "Error" in result or "provide a description" in result

@pytest.mark.asyncio
async def test_unavailable_model(monkeypatch):
    monkeypatch.setattr("discord_bot.OPENROUTER_IMAGE_MODEL", "nonexistent-model")
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("Model not found")
    monkeypatch.setattr("requests.post", lambda *a, **kw: mock_response)
    message = MagicMock()
    message.channel = MagicMock()
    message.channel.send = AsyncMock()
    with patch("db.AsyncSessionLocal", lambda: DummyAsyncSession()), \
         patch("crud.create_generated_image", AsyncMock(return_value=True)):
        result = await discord_bot.generate_image_from_prompt("A cat", "user123", message)
    assert "failed" in result or "Error" in result

@pytest.mark.asyncio
async def test_api_failure(monkeypatch):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("API failure")
    monkeypatch.setattr("requests.post", lambda *a, **kw: mock_response)
    message = MagicMock()
    message.channel = MagicMock()
    message.channel.send = AsyncMock()
    with patch("db.AsyncSessionLocal", lambda: DummyAsyncSession()), \
         patch("crud.create_generated_image", AsyncMock(return_value=True)):
        result = await discord_bot.generate_image_from_prompt("A dog", "user123", message)
    assert "failed" in result or "Error" in result

@pytest.mark.asyncio
async def test_invalid_api_response(monkeypatch):
    mock_response = MagicMock()
    mock_response.json.return_value = {"unexpected": "format"}
    mock_response.raise_for_status.return_value = None
    monkeypatch.setattr("requests.post", lambda *a, **kw: mock_response)
    message = MagicMock()
    message.channel = MagicMock()
    message.channel.send = AsyncMock()
    with patch("db.AsyncSessionLocal", lambda: DummyAsyncSession()), \
         patch("crud.create_generated_image", AsyncMock(return_value=True)):
        result = await discord_bot.generate_image_from_prompt("A robot", "user123", message)
    assert "Unexpected response format" in result or "Error" in result

@pytest.mark.asyncio
async def test_image_metadata(monkeypatch):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "https://example.com/image.png"}}]
    }
    mock_response.raise_for_status.return_value = None
    monkeypatch.setattr("requests.post", lambda *a, **kw: mock_response)
    class MockResp:
        status = 200
        async def read(self): return b"fake_image_bytes"
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
    class MockSession:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def get(self, url): return MockResp()
    monkeypatch.setattr("aiohttp.ClientSession", lambda: MockSession())
    message = MagicMock()
    message.channel = MagicMock()
    message.channel.send = AsyncMock()
    with patch("db.AsyncSessionLocal", lambda: DummyAsyncSession()), \
         patch("crud.create_generated_image", AsyncMock(return_value=True)):
        result = await discord_bot.generate_image_from_prompt("A logo", "user123", message)
    assert "generated an image" in result
