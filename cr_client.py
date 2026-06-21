"""
Cliente para a API oficial do Clash Royale.

Comparado à versão anterior (uma função `cr_get` que abria headers e fazia
`requests.get` toda vez), este módulo:

- reutiliza uma única `requests.Session` com pool de conexões e retry/backoff
  automático para erros transitórios (timeout, conexão recusada, 502/503/504);
- valida e normaliza a tag antes de montar a URL, evitando que texto arbitrário
  digitado pelo usuário vá parar na requisição para a API da Supercell;
- cacheia respostas por um curto período (configurável), evitando bater na API
  repetidamente quando o usuário troca de aba no mesmo jogador/clã;
- centraliza o tratamento de erros de rede, devolvendo sempre um formato
  consistente: (dict, status_code).
"""
import time
import threading
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config


class InvalidTagError(ValueError):
    """Tag não corresponde ao formato de tags do Clash Royale."""


def normalize_tag(raw_tag: str) -> str:
    """Remove '#', espaços e maiúsculiza. Levanta InvalidTagError se inválida."""
    tag = (raw_tag or "").strip().lstrip("#").upper()
    if not tag or any(ch not in config.VALID_TAG_CHARS for ch in tag):
        raise InvalidTagError(f"Tag inválida: '{raw_tag}'")
    return tag


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=config.CR_MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=(502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=20)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class _TTLCache:
    """Cache em memória simples e thread-safe. Não persiste entre cold starts
    em ambiente serverless — é uma otimização best-effort, não uma garantia."""

    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def get(self, key):
        if config.CACHE_TTL_SECONDS <= 0:
            return None
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            value, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key, value):
        if config.CACHE_TTL_SECONDS <= 0:
            return
        with self._lock:
            self._store[key] = (value, time.time() + config.CACHE_TTL_SECONDS)


_session = _build_session()
_cache = _TTLCache()


def cr_get(path: str, api_key: str, use_cache: bool = True):
    """Faz GET em `{CR_BASE_URL}/{path}` autenticado com `api_key`.

    Retorna sempre (dict, status_code), mesmo em caso de erro de rede —
    nesse caso o dict tem o formato {"reason": ..., "message": ...},
    compatível com o formato de erro que a própria API da Supercell usa
    (e que o frontend já sabe ler via `data.message`).
    """
    cache_key = (path, bool(api_key))
    if use_cache:
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

    url = f"{config.CR_BASE_URL}/{path}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        resp = _session.get(url, headers=headers, timeout=config.CR_TIMEOUT)
    except requests.exceptions.Timeout:
        return {"reason": "timeout", "message": "A API do Clash Royale demorou demais para responder."}, 504
    except requests.exceptions.ConnectionError:
        return {"reason": "connectionError", "message": "Não foi possível conectar à API do Clash Royale."}, 502
    except requests.exceptions.RequestException as exc:
        return {"reason": "requestError", "message": f"Erro ao consultar a API: {exc}"}, 502

    try:
        data = resp.json()
    except ValueError:
        data = {"reason": "invalidResponse", "message": "Resposta inesperada da API do Clash Royale."}

    result = (data, resp.status_code)
    if use_cache and resp.status_code == 200:
        _cache.set(cache_key, result)
    return result


def player_path(tag: str) -> str:
    return f"players/%23{quote(normalize_tag(tag))}"


def clan_path(tag: str) -> str:
    return f"clans/%23{quote(normalize_tag(tag))}"


def get_player(tag: str, api_key: str):
    return cr_get(player_path(tag), api_key)


def get_battlelog(tag: str, api_key: str):
    return cr_get(f"{player_path(tag)}/battlelog", api_key)


def get_clan(tag: str, api_key: str):
    return cr_get(clan_path(tag), api_key)


def get_clan_members(tag: str, api_key: str):
    return cr_get(f"{clan_path(tag)}/members", api_key)


def get_clan_warlog(tag: str, api_key: str):
    return cr_get(f"{clan_path(tag)}/riverracelog", api_key)


def extract_items(payload):
    """A API às vezes devolve uma lista direto, às vezes um dict com 'items'."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("items", [])
    return []
