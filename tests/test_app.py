"""Testes do backend (sem rede: a sessão HTTP do cr_client é substituída)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cr_client  # noqa: E402
import csv_export  # noqa: E402
from app import app  # noqa: E402


class FakeResp:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status

    def json(self):
        return self._data


@pytest.fixture(autouse=True)
def _clean_cache():
    cr_client._cache.clear()
    yield
    cr_client._cache.clear()


@pytest.fixture
def client():
    return app.test_client()


def fake_get(routes, calls=None):
    def _get(url, headers=None, timeout=None):
        if calls is not None:
            calls.append((url, headers))
        for suffix, resp in routes.items():
            if url.endswith(suffix):
                return resp
        return FakeResp({"reason": "notFound"}, 404)
    return _get


# ── tags ───────────────────────────────────────────────────
def test_normalize_tag_ok():
    assert cr_client.normalize_tag(" #2pp ") == "2PP"


@pytest.mark.parametrize("bad", ["", "#", "ABC", "2PP/../x", "2PP?a=1"])
def test_normalize_tag_invalid(bad):
    with pytest.raises(cr_client.InvalidTagError):
        cr_client.normalize_tag(bad)


def test_invalid_tag_returns_400(client):
    r = client.get("/api/player/XYZ", headers={"X-Api-Key": "k"})
    assert r.status_code == 400


# ── chave de API / cache ───────────────────────────────────
def test_missing_api_key_is_401_without_network(client, monkeypatch):
    calls = []
    monkeypatch.setattr(cr_client._session, "get", fake_get({}, calls))
    r = client.get("/api/player/2PP")
    assert r.status_code == 401
    assert calls == []


def test_cache_is_not_shared_between_api_keys(monkeypatch):
    calls = []
    monkeypatch.setattr(
        cr_client._session, "get",
        fake_get({"players/%232PP": FakeResp({"name": "ok"})}, calls),
    )
    assert cr_client.get_player("2PP", "key-A")[1] == 200
    assert cr_client.get_player("2PP", "key-A")[1] == 200  # cache hit
    assert len(calls) == 1
    cr_client.get_player("2PP", "key-B")  # outra chave → nova chamada
    assert len(calls) == 2


def test_cache_respects_max_entries(monkeypatch):
    monkeypatch.setattr(cr_client.config, "CACHE_MAX_ENTRIES", 3)
    for i in range(10):
        cr_client._cache.set(("p", str(i)), (i, 200))
    assert len(cr_client._cache._store) <= 3


def test_error_responses_are_not_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(
        cr_client._session, "get",
        fake_get({"players/%232PP": FakeResp({"reason": "accessDenied"}, 403)}, calls),
    )
    cr_client.get_player("2PP", "k")
    cr_client.get_player("2PP", "k")
    assert len(calls) == 2


# ── rotas ──────────────────────────────────────────────────
def test_security_headers(client, monkeypatch):
    monkeypatch.setattr(
        cr_client._session, "get",
        fake_get({"players/%232PP": FakeResp({"name": "x"})}),
    )
    r = client.get("/api/player/2PP", headers={"X-Api-Key": "k"})
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_index_served(client):
    assert client.get("/").status_code == 200


def test_player_csv_download(client, monkeypatch):
    monkeypatch.setattr(cr_client._session, "get", fake_get({
        "players/%232PP": FakeResp({"name": "=cmd()", "tag": "#2PP", "cards": [], "badges": []}),
        "battlelog": FakeResp([]),
    }))
    r = client.get("/download/player/2PP/csv?key=k")
    assert r.status_code == 200
    assert "'=cmd()" in r.data.decode("utf-8-sig")
    assert "jogador_2PP.csv" in r.headers["Content-Disposition"]


def test_clan_json_download(client, monkeypatch):
    monkeypatch.setattr(cr_client._session, "get", fake_get({
        "clans/%232PP": FakeResp({"name": "C", "tag": "#2PP"}),
        "members": FakeResp({"items": [{"name": "m"}]}),
        "riverracelog": FakeResp({"items": []}),
    }))
    r = client.get("/download/clan/2PP/json?key=k")
    assert r.status_code == 200
    assert r.get_json()["membros"] == [{"name": "m"}]


# ── CSV ────────────────────────────────────────────────────
@pytest.mark.parametrize("val", ["=1+1", "+1", "-1+2", "@SUM(A1)", "\tx"])
def test_safe_cell_neutralizes_formulas(val):
    assert csv_export.safe_cell(val).startswith("'")


def test_safe_cell_keeps_numbers_and_text():
    assert csv_export.safe_cell(-5) == -5
    assert csv_export.safe_cell("Alex") == "Alex"


def test_fmt_date():
    assert csv_export.fmt_date("20261114T182300.000Z") == "14/11/2026 18:23"
