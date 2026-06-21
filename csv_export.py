"""
Geração dos arquivos CSV de jogador e clã.

Extraído do app.py original (onde cada rota de download tinha ~150 linhas
de `w.writerow(...)` repetidas). A estrutura e os nomes de coluna são os
mesmos da versão anterior — só a organização do código mudou — então os
CSVs gerados continuam compatíveis com qualquer planilha/processo que o
usuário já tenha montado em cima deles.
"""
import csv
import io


def fmt_date(ts) -> str:
    s = str(ts)
    if len(s) < 8:
        return s
    h = s[9:11] if len(s) > 9 else "00"
    m = s[11:13] if len(s) > 11 else "00"
    return f"{s[6:8]}/{s[4:6]}/{s[0:4]} {h}:{m}"


def cards_str(card_list) -> str:
    if not card_list:
        return ""
    return " | ".join(f"{c.get('name', '?')} (Nv.{c.get('level', '?')})" for c in card_list)


def _write_kv_section(w, title, rows):
    w.writerow([f"=== {title} ==="])
    w.writerow(["Campo", "Valor"])
    for label, val in rows:
        w.writerow([label, val])
    w.writerow([])


def _write_table_section(w, title, headers, rows):
    w.writerow([f"=== {title} ==="])
    w.writerow(headers)
    for row in rows:
        w.writerow(row)
    w.writerow([])


def _to_csv_response_text(output: io.StringIO) -> str:
    output.seek(0)
    return "\ufeff" + output.getvalue()  # BOM UTF-8 para abrir certo no Excel


# ─────────────────────────────── JOGADOR ───────────────────────────────

def build_player_csv(player: dict, battles: list) -> str:
    output = io.StringIO()
    w = csv.writer(output)

    clan = player.get("clan", {}) or {}
    league = player.get("leagueStatistics", {}) or {}
    cur_season = league.get("currentSeason", {}) or {}
    prev_season = league.get("previousSeason", {}) or {}
    best_season = league.get("bestSeason", {}) or {}
    arena = player.get("arena") or {}
    fav_card = player.get("currentFavouriteCard") or {}

    _write_kv_section(w, "PERFIL DO JOGADOR", [
        ("Nome", player.get("name", "")),
        ("Tag", player.get("tag", "")),
        ("Nível de Experiência", player.get("expLevel", "")),
        ("Pontos de Experiência", player.get("expPoints", "")),
        ("Total Pontos Exp.", player.get("totalExpPoints", "")),
        ("Star Points", player.get("starPoints", "")),
        ("Troféus Atuais", player.get("trophies", "")),
        ("Melhor Troféus", player.get("bestTrophies", "")),
        ("High Score Estrada Troféus", player.get("legacyTrophyRoadHighScore", "")),
        ("Arena Atual", arena.get("name", "")),
        ("ID Arena", arena.get("id", "")),
        ("Total de Batalhas", player.get("battleCount", "")),
        ("Vitórias", player.get("wins", "")),
        ("Derrotas", player.get("losses", "")),
        ("Vitórias 3 Coroas", player.get("threeCrownWins", "")),
        ("Clã", clan.get("name", "Sem clã")),
        ("Tag do Clã", clan.get("tag", "")),
        ("Cargo no Clã", player.get("role", "")),
        ("Doações", player.get("donations", "")),
        ("Doações Recebidas", player.get("donationsReceived", "")),
        ("Vitórias em Guerra", player.get("warDayWins", "")),
        ("Cartas Coletadas (Clã)", player.get("clanCardsCollected", "")),
        ("Temporada Atual - Troféus", cur_season.get("trophies", "")),
        ("Temporada Atual - Melhor", cur_season.get("bestTrophies", "")),
        ("Temporada Anterior - ID", prev_season.get("id", "")),
        ("Temporada Anterior - Troféus", prev_season.get("trophies", "")),
        ("Temporada Anterior - Melhor", prev_season.get("bestTrophies", "")),
        ("Melhor Temporada - ID", best_season.get("id", "")),
        ("Melhor Temporada - Troféus", best_season.get("trophies", "")),
        ("Carta Favorita", fav_card.get("name", "")),
    ])

    _write_table_section(
        w, "DECK ATUAL",
        ["Slot", "Carta", "Nível", "Nível Máx.", "ID", "Elixir"],
        (
            [i, c.get("name", ""), c.get("level", ""), c.get("maxLevel", ""), c.get("id", ""), c.get("elixirCost", "")]
            for i, c in enumerate(player.get("currentDeck", []), 1)
        ),
    )

    _write_table_section(
        w, "COLEÇÃO DE CARTAS",
        ["Carta", "Nível", "Nível Máx.", "Quantidade", "Qtd. p/ Upgrade", "ID", "Elixir"],
        (
            [c.get("name", ""), c.get("level", ""), c.get("maxLevel", ""), c.get("count", ""),
             c.get("upgradeToNextLevel", ""), c.get("id", ""), c.get("elixirCost", "")]
            for c in player.get("cards", [])
        ),
    )

    _write_table_section(
        w, "CONQUISTAS (BADGES)",
        ["Nome", "Nível", "Progresso", "Progresso Máx.", "Target"],
        (
            [b.get("name", ""), b.get("level", ""), b.get("progress", ""), b.get("maxProgress", ""), b.get("target", "")]
            for b in player.get("badges", [])
        ),
    )

    def battle_rows():
        for b in battles:
            team_p = (b.get("team") or [{}])[0]
            opp_p = (b.get("opponent") or [{}])[0]
            my_c, op_c = team_p.get("crowns", 0), opp_p.get("crowns", 0)
            result = "Vitória" if my_c > op_c else "Derrota" if my_c < op_c else "Empate"

            def towers(p_data):
                towers_hp = p_data.get("princessTowersHitPoints") or []
                king = p_data.get("kingTowerHitPoints", "")
                princess = " / ".join(str(t) for t in towers_hp) if towers_hp else ""
                return king, princess

            my_king, my_princess = towers(team_p)
            op_king, op_princess = towers(opp_p)

            yield [
                fmt_date(b.get("battleTime", "")),
                b.get("type", ""),
                (b.get("gameMode") or {}).get("name", ""),
                (b.get("arena") or {}).get("name", ""),
                team_p.get("name", ""), team_p.get("tag", ""), team_p.get("startingTrophies", ""),
                my_c, my_king, my_princess, cards_str(team_p.get("cards", [])),
                opp_p.get("name", ""), opp_p.get("tag", ""), opp_p.get("startingTrophies", ""),
                op_c, op_king, op_princess, cards_str(opp_p.get("cards", [])),
                result,
            ]

    _write_table_section(
        w, "HISTÓRICO DE BATALHAS",
        ["Data", "Tipo", "Modo de Jogo", "Arena",
         "Jogador (Time)", "Tag (Time)", "Troféus (Time)", "Coroas (Time)", "King HP (Time)", "Princess HP (Time)", "Deck Usado (Time)",
         "Oponente", "Tag (Oponente)", "Troféus (Oponente)", "Coroas (Oponente)", "King HP (Oponente)", "Princess HP (Oponente)", "Deck Usado (Oponente)",
         "Resultado"],
        battle_rows(),
    )

    return _to_csv_response_text(output)


# ───────────────────────────────── CLÃ ─────────────────────────────────

ROLES = {"leader": "Líder", "coLeader": "Co-Líder", "elder": "Ancião", "member": "Membro"}
CLAN_TYPE_LABELS = {"open": "Aberto", "inviteOnly": "Apenas Convite", "closed": "Fechado"}


def build_clan_csv(clan: dict, members: list, warlog: list) -> str:
    output = io.StringIO()
    w = csv.writer(output)
    location = clan.get("location") or {}

    _write_kv_section(w, "INFORMAÇÕES DO CLÃ", [
        ("Nome", clan.get("name", "")),
        ("Tag", clan.get("tag", "")),
        ("Descrição", clan.get("description", "")),
        ("Tipo", CLAN_TYPE_LABELS.get(clan.get("type", ""), clan.get("type", ""))),
        ("Pontuação do Clã", clan.get("clanScore", "")),
        ("Troféus de Guerra", clan.get("clanWarTrophies", "")),
        ("Membros", clan.get("members", "")),
        ("Doações/Semana", clan.get("donationsPerWeek", "")),
        ("Troféus Mínimos", clan.get("requiredTrophies", "")),
        ("Localização", location.get("name", "")),
        ("País", location.get("countryCode", "")),
        ("ID Localização", location.get("id", "")),
        ("Tag do Badge", clan.get("badgeId", "")),
    ])

    def member_rows():
        for i, m in enumerate(members, 1):
            arena = (m.get("arena") or {}).get("name", "")
            yield [
                i, m.get("name", ""), m.get("tag", ""), ROLES.get(m.get("role", ""), m.get("role", "")),
                m.get("expLevel", ""), m.get("trophies", ""), m.get("bestTrophies", ""), arena,
                m.get("clanRank", ""), m.get("previousClanRank", ""),
                m.get("donations", ""), m.get("donationsReceived", ""),
                fmt_date(m.get("lastSeen", "")) if m.get("lastSeen") else "",
            ]

    _write_table_section(
        w, "MEMBROS ATUAIS",
        ["#", "Nome", "Tag", "Cargo", "Nível Exp.", "Troféus", "Melhor Troféus", "Arena",
         "Rank no Clã", "Rank Anterior no Clã", "Doações", "Doações Recebidas", "Último Online"],
        member_rows(),
    )

    def war_summary_rows():
        for i, race in enumerate(warlog, 1):
            standings = sorted(race.get("standings", []), key=lambda x: x.get("rank", 99))
            our = next((s for s in standings if s.get("clan", {}).get("tag") == clan.get("tag")), None)
            our_clan = our.get("clan", {}) if our else {}

            def sname(idx):
                return standings[idx].get("clan", {}).get("name", "") if idx < len(standings) else ""

            def sfame(idx):
                return standings[idx].get("clan", {}).get("fame", "") if idx < len(standings) else ""

            yield [
                race.get("seasonId", i), race.get("sectionIndex", ""),
                our.get("rank", "") if our else "",
                our_clan.get("fame", ""), our_clan.get("repairPoints", ""),
                len(our_clan.get("participants", [])),
                sname(0), sfame(0), sname(1), sfame(1), sname(2), sfame(2), sname(3), sfame(3), sname(4), sfame(4),
            ]

    _write_table_section(
        w, "HISTÓRICO DE GUERRAS — RESUMO",
        ["Temporada", "Seção", "Posição do Clã", "Fama", "Reparos", "Participantes",
         "1º Lugar", "Fama 1º", "2º Lugar", "Fama 2º", "3º Lugar", "Fama 3º", "4º Lugar", "Fama 4º", "5º Lugar", "Fama 5º"],
        war_summary_rows(),
    )

    def war_participant_rows():
        for i, race in enumerate(warlog, 1):
            standings = sorted(race.get("standings", []), key=lambda x: x.get("rank", 99))
            our = next((s for s in standings if s.get("clan", {}).get("tag") == clan.get("tag")), None)
            our_clan = our.get("clan", {}) if our else {}
            our_rank = our.get("rank", "") if our else ""
            for p in our_clan.get("participants", []):
                yield [
                    race.get("seasonId", i), race.get("sectionIndex", ""), our_rank,
                    p.get("name", ""), p.get("tag", ""), p.get("fame", ""), p.get("repairPoints", ""),
                    p.get("boatAttacks", ""), p.get("decksUsedToday", ""),
                    p.get("decksUsed", ""), p.get("decksUsedTotal", ""),
                ]

    _write_table_section(
        w, "HISTÓRICO DE GUERRAS — PARTICIPANTES INDIVIDUAIS",
        ["Temporada", "Seção", "Posição do Clã", "Nome do Jogador", "Tag do Jogador",
         "Fama", "Reparos", "Batalhas no Barco", "Ataques Restantes", "Decks Usados", "Decks na Semana"],
        war_participant_rows(),
    )

    return _to_csv_response_text(output)
