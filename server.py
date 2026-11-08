from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List, Optional
import itertools
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

def get_db():
    conn = sqlite3.connect('lol_teams.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Модели данных ---

class PlayerUpdate(BaseModel):
    name: str
    global_tier: Optional[str] = None
    scores: Optional[dict] = None
    bans: Optional[dict] = None
    priority_role: Optional[str] = None
    champion_bans: Optional[List[str]] = None
    is_active_session: Optional[int] = None

class AutoRequest(BaseModel):
    names: List[str]

# --- Эндпоинты ---

@app.get("/api/players")
def get_players():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, global_tier, total_games, total_wins, is_active_session
        FROM players
        ORDER BY
            CASE global_tier
                WHEN 'SSS' THEN 1
                WHEN 'SS' THEN 2
                WHEN 'S' THEN 3
                WHEN 'A' THEN 4
                WHEN 'B' THEN 5
                WHEN 'C' THEN 6
                WHEN 'D' THEN 7
                ELSE 8
            END,
            name
    ''')
    players = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return players

@app.get("/api/player/{player_id}")
def get_player(player_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, global_tier, total_games, total_wins, is_active_session FROM players WHERE id = ?', (player_id,))
    player = cursor.fetchone()
    if not player:
        conn.close()
        raise HTTPException(status_code=404, detail="Игрок не найден")

    player_dict = dict(player)

    cursor.execute('''
        SELECT r.name, pr.score, pr.is_banned, pr.is_priority
        FROM player_roles pr
        JOIN roles r ON pr.role_id = r.id
        WHERE pr.player_id = ?
    ''', (player_id,))
    roles_data = {}
    for row in cursor.fetchall():
        roles_data[row['name']] = {
            'score': row['score'],
            'is_banned': row['is_banned'],
            'is_priority': row['is_priority']
        }

    cursor.execute('SELECT champion_name FROM player_champions WHERE player_id = ?', (player_id,))
    champs = [row['champion_name'] for row in cursor.fetchall()]

    conn.close()
    return {
        'id': player_dict['id'],
        'name': player_dict['name'],
        'global_tier': player_dict['global_tier'],
        'total_games': player_dict['total_games'],
        'total_wins': player_dict['total_wins'],
        'is_active_session': player_dict['is_active_session'],
        'roles': roles_data,
        'champion_bans': champs
    }
@app.post("/api/player/{player_id}")
def update_player(player_id: int, data: PlayerUpdate):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM players WHERE id = ?', (player_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Игрок не найден")

    if data.global_tier:
        cursor.execute('UPDATE players SET global_tier = ? WHERE id = ?', (data.global_tier, player_id))

    if data.is_active_session is not None:
        cursor.execute('UPDATE players SET is_active_session = ? WHERE id = ?', (data.is_active_session, player_id))

    if data.scores or data.bans:
        cursor.execute('SELECT id, name FROM roles')
        role_map = {row['name']: row['id'] for row in cursor.fetchall()}
        for role_name, score in (data.scores or {}).items():
            if role_name in role_map:
                cursor.execute('UPDATE player_roles SET score = ? WHERE player_id = ? AND role_id = ?', (score, player_id, role_map[role_name]))
        for role_name, ban in (data.bans or {}).items():
            if role_name in role_map:
                cursor.execute('UPDATE player_roles SET is_banned = ? WHERE player_id = ? AND role_id = ?', (ban, player_id, role_map[role_name]))

    if data.priority_role is not None:
        cursor.execute('SELECT id FROM roles WHERE name = ?', (data.priority_role,))
        row = cursor.fetchone()
        if row:
            role_id = row['id']
            cursor.execute('UPDATE player_roles SET is_priority = 0 WHERE player_id = ?', (player_id,))
            cursor.execute('UPDATE player_roles SET is_priority = 1 WHERE player_id = ? AND role_id = ?', (player_id, role_id))

    if data.champion_bans is not None:
        cursor.execute('DELETE FROM player_champions WHERE player_id = ?', (player_id,))
        for champ in data.champion_bans:
            cursor.execute('INSERT INTO player_champions (player_id, champion_name) VALUES (?, ?)', (player_id, champ))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Данные игрока обновлены"}

@app.get("/api/roles")
def get_roles():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM roles ORDER BY id')
    roles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return roles

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Сервер работает"}

@app.post("/api/auto")
def auto_team(req: AutoRequest):
    if len(req.names) != 5:
        return {"error": f"Нужно ровно 5 игроков, а указано {len(req.names)}."}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT value FROM settings WHERE key = "max_score_threshold"')
    row = cursor.fetchone()
    MAX_SCORE_THRESHOLD = int(row['value']) if row else 30

    players_data = []
    for name in req.names:
        cursor.execute('SELECT id, name, global_tier FROM players WHERE name = ? AND is_active_session = 1', (name,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"error": f"Игрок '{name}' не найден или не активен."}
        players_data.append((row['id'], row['name'], row['global_tier']))

    sss = sum(1 for _, _, t in players_data if t == 'SSS')
    ss = sum(1 for _, _, t in players_data if t == 'SS')
    if sss > 1:
        conn.close()
        return {"error": "Больше одного игрока SSS!"}
    if ss > 1:
        conn.close()
        return {"error": "Больше одного игрока SS!"}

    cursor.execute('SELECT id, name FROM roles ORDER BY id')
    roles = cursor.fetchall()
    role_ids = [r['id'] for r in roles]
    role_names = [r['name'] for r in roles]

    player_role_data = {}
    for pid, _, _ in players_data:
        player_role_data[pid] = {}
        cursor.execute('SELECT role_id, score, is_banned FROM         player_roles WHERE player_id = ?', (pid,))
        rows = cursor.fetchall()
        cursor.execute('SELECT total_games, total_wins FROM         players WHERE id = ?', (pid,))
        tg, tw = cursor.fetchone()
        winrate = 50 if tg == 0 else (tw / tg) * 100
        for row in rows:
            adjusted = row['score']
            if winrate <= 35:
                adjusted -= 1
            elif winrate >= 70:
                adjusted += 1
            player_role_data[pid][row['role_id']] = {
                'adjusted': adjusted,
                'base': row['score'],
                'is_banned': row['is_banned']
            }

 # Проверка истории: две игры подряд на одной роли
    role_history = {}
    for pid, _, _ in players_data:
        cursor.execute('''
            SELECT role_id FROM game_players
            WHERE player_id = ?
            ORDER BY game_id DESC
            LIMIT 2
        ''', (pid,))
        last_roles = [row['role_id'] for row in cursor.fetchall()]
        if len(last_roles) == 2 and last_roles[0] == last_roles[1]:
            role_history[pid] = last_roles[0]

    # Чтение фиксаций SSS из драфта
    fixed_roles = {}
    fixed_champions = {}
    for pid, _, _ in players_data:
        cursor.execute('SELECT fixed_role_id, fixed_champion, is_random_sss FROM draft WHERE player_id = ?', (pid,))
        row = cursor.fetchone()
        if row and row['is_random_sss'] == 1 and row['fixed_role_id']:
            fixed_roles[pid] = row['fixed_role_id']
            fixed_champions[pid] = row['fixed_champion']
    print("=== DEBUG ===")
    for pid, name, tier in players_data:
        if name == "Андрей Носков":
            print(f"Игрок: {name}, pid={pid}")
            print(f"  fixed_roles: {fixed_roles.get(pid)}")
            print(f"  role_history: {role_history.get(pid)}")
            for rid, data in player_role_data[pid].items():
                print(f"  role_id={rid}, adjusted={data['adjusted']}, base={data['base']}")

    best_variants = []
    for perm in itertools.permutations(players_data):
        total = 0
        valid = True
        for i, (pid, name, tier) in enumerate(perm):
            rid = role_ids[i]
            if rid not in player_role_data[pid]:
                valid = False
                break
            data = player_role_data[pid][rid]
            if data['is_banned']:
                valid = False
                break
            if role_history.get(pid) == rid:
                valid = False
                break
            # Проверка фиксации SSS
            if pid in fixed_roles:
                if rid != fixed_roles[pid]:
                    valid = False
                    break
                total += data['adjusted'] - 2  # стоимость -2 за рандом
            else:
                total += data['adjusted']
        if valid and total <= MAX_SCORE_THRESHOLD:
            best_variants.append((total, perm))

    conn.close()

    if not best_variants:
        return {"error": "Нет вариантов в пределах порога."}

    best_variants.sort(key=lambda x: x[0], reverse=True)  # по убыванию
    top = best_variants[:15]

    result = []
    for total, perm in top:
        roles_list = []
        for i, (pid, name, tier) in enumerate(perm):
            data = player_role_data[pid][role_ids[i]]
            score = data['adjusted']
            if pid in fixed_roles:
                score -= 2
            roles_list.append({
                "role": role_names[i],
                "name": name,
                "tier": tier,
                "score": score,
                "base_score": data['base']
            })
        result.append({"total_score": total, "roles": roles_list})

    return {"variants": result}

class PickRequest(BaseModel):
    player_id: int
    team: int  # 1 или 2

@app.post("/api/draft/pick")
def draft_pick(req: PickRequest):
    conn = get_db()
    cursor = conn.cursor()

    # Проверяем, что игрок ещё не выбран
    cursor.execute('SELECT id FROM draft WHERE player_id = ?', (req.player_id,))
    if cursor.fetchone():
        conn.close()
        return {"error": "Этот игрок уже выбран."}

    # Проверяем, что в команде ещё меньше 5 игроков
    cursor.execute('SELECT COUNT(*) as cnt FROM draft WHERE team = ?', (req.team,))
    count = cursor.fetchone()['cnt']
    if count >= 5:
        conn.close()
        return {"error": f"В команде {req.team} уже 5 игроков."}

    # Проверяем, что в команде нет двух SSS или двух SS
    cursor.execute('''
        SELECT p.global_tier, COUNT(*) as cnt
        FROM draft d
        JOIN players p ON d.player_id = p.id
        WHERE d.team = ? AND p.global_tier IN ('SSS', 'SS')
        GROUP BY p.global_tier
    ''', (req.team,))
    tier_counts = {row['global_tier']: row['cnt'] for row in cursor.fetchall()}

    # Получаем тир нового игрока
    cursor.execute('SELECT global_tier FROM players WHERE id = ?', (req.player_id,))
    new_tier = cursor.fetchone()['global_tier']

    if new_tier == 'SSS' and tier_counts.get('SSS', 0) >= 1:
        conn.close()
        return {"error": "В команде уже есть игрок SSS. Нельзя брать второго."}
    if new_tier == 'SS' and tier_counts.get('SS', 0) >= 1:
        conn.close()
        return {"error": "В команде уже есть игрок SS. Нельзя брать второго."}
     # Проверяем, чей сейчас ход
    cursor.execute('SELECT turn FROM draft_state WHERE id = 1')
    current_turn = cursor.fetchone()['turn']
    if current_turn != req.team:
        conn.close()
        return {"error": f"Сейчас ход команды {current_turn}. Подожди."}
    # Добавляем пик
    cursor.execute('SELECT COALESCE(MAX(pick_order), 0) + 1 as next_order FROM draft')
    next_order = cursor.fetchone()['next_order']
    cursor.execute('INSERT INTO draft (player_id, team, pick_order) VALUES (?, ?, ?)', (req.player_id, req.team, next_order))
    conn.commit()
    cursor.execute('UPDATE draft_state SET turn = ? WHERE id = 1', (2 if req.team == 1 else 1,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/draft/state")
def draft_state():
    conn = get_db()
    cursor = conn.cursor()

    # Все выбранные игроки
    cursor.execute('''
        SELECT d.id, d.player_id, d.team, d.pick_order, p.name, p.global_tier,
               d.fixed_role_id, d.fixed_champion, d.is_random_sss
        FROM draft d
        JOIN players p ON d.player_id = p.id
        ORDER BY d.pick_order
    ''')
    picked = [dict(row) for row in cursor.fetchall()]

    # Все активные игроки, которые ещё не выбраны
    cursor.execute('''
        SELECT id, name, global_tier
        FROM players
        WHERE is_active_session = 1
        AND id NOT IN (SELECT player_id FROM draft)
        ORDER BY global_tier DESC, name
    ''')
    available = [dict(row) for row in cursor.fetchall()]
    cursor.execute('SELECT turn FROM draft_state WHERE id = 1')
    turn = cursor.fetchone()['turn']
    conn.close()
    return {"picked": picked, "available": available, "turn": turn}

@app.post("/api/draft/reset")
def draft_reset():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM draft')
    cursor.execute('DELETE FROM draft_roles')
    cursor.execute('UPDATE draft_state SET turn = 1 WHERE id = 1')
    cursor.execute('UPDATE captain_ready SET ready = 0')
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES ("game_finished", "0")')
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Драфт сброшен."}

class RandomSSSRequest(BaseModel):
    player_id: int
    team: int
    role_name: str
    champion_name: str

@app.post("/api/draft/random_sss")
def draft_random_sss(req: RandomSSSRequest):
    conn = get_db()
    cursor = conn.cursor()

    # Проверяем, что игрок есть в драфте и в этой команде
    cursor.execute('SELECT id, team FROM draft WHERE player_id = ?', (req.player_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": "Игрок не найден в драфте."}
    if row['team'] != req.team:
        conn.close()
        return {"error": "Игрок в другой команде."}

    # Проверяем, что игрок SSS
    cursor.execute('SELECT global_tier FROM players WHERE id = ?', (req.player_id,))
    tier = cursor.fetchone()['global_tier']
    if tier != 'SSS':
        conn.close()
        return {"error": "Рандом доступен только для SSS."}

    # Проверяем роль
    cursor.execute('SELECT id FROM roles WHERE name = ?', (req.role_name,))
    role_row = cursor.fetchone()
    if not role_row:
        conn.close()
        return {"error": "Роль не найдена."}
    role_id = role_row['id']

    # Проверяем запрет на роль
    cursor.execute('SELECT is_banned FROM player_roles WHERE player_id = ? AND role_id = ?', (req.player_id, role_id))
    ban_row = cursor.fetchone()
    if ban_row and ban_row['is_banned']:
        conn.close()
        return {"error": "Эта роль запрещена для игрока."}

    # Проверяем запрет на персонажа (вечный)
    cursor.execute('SELECT 1 FROM player_champions WHERE player_id = ? AND champion_name = ?', (req.player_id, req.champion_name))
    if cursor.fetchone():
        conn.close()
        return {"error": "Этот персонаж запрещён для игрока."}

    # Сохраняем фиксацию
    cursor.execute('UPDATE draft SET fixed_role_id = ?, fixed_champion = ?, is_random_sss = 1 WHERE player_id = ?', (role_id, req.champion_name, req.player_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/draft/team_score/{team}")
def team_score(team: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT dr.player_id, dr.role_id, pr.score, p.total_games, p.total_wins,
               d.is_random_sss, d.fixed_role_id
        FROM draft_roles dr
        JOIN players p ON dr.player_id = p.id
        JOIN player_roles pr ON pr.player_id = dr.player_id AND pr.role_id = dr.role_id
        LEFT JOIN draft d ON d.player_id = dr.player_id
        WHERE dr.team = ?
    ''', (team,))

    total = 0
    details = []
    for row in cursor.fetchall():
        score = row['score']
        tg = row['total_games']
        tw = row['total_wins']
        winrate = 50 if tg == 0 else (tw / tg) * 100
        if winrate <= 35:
            score -= 1
        elif winrate >= 70:
            score += 1
        if row['is_random_sss'] == 1 and row['fixed_role_id'] == row['role_id']:
            score -= 2
        total += score
        details.append({'player_id': row['player_id'], 'role_id': row['role_id'], 'score': score})

    conn.close()
    return {'total': total, 'details': details}

class TeamBansRequest(BaseModel):
    team: int
    champions: List[str]

@app.post("/api/draft/bans")
def save_bans(req: TeamBansRequest):
    conn = get_db()
    cursor = conn.cursor()

    if len(req.champions) != 2:
        conn.close()
        return {"error": "Нужно ровно 2 героя."}

    # Очищаем старые запреты для этой команды
    cursor.execute('DELETE FROM game_bans WHERE team = ?', (req.team,))
    for champ in req.champions:
        cursor.execute('INSERT INTO game_bans (game_id, team, champion_name) VALUES (0, ?, ?)', (req.team, champ))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Запреты сохранены."}

@app.get("/api/draft/bans")
def get_bans():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT team, champion_name FROM game_bans')
    rows = cursor.fetchall()
    result = {1: [], 2: []}
    for row in rows:
        result[row['team']].append(row['champion_name'])
    conn.close()
    return result

class RoleAssignment(BaseModel):
    team: int
    assignments: dict  # {"player_id": role_id, ...}

@app.post("/api/draft/roles")
def save_roles(req: RoleAssignment):
    conn = get_db()
    cursor = conn.cursor()

    # Проверяем, что в команде 5 игроков
    cursor.execute('SELECT COUNT(*) as cnt FROM draft WHERE team = ?', (req.team,))
    count = cursor.fetchone()['cnt']
    if count != 5:
        conn.close()
        return {"error": f"В команде {req.team} должно быть 5 игроков, а сейчас {count}."}

    # Проверяем, что все player_id из assignments есть в этой команде
    for pid_str, role_id in req.assignments.items():
        pid = int(pid_str)
        cursor.execute('SELECT id FROM draft WHERE player_id = ? AND team = ?', (pid, req.team))
        if not cursor.fetchone():
            conn.close()
            return {"error": f"Игрок {pid} не найден в команде {req.team}."}
        # Проверяем, что роль существует
        cursor.execute('SELECT id FROM roles WHERE id = ?', (role_id,))
        if not cursor.fetchone():
            conn.close()
            return {"error": f"Роль {role_id} не найдена."}

    # Сохраняем распределение (пока в отдельную таблицу draft_roles)
    cursor.execute('DELETE FROM draft_roles WHERE team = ?', (req.team,))
    for pid_str, role_id in req.assignments.items():
        pid = int(pid_str)
        cursor.execute('INSERT INTO draft_roles (team, player_id, role_id) VALUES (?, ?, ?)', (req.team, pid, role_id))

    # Проверяем сумму с учётом порога
    cursor.execute('SELECT value FROM settings WHERE key = "max_score_threshold"')
    row = cursor.fetchone()
    max_threshold = int(row['value']) if row else 30

    cursor.execute('''
        SELECT dr.player_id, dr.role_id, pr.score, p.total_games, p.total_wins,
               d.is_random_sss, d.fixed_role_id
        FROM draft_roles dr
        JOIN players p ON dr.player_id = p.id
        JOIN player_roles pr ON pr.player_id = dr.player_id AND pr.role_id = dr.role_id
        LEFT JOIN draft d ON d.player_id = dr.player_id
        WHERE dr.team = ?
    ''', (req.team,))

    total = 0
    for row in cursor.fetchall():
        score = row['score']
        tg = row['total_games']
        tw = row['total_wins']
        winrate = 50 if tg == 0 else (tw / tg) * 100
        if winrate <= 35:
            score -= 1
        elif winrate >= 70:
            score += 1
        if row['is_random_sss'] == 1 and row['fixed_role_id'] == row['role_id']:
            score -= 2
        total += score

    if total > max_threshold:
        conn.rollback()
        conn.close()
        return {"error": f"Сумма команды {total} превышает порог {max_threshold}. Попробуйте другую расстановку."}

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Распределение сохранено."}

@app.get("/api/draft/roles")
def get_roles_assignment():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT dr.team, dr.player_id, p.name, p.global_tier, dr.role_id, r.name as role_name
        FROM draft_roles dr
        JOIN players p ON dr.player_id = p.id
        JOIN roles r ON dr.role_id = r.id
        ORDER BY dr.team, dr.player_id
    ''')
    rows = [dict(row) for row in cursor.fetchall()]

    result = {1: [], 2: []}
    for row in rows:
        # Получаем балл игрока на этой роли
        cursor.execute('SELECT score FROM player_roles WHERE player_id = ? AND role_id = ?', (row['player_id'], row['role_id']))
        score_row = cursor.fetchone()
        score = score_row['score'] if score_row else 0

        result[row['team']].append({
            'player_id': row['player_id'],
            'name': row['name'],
            'tier': row['global_tier'],
            'role_id': row['role_id'],
            'role_name': row['role_name'],
            'score': score
        })

    conn.close()
    return result

class SettingsUpdate(BaseModel):
    max_score_threshold: int

@app.get("/api/settings")
def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = "max_score_threshold"')
    row = cursor.fetchone()
    conn.close()
    return {"max_score_threshold": int(row['value']) if row else 30}

@app.post("/api/settings")
def update_settings(req: SettingsUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES ("max_score_threshold", ?)', (str(req.max_score_threshold),))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Настройки сохранены."}

@app.get("/api/player/{player_id}/role_history")
def get_role_history(player_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role_id FROM game_players
        WHERE player_id = ?
        ORDER BY game_id DESC
        LIMIT 2
    ''', (player_id,))
    last_roles = [row['role_id'] for row in cursor.fetchall()]
    conn.close()

    blocked_role_id = None
    if len(last_roles) == 2 and last_roles[0] == last_roles[1]:
        blocked_role_id = last_roles[0]

    return {"blocked_role_id": blocked_role_id}

class FinishGameRequest(BaseModel):
    winner_team: int
    champions: dict  # {"player_id": "champion_name", ...}

@app.post("/api/draft/finish")
def finish_game(req: FinishGameRequest):
    conn = get_db()
    cursor = conn.cursor()

    # Проверяем, что в обеих командах по 5 игроков
    cursor.execute('SELECT team, player_id, role_id FROM draft_roles')
    roles_rows = cursor.fetchall()
    team1 = [r for r in roles_rows if r['team'] == 1]
    team2 = [r for r in roles_rows if r['team'] == 2]

    if len(team1) != 5 or len(team2) != 5:
        conn.close()
        return {"error": "Обе команды должны быть распределены по ролям."}

    if req.winner_team not in (1, 2):
        conn.close()
        return {"error": "Победитель должен быть 1 или 2."}

    # Создаём игру
    import datetime
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    cursor.execute('INSERT INTO games (date, winner_team) VALUES (?, ?)', (date, req.winner_team))
    game_id = cursor.lastrowid

    # Записываем игроков и обновляем статистику
    for row in roles_rows:
        pid = row['player_id']
        champion = req.champions.get(str(pid), '')
        cursor.execute('''
            INSERT INTO game_players (game_id, player_id, team, role_id, champion_name, is_random_sss)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (game_id, pid, row['team'], row['role_id'], champion))

        if row['team'] == req.winner_team:
            cursor.execute('UPDATE players SET total_games = total_games + 1, total_wins = total_wins + 1 WHERE id = ?', (pid,))
        else:
            cursor.execute('UPDATE players SET total_games = total_games + 1 WHERE id = ?', (pid,))

    # Сохраняем антибаны в game_bans для этой игры
    cursor.execute('SELECT team, champion_name FROM game_bans WHERE game_id = 0')
    for row in cursor.fetchall():
        cursor.execute('INSERT INTO game_bans (game_id, team, champion_name) VALUES (?, ?, ?)', (game_id, row['team'], row['champion_name']))

    # Очищаем драфт
    cursor.execute('DELETE FROM draft')
    cursor.execute('DELETE FROM draft_roles')
    cursor.execute('DELETE FROM game_bans WHERE game_id = 0')
    cursor.execute('UPDATE draft_state SET turn = 1 WHERE id = 1')
    cursor.execute('UPDATE captain_ready SET ready = 0')
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES ("game_finished", "1")')

    conn.commit()
    conn.close()
    return {"status": "ok", "game_id": game_id, "message": "Игра завершена."}

@app.get("/api/player/{player_id}/champion_history")
def get_champion_history(player_id: int, role_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT champion_name FROM game_players
        WHERE player_id = ? AND role_id = ?
        ORDER BY game_id DESC
        LIMIT 2
    ''', (player_id, role_id))
    last_champs = [row['champion_name'] for row in cursor.fetchall()]
    conn.close()

    blocked_champion = None
    if len(last_champs) == 2 and last_champs[0] == last_champs[1] and last_champs[0]:
        blocked_champion = last_champs[0]

    return {"blocked_champion": blocked_champion}

class CaptainReadyRequest(BaseModel):
    team: int
    ready: int

@app.post("/api/captain/ready")
def set_captain_ready(req: CaptainReadyRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE captain_ready SET ready = ? WHERE team = ?', (req.ready, req.team))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/captain/ready")
def get_captain_ready():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT team, ready FROM captain_ready')
    rows = cursor.fetchall()
    result = {1: 0, 2: 0}
    for row in rows:
        result[row['team']] = row['ready']
    conn.close()
    return result

@app.get("/api/game_finished")
def get_game_finished():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = "game_finished"')
    row = cursor.fetchone()
    conn.close()
    return {"finished": int(row['value']) if row else 0}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)