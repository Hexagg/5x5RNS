import sqlite3

def create_database():
    conn = sqlite3.connect('lol_teams.db')
    cursor = conn.cursor()

    # Таблица игроков
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        global_tier TEXT NOT NULL,
        total_games INTEGER DEFAULT 0,
        total_wins INTEGER DEFAULT 0
    )
    ''')

    # Таблица ролей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    ''')

    # Оценки и запреты по ролям
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_roles (
        player_id INTEGER,
        role_id INTEGER,
        score INTEGER NOT NULL,
        is_banned INTEGER DEFAULT 0,
        is_priority INTEGER DEFAULT 0,
        PRIMARY KEY (player_id, role_id),
        FOREIGN KEY (player_id) REFERENCES players (id),
        FOREIGN KEY (role_id) REFERENCES roles (id)
    )
    ''')

    # Вечные запреты на персонажей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_champions (
        player_id INTEGER,
        champion_name TEXT NOT NULL,
        PRIMARY KEY (player_id, champion_name),
        FOREIGN KEY (player_id) REFERENCES players (id)
    )
    ''')

    # Игры
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        team1_score INTEGER,
        team2_score INTEGER,
        winner_team INTEGER,
        max_score_threshold INTEGER
    )
    ''')

    # Кто где играл
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_players (
        game_id INTEGER,
        player_id INTEGER,
        team INTEGER,
        role_id INTEGER,
        champion_name TEXT,
        is_random_sss INTEGER DEFAULT 0,
        PRIMARY KEY (game_id, player_id),
        FOREIGN KEY (game_id) REFERENCES games (id),
        FOREIGN KEY (player_id) REFERENCES players (id),
        FOREIGN KEY (role_id) REFERENCES roles (id)
    )
    ''')

    # Запреты на баны/пики для каждой игры
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_bans (
        game_id INTEGER,
        team INTEGER,
        champion_name TEXT,
        PRIMARY KEY (game_id, team, champion_name),
        FOREIGN KEY (game_id) REFERENCES games (id)
    )
    ''')

    # Заполняем роли, если их ещё нет
    roles = ['Top', 'Jungle', 'Mid', 'ADC', 'Support']
    for role in roles:
        cursor.execute('INSERT OR IGNORE INTO roles (name) VALUES (?)', (role,))

    conn.commit()
    conn.close()
    print("База данных 'lol_teams.db' успешно создана (или уже существует).")

if __name__ == '__main__':
    create_database()