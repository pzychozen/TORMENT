"""Keep active release identifiers consistent across package, HTTP and setup UI."""
from pathlib import Path

import pytest

from test_rest_auth_boundary import API_KEY, _client_with_env


RELEASE_VERSION = "2.5.1"


def test_package_release_version():
    import torment_service

    assert torment_service.__version__ == RELEASE_VERSION


@pytest.fixture()
def release_client(tmp_path):
    yield from _client_with_env(tmp_path, auth_enabled=True)


@pytest.mark.parametrize("path", ["/health", "/openapi.json"])
def test_http_release_version(release_client, path):
    client, appmod = release_client
    assert appmod.app.version == RELEASE_VERSION
    response = client.get(path, headers={"X-API-Key": API_KEY})
    assert response.status_code == 200, response.text
    payload = response.json()
    metadata = payload["info"] if path == "/openapi.json" else payload
    assert metadata["version"] == RELEASE_VERSION


def test_setup_page_release_version():
    root = Path(__file__).resolve().parents[1]
    html = (root / "start" / "torment_character_creator.html").read_text(encoding="utf-8")
    assert f'<div class="version-tag">v{RELEASE_VERSION}</div>' in html
