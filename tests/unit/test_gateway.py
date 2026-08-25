"""
Gateway unit tests — auth and rate-limiter key function, without spinning up
the full FastAPI app. Full end-to-end route behavior (auth enforcement,
brand CRUD, pipeline trigger + concurrency guard, real signal harvest +
classify + score) was verified manually against a live local server —
see the run history for that trace.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from gateway.auth import require_api_key
from gateway.limiter import _real_client_ip


class TestRequireApiKey:
    async def test_missing_key_rejected(self, monkeypatch):
        monkeypatch.setattr("gateway.auth.settings.signalharvest_api_key", "secret-key")
        with pytest.raises(HTTPException) as exc:
            await require_api_key(api_key=None)
        assert exc.value.status_code == 401

    async def test_wrong_key_rejected(self, monkeypatch):
        monkeypatch.setattr("gateway.auth.settings.signalharvest_api_key", "secret-key")
        with pytest.raises(HTTPException) as exc:
            await require_api_key(api_key="wrong-key")
        assert exc.value.status_code == 401

    async def test_correct_key_accepted(self, monkeypatch):
        monkeypatch.setattr("gateway.auth.settings.signalharvest_api_key", "secret-key")
        result = await require_api_key(api_key="secret-key")
        assert result == "secret-key"

    async def test_empty_configured_key_rejects_everything(self, monkeypatch):
        # An unset SIGNALHARVEST_API_KEY must fail closed, not fail open.
        monkeypatch.setattr("gateway.auth.settings.signalharvest_api_key", "")
        with pytest.raises(HTTPException) as exc:
            await require_api_key(api_key="")
        assert exc.value.status_code == 401


def _request(headers: dict, client_host: str | None = "10.0.0.1") -> MagicMock:
    req = MagicMock()
    req.headers = headers
    req.client = MagicMock(host=client_host) if client_host else None
    return req


class TestRealClientIp:
    def test_prefers_cf_connecting_ip(self):
        req = _request({"cf-connecting-ip": "203.0.113.5", "x-forwarded-for": "10.1.1.1"})
        assert _real_client_ip(req) == "203.0.113.5"

    def test_falls_back_to_x_forwarded_for(self):
        req = _request({"x-forwarded-for": "203.0.113.9, 10.1.1.1"})
        assert _real_client_ip(req) == "203.0.113.9"

    def test_falls_back_to_client_host_when_no_proxy_headers(self):
        req = _request({}, client_host="127.0.0.1")
        assert _real_client_ip(req) == "127.0.0.1"

    def test_handles_missing_client(self):
        req = _request({}, client_host=None)
        assert _real_client_ip(req) == "unknown"
