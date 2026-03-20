from flask import Flask, request, jsonify, render_template, Response
import requests
import csv
import json
import io

app = Flask(__name__)

CR_BASE = "https://api.clashroyale.com/v1"


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


# ── downloads JSON ────────────────────────────────────────

@app.route("/download/player/<tag>/json")
def download_player_json(tag):
    api_key = request.args.get("key", "")
    clean = tag.lstrip("#")
    player, ps = cr_get(f"players/%23{clean}", api_key)
    if ps != 200:
        return jsonify(player), ps
    battles, _ = cr_get(f"players/%23{clean}/battlelog", api_key)
    payload = {
        "perfil": player,
        "historico_batalhas": battles if isinstance(battles, list) else battles.get("items", [])
    }
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=jogador_{clean}.json"}
    )


@app.route("/download/clan/<tag>/json")
def download_clan_json(tag):
    api_key = request.args.get("key", "")
    clean = tag.lstrip("#")
    clan, cs = cr_get(f"clans/%23{clean}", api_key)
    if cs != 200:
        return jsonify(clan), cs
    members, _ = cr_get(f"clans/%23{clean}/members", api_key)
    warlog,  _ = cr_get(f"clans/%23{clean}/riverracelog", api_key)
    payload = {
        "clan": clan,
        "membros":           members.get("items", []) if isinstance(members, dict) else members,
        "historico_guerras": warlog.get("items",   []) if isinstance(warlog,  dict) else warlog,
    }
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=cla_{clean}.json"}
    )


# ── download CSV jogador (completo) ───────────────────────

@app.route("/download/player/<tag>/csv")
def download_player_csv(tag):
    api_key = request.args.get("key", "")
    clean = tag.lstrip("#")

    player, ps = cr_get(f"players/%23{clean}", api_key)
    if ps != 200:
        return jsonify(player), ps

    battles, _ = cr_get(f"players/%23{clean}/battlelog", api_key)
    battles = battles if isinstance(battles, list) else battles.get("items", [])

    output = io.StringIO()
    w = csv.writer(output)

    # ════════════════════════════════════════
    # 1. PERFIL COMPLETO
    # ════════════════════════════════════════
    w.writerow(["=== PERFIL DO JOGADOR ==="])
    w.writerow(["Campo", "Valor"])

    clan      = player.get("clan", {}) or {}
    league    = player.get("leagueStatistics", {}) or {}
    cur_season  = league.get("currentSeason", {})  or {}
    prev_season = league.get("previousSeason", {}) or {}
    best_season = league.get("bestSeason", {})      or {}

    rows_perfil = [
        # Identificação
        ("Nome",                    player.get("name", "")),
        ("Tag",                     player.get("tag", "")),
        ("Nível de Experiência",    player.get("expLevel", "")),
        ("Pontos de Experiência",   player.get("expPoints", "")),
        ("Total Pontos Exp.",       player.get("totalExpPoints", "")),
        ("Star Points",             player.get("starPoints", "")),
        # Troféus
        ("Troféus Atuais",          player.get("trophies", "")),
        ("Melhor Troféus",          player.get("bestTrophies", "")),
        ("High Score Estrada Troféus", player.get("legacyTrophyRoadHighScore", "")),
        # Arena
        ("Arena Atual",             player.get("arena", {}).get("name", "") if player.get("arena") else ""),
        ("ID Arena",                player.get("arena", {}).get("id", "")   if player.get("arena") else ""),
        # Batalhas
        ("Total de Batalhas",       player.get("battleCount", "")),
        ("Vitórias",                player.get("wins", "")),
        ("Derrotas",                player.get("losses", "")),
        ("Vitórias 3 Coroas",       player.get("threeCrownWins", "")),
        # Clã
        ("Clã",                     clan.get("name", "Sem clã")),
        ("Tag do Clã",              clan.get("tag", "")),
        ("Cargo no Clã",            player.get("role", "")),
        ("Doações",                 player.get("donations", "")),
        ("Doações Recebidas",       player.get("donationsReceived", "")),
        ("Vitórias em Guerra",      player.get("warDayWins", "")),
        ("Cartas Coletadas (Clã)",  player.get("clanCardsCollected", "")),
        # Liga
        ("Temporada Atual - Troféus",     cur_season.get("trophies", "")),
        ("Temporada Atual - Melhor",      cur_season.get("bestTrophies", "")),
        ("Temporada Anterior - ID",       prev_season.get("id", "")),
        ("Temporada Anterior - Troféus",  prev_season.get("trophies", "")),
        ("Temporada Anterior - Melhor",   prev_season.get("bestTrophies", "")),
        ("Melhor Temporada - ID",         best_season.get("id", "")),
        ("Melhor Temporada - Troféus",    best_season.get("trophies", "")),
        # Carta favorita
        ("Carta Favorita",          player.get("currentFavouriteCard", {}).get("name", "") if player.get("currentFavouriteCard") else ""),
    ]
    for label, val in rows_perfil:
        w.writerow([label, val])
    w.writerow([])

    # ════════════════════════════════════════
    # 2. DECK ATUAL
    # ════════════════════════════════════════
    w.writerow(["=== DECK ATUAL ==="])
    w.writerow(["Slot", "Carta", "Nível", "Nível Máx.", "ID", "Elixir"])
    for i, c in enumerate(player.get("currentDeck", []), 1):
        w.writerow([
            i,
            c.get("name", ""),
            c.get("level", ""),
            c.get("maxLevel", ""),
            c.get("id", ""),
            c.get("elixirCost", ""),
        ])
    w.writerow([])

    # ════════════════════════════════════════
    # 3. COLEÇÃO DE CARTAS
    # ════════════════════════════════════════
    w.writerow(["=== COLEÇÃO DE CARTAS ==="])
    w.writerow(["Carta", "Nível", "Nível Máx.", "Quantidade", "Qtd. p/ Upgrade", "ID", "Elixir"])
    for c in player.get("cards", []):
        w.writerow([
            c.get("name", ""),
            c.get("level", ""),
            c.get("maxLevel", ""),
            c.get("count", ""),
            c.get("upgradeToNextLevel", ""),
            c.get("id", ""),
            c.get("elixirCost", ""),
        ])
    w.writerow([])

    # ════════════════════════════════════════
    # 4. CONQUISTAS (BADGES)
    # ════════════════════════════════════════
    w.writerow(["=== CONQUISTAS (BADGES) ==="])
    w.writerow(["Nome", "Nível", "Progresso", "Progresso Máx.", "Target"])
    for b in player.get("badges", []):
        w.writerow([
            b.get("name", ""),
            b.get("level", ""),
            b.get("progress", ""),
            b.get("maxProgress", ""),
            b.get("target", ""),
        ])
    w.writerow([])

    # ════════════════════════════════════════
    # 5. HISTÓRICO DE BATALHAS (COMPLETO)
    # ════════════════════════════════════════
    w.writerow(["=== HISTÓRICO DE BATALHAS ==="])
    w.writerow([
        # Cabeçalho principal
        "Data", "Tipo", "Modo de Jogo", "Arena",
        # Time
        "Jogador (Time)", "Tag (Time)", "Troféus (Time)", "Coroas (Time)", "King HP (Time)", "Princess HP (Time)",
        "Deck Usado (Time)",
        # Oponente
        "Oponente", "Tag (Oponente)", "Troféus (Oponente)", "Coroas (Oponente)", "King HP (Oponente)", "Princess HP (Oponente)",
        "Deck Usado (Oponente)",
        # Resultado
        "Resultado",
    ])

    for b in battles:
        team_p = b.get("team", [{}])[0]     if b.get("team")     else {}
        opp_p  = b.get("opponent", [{}])[0] if b.get("opponent") else {}

        my_c  = team_p.get("crowns", 0)
        op_c  = opp_p.get("crowns", 0)
        result = "Vitória" if my_c > op_c else "Derrota" if my_c < op_c else "Empate"

        # King/Princess HP (towers)
        def get_towers(p_data):
            towers = p_data.get("princessTowersHitPoints") or []
            king   = p_data.get("kingTowerHitPoints", "")
            princess = " / ".join(str(t) for t in towers) if towers else ""
            return king, princess

        my_king, my_princess = get_towers(team_p)
        op_king, op_princess = get_towers(opp_p)

        w.writerow([
            fmt_date(b.get("battleTime", "")),
            b.get("type", ""),
            b.get("gameMode", {}).get("name", "") if b.get("gameMode") else "",
            b.get("arena", {}).get("name", "")    if b.get("arena")    else "",
            # Time
            team_p.get("name", ""),
            team_p.get("tag", ""),
            team_p.get("startingTrophies", ""),
            my_c,
            my_king,
            my_princess,
            cards_str(team_p.get("cards", [])),
            # Oponente
            opp_p.get("name", ""),
            opp_p.get("tag", ""),
            opp_p.get("startingTrophies", ""),
            op_c,
            op_king,
            op_princess,
            cards_str(opp_p.get("cards", [])),
            result,
        ])
    w.writerow([])

    output.seek(0)
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=jogador_{clean}.csv"}
    )


# ── download CSV clã (completo) ───────────────────────────

@app.route("/download/clan/<tag>/csv")
def download_clan_csv(tag):
    api_key = request.args.get("key", "")
    clean = tag.lstrip("#")

    clan, cs = cr_get(f"clans/%23{clean}", api_key)
    if cs != 200:
        return jsonify(clan), cs

    members, _ = cr_get(f"clans/%23{clean}/members", api_key)
    members = members.get("items", []) if isinstance(members, dict) else members

    warlog, _ = cr_get(f"clans/%23{clean}/riverracelog", api_key)
    warlog = warlog.get("items", []) if isinstance(warlog, dict) else warlog

    output = io.StringIO()
    w = csv.writer(output)

    ROLES = {"leader": "Líder", "coLeader": "Co-Líder", "elder": "Ancião", "member": "Membro"}

    # ════════════════════════════════════════
    # 1. INFORMAÇÕES DO CLÃ
    # ════════════════════════════════════════
    w.writerow(["=== INFORMAÇÕES DO CLÃ ==="])
    w.writerow(["Campo", "Valor"])
    type_label = {"open": "Aberto", "inviteOnly": "Apenas Convite", "closed": "Fechado"}
    rows_clan = [
        ("Nome",               clan.get("name", "")),
        ("Tag",                clan.get("tag", "")),
        ("Descrição",          clan.get("description", "")),
        ("Tipo",               type_label.get(clan.get("type", ""), clan.get("type", ""))),
        ("Pontuação do Clã",   clan.get("clanScore", "")),
        ("Troféus de Guerra",  clan.get("clanWarTrophies", "")),
        ("Membros",            clan.get("members", "")),
        ("Doações/Semana",     clan.get("donationsPerWeek", "")),
        ("Troféus Mínimos",    clan.get("requiredTrophies", "")),
        ("Localização",        clan.get("location", {}).get("name", "") if clan.get("location") else ""),
        ("País",               clan.get("location", {}).get("countryCode", "") if clan.get("location") else ""),
        ("ID Localização",     clan.get("location", {}).get("id", "") if clan.get("location") else ""),
        ("Tag do Badge",       clan.get("badgeId", "")),
    ]
    for label, val in rows_clan:
        w.writerow([label, val])
    w.writerow([])

    # ════════════════════════════════════════
    # 2. MEMBROS COMPLETOS
    # ════════════════════════════════════════
    w.writerow(["=== MEMBROS ATUAIS ==="])
    w.writerow([
        "#", "Nome", "Tag", "Cargo",
        "Nível Exp.", "Troféus", "Melhor Troféus",
        "Arena", "Rank no Clã", "Rank Anterior no Clã",
        "Doações", "Doações Recebidas",
        "Último Online",
    ])
    for i, m in enumerate(members, 1):
        arena = m.get("arena", {}).get("name", "") if m.get("arena") else ""
        w.writerow([
            i,
            m.get("name", ""),
            m.get("tag", ""),
            ROLES.get(m.get("role", ""), m.get("role", "")),
            m.get("expLevel", ""),
            m.get("trophies", ""),
            m.get("bestTrophies", ""),
            arena,
            m.get("clanRank", ""),
            m.get("previousClanRank", ""),
            m.get("donations", ""),
            m.get("donationsReceived", ""),
            fmt_date(m.get("lastSeen", "")) if m.get("lastSeen") else "",
        ])
    w.writerow([])

    # ════════════════════════════════════════
    # 3. GUERRAS — RESUMO POR TEMPORADA
    # ════════════════════════════════════════
    w.writerow(["=== HISTÓRICO DE GUERRAS — RESUMO ==="])
    w.writerow([
        "Temporada", "Seção", "Posição do Clã",
        "Fama", "Reparos", "Participantes",
        "1º Lugar", "Fama 1º",
        "2º Lugar", "Fama 2º",
        "3º Lugar", "Fama 3º",
        "4º Lugar", "Fama 4º",
        "5º Lugar", "Fama 5º",
    ])
    for i, race in enumerate(warlog, 1):
        standings = sorted(race.get("standings", []), key=lambda x: x.get("rank", 99))
        our = next((s for s in standings if s.get("clan", {}).get("tag") == clan.get("tag")), None)
        our_clan = our.get("clan", {}) if our else {}

        def sname(idx): return standings[idx].get("clan", {}).get("name", "") if idx < len(standings) else ""
        def sfame(idx): return standings[idx].get("clan", {}).get("fame", "") if idx < len(standings) else ""

        w.writerow([
            race.get("seasonId", i),
            race.get("sectionIndex", ""),
            our.get("rank", "") if our else "",
            our_clan.get("fame", ""),
            our_clan.get("repairPoints", ""),
            len(our_clan.get("participants", [])),
            sname(0), sfame(0),
            sname(1), sfame(1),
            sname(2), sfame(2),
            sname(3), sfame(3),
            sname(4), sfame(4),
        ])
    w.writerow([])

    # ════════════════════════════════════════
    # 4. GUERRAS — PARTICIPANTES INDIVIDUAIS
    # ════════════════════════════════════════
    w.writerow(["=== HISTÓRICO DE GUERRAS — PARTICIPANTES INDIVIDUAIS ==="])
    w.writerow([
        "Temporada", "Seção", "Posição do Clã",
        "Nome do Jogador", "Tag do Jogador",
        "Fama", "Reparos",
        "Batalhas no Barco", "Ataques Restantes",
        "Decks Usados", "Decks na Semana",
    ])
    for i, race in enumerate(warlog, 1):
        standings = sorted(race.get("standings", []), key=lambda x: x.get("rank", 99))
        our = next((s for s in standings if s.get("clan", {}).get("tag") == clan.get("tag")), None)
        our_clan = our.get("clan", {}) if our else {}
        our_rank = our.get("rank", "") if our else ""

        for p in our_clan.get("participants", []):
            w.writerow([
                race.get("seasonId", i),
                race.get("sectionIndex", ""),
                our_rank,
                p.get("name", ""),
                p.get("tag", ""),
                p.get("fame", ""),
                p.get("repairPoints", ""),
                p.get("boatAttacks", ""),
                p.get("decksUsedToday", ""),
                p.get("decksUsed", ""),
                p.get("decksUsedTotal", ""),
            ])
    w.writerow([])

    output.seek(0)
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=cla_{clean}.csv"}
    )


if __name__ == "__main__":
    print("✅ Clash Royale Tracker rodando em http://localhost:5000")
    app.run(debug=True, port=5000)
