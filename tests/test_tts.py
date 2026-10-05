"""TTS API and the security policy needed for object-URL playback."""
from unittest.mock import AsyncMock, patch

import httpx
import pytest


def test_audio_object_urls_allowed_without_relaxing_scripts(client):
    response = client.get('/login')
    policy = response.headers['content-security-policy']
    directives = dict(part.strip().split(' ', 1) for part in policy.split(';') if part.strip())
    assert directives['media-src'] == "'self' blob:"
    assert directives['script-src'] == "'self'"


def test_tts_returns_audio(auth_client):
    upstream = httpx.Response(200, content=b'ID3-test-audio', headers={'content-type': 'audio/mpeg'})
    with patch('main.httpx.AsyncClient') as factory:
        factory.return_value.__aenter__.return_value.get = AsyncMock(return_value=upstream)
        response = auth_client.post('/api/tts', json={'text': 'Bonjour', 'lang': 'fr'})
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('audio/mpeg')
    assert response.content == b'ID3-test-audio'


@pytest.mark.parametrize('status, content, content_type', [
    (403, b'blocked', 'text/html'),
    (200, b'<html>Not audio</html>', 'text/html'),
    (200, b'', 'audio/mpeg'),
])
def test_tts_rejects_provider_failure(auth_client, status, content, content_type):
    upstream = httpx.Response(status, content=content, headers={'content-type': content_type})
    with patch('main.httpx.AsyncClient') as factory:
        factory.return_value.__aenter__.return_value.get = AsyncMock(return_value=upstream)
        response = auth_client.post('/api/tts', json={'text': 'Bonjour'})
    assert response.status_code == 502


def test_tts_rejects_blank_text(auth_client):
    response = auth_client.post('/api/tts', json={'text': '   '})
    assert response.status_code == 400
