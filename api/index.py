from flask import Flask, request, jsonify, render_template, Response
import requests
import csv
import json
import io
import os

# AJUSTE 1: Mostra ao Flask onde está a pasta templates na Vercel
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))

# AJUSTE 2: Usando o Proxy gratuito da comunidade para burlar o bloqueio de IP
CR_BASE = "https://proxy.royaleapi.dev/v1"

def cr_get(path, api_key):
    url = f"{CR_BASE}/{path}"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers, timeout=10)
    return resp.json(), resp.status_code

def fmt_date(ts):
    s = str(ts)
    if len(s) < 8:
        return s
    h = s[9:11] if len(s) > 9 else "00"
    m = s[11:13] if len(s) > 11 else "00"
    return f"{s[6:8]}/{s[4:6]}/{s[0:4]} {h}:{m}"

def cards_str(card_list):
    """Converte lista de cartas em string legível."""
    if not card_list:
        return ""
    return " | ".join(
        f"{c.get('name','?')} (Nv.{c.get('level','?')})"
        for c in card_list
    )

# ── rotas principais ──────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/player/<tag>")
def get_player(tag):
    api_key = request.headers.get("X-Api-Key", "")
    data, status = cr_get(f"players/%23{tag.lstrip('#')}", api_key)
    return jsonify(data), status

@app.route("/api/player/<tag>/battlelog")
def get_battlelog(tag):
    api_key = request.headers.get("X-Api-Key", "")
    data, status = cr_get(f"players/%23{tag.lstrip('#')}/battlelog", api_key)
    return jsonify(data), status

@app.route("/api/clan/<tag>")
def get_clan(tag):
    api_key = request.headers.get("X-Api-Key", "")
    data, status = cr_get(f"clans/%23{tag.lstrip('#')}", api_key)
    return jsonify(data), status

@app.route("/api/clan/<tag>/members")
def get_clan_members(tag):
    api_key = request.headers.get("X-Api-Key", "")
    data, status = cr_get(f"clans/%23{tag.lstrip('#')}/members", api_key)
    return jsonify(data), status

@app.route("/api/clan/<tag>/warlog")
def get_clan_warlog(tag):
    api_key = request.headers.get("X-Api-Key", "")
    data, status = cr_get(f"clans/%23{tag.lstrip('#')}/riverracelog", api_key)
    return jsonify(data), status

# ... (MANTENHA AQUI TODAS AS SUAS ROTAS DE DOWNLOAD CSV E JSON EXATAMENTE COMO ESTAVAM) ...

# AJUSTE 3: O bloco de execução local fica isolado.
if __name__ == "__main__":
    print("✅ Clash Royale Tracker rodando localmente")
    app.run(debug=True, port=5000)