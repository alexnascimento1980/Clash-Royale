"""
Clash Royale Tracker — backend Flask.

Mudanças em relação à versão anterior (mesmo contrato de rotas, então o
frontend não precisa mudar nada):

- chamadas à API da Supercell passam por cr_client (sessão com retry, cache
  curto e tratamento de erro de rede uniforme) em vez de `requests.get` cru;
- rotas de download fazem as 2-3 chamadas à API EM PARALELO
  (concurrent.futures) em vez de sequencialmente — corta a latência do
  download praticamente pela metade;
- tags são validadas (InvalidTagError -> 400) antes de chegar na API externa;
- geração de CSV foi para csv_export.py, então as rotas não têm mais 150
  linhas de writerow cada;
- debug do Flask agora é controlado por variável de ambiente, desligado por
  padrão.
"""
import json
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, render_template, Response

import config
import cr_client
import csv_export

app = Flask(__name__)

# Pool pequeno e compartilhado só para paralelizar as chamadas dentro de uma
# mesma requisição de download (2 a 3 chamadas por vez, no máximo).
_executor = ThreadPoolExecutor(max_workers=4)


def _api_key_from_header():
    return request.headers.get("X-Api-Key", "")


def _api_key_from_query():
    return request.args.get("key", "")


def _error_response(message, status=400):
    return jsonify({"reason": "invalidTag", "message": message}), status


# ── rota principal ────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ── proxy: jogador ────────────────────────────────────────
@app.route("/api/player/<tag>")
def get_player(tag):
    try:
        data, status = cr_client.get_player(tag, _api_key_from_header())
    except cr_client.InvalidTagError as e:
        return _error_response(str(e))
    return jsonify(data), status


@app.route("/api/player/<tag>/battlelog")
def get_battlelog(tag):
    try:
        data, status = cr_client.get_battlelog(tag, _api_key_from_header())
    except cr_client.InvalidTagError as e:
        return _error_response(str(e))
    return jsonify(data), status


# ── proxy: clã ────────────────────────────────────────────
@app.route("/api/clan/<tag>")
def get_clan(tag):
    try:
        data, status = cr_client.get_clan(tag, _api_key_from_header())
    except cr_client.InvalidTagError as e:
        return _error_response(str(e))
    return jsonify(data), status


@app.route("/api/clan/<tag>/members")
def get_clan_members(tag):
    try:
        data, status = cr_client.get_clan_members(tag, _api_key_from_header())
    except cr_client.InvalidTagError as e:
        return _error_response(str(e))
    return jsonify(data), status


@app.route("/api/clan/<tag>/warlog")
def get_clan_warlog(tag):
    try:
        data, status = cr_client.get_clan_warlog(tag, _api_key_from_header())
    except cr_client.InvalidTagError as e:
        return _error_response(str(e))
    return jsonify(data), status


# ── downloads JSON ───────────────────────────────────────
@app.route("/download/player/<tag>/json")
def download_player_json(tag):
    api_key = _api_key_from_query()
    try:
        future_player = _executor.submit(cr_client.get_player, tag, api_key)
        future_battles = _executor.submit(cr_client.get_battlelog, tag, api_key)
        player, ps = future_player.result()
        battles, _ = future_battles.result()
    except cr_client.InvalidTagError as e:
        return _error_response(str(e))

    if ps != 200:
        return jsonify(player), ps

    payload = {"perfil": player, "historico_batalhas": cr_client.extract_items(battles) if not isinstance(battles, list) else battles}
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=jogador_{tag.lstrip('#').upper()}.json"},
    )


@app.route("/download/clan/<tag>/json")
def download_clan_json(tag):
    api_key = _api_key_from_query()
    try:
        future_clan = _executor.submit(cr_client.get_clan, tag, api_key)
        future_members = _executor.submit(cr_client.get_clan_members, tag, api_key)
        future_warlog = _executor.submit(cr_client.get_clan_warlog, tag, api_key)
        clan, cs = future_clan.result()
        members, _ = future_members.result()
        warlog, _ = future_warlog.result()
    except cr_client.InvalidTagError as e:
        return _error_response(str(e))

    if cs != 200:
        return jsonify(clan), cs

    payload = {
        "clan": clan,
        "membros": cr_client.extract_items(members),
        "historico_guerras": cr_client.extract_items(warlog),
    }
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=cla_{tag.lstrip('#').upper()}.json"},
    )


# ── downloads CSV ────────────────────────────────────────
@app.route("/download/player/<tag>/csv")
def download_player_csv(tag):
    api_key = _api_key_from_query()
    try:
        future_player = _executor.submit(cr_client.get_player, tag, api_key)
        future_battles = _executor.submit(cr_client.get_battlelog, tag, api_key)
        player, ps = future_player.result()
        battles, _ = future_battles.result()
    except cr_client.InvalidTagError as e:
        return _error_response(str(e))

    if ps != 200:
        return jsonify(player), ps

    csv_text = csv_export.build_player_csv(player, cr_client.extract_items(battles))
    return Response(
        csv_text,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=jogador_{tag.lstrip('#').upper()}.csv"},
    )


@app.route("/download/clan/<tag>/csv")
def download_clan_csv(tag):
    api_key = _api_key_from_query()
    try:
        future_clan = _executor.submit(cr_client.get_clan, tag, api_key)
        future_members = _executor.submit(cr_client.get_clan_members, tag, api_key)
        future_warlog = _executor.submit(cr_client.get_clan_warlog, tag, api_key)
        clan, cs = future_clan.result()
        members, _ = future_members.result()
        warlog, _ = future_warlog.result()
    except cr_client.InvalidTagError as e:
        return _error_response(str(e))

    if cs != 200:
        return jsonify(clan), cs

    csv_text = csv_export.build_clan_csv(clan, cr_client.extract_items(members), cr_client.extract_items(warlog))
    return Response(
        csv_text,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=cla_{tag.lstrip('#').upper()}.csv"},
    )


# ── handler genérico de erro (evita vazar stacktrace) ────
@app.errorhandler(500)
def handle_500(e):
    return jsonify({"reason": "internalError", "message": "Erro interno no servidor."}), 500


if __name__ == "__main__":
    print(f"✅ Clash Royale Tracker rodando em http://localhost:{config.FLASK_PORT}")
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
