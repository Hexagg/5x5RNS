import sqlite3

def seed_data():
    conn = sqlite3.connect('lol_teams.db')
    cursor = conn.cursor()

    # Очищаем таблицы перед заполнением
    cursor.execute('DELETE FROM player_roles')
    cursor.execute('DELETE FROM player_champions')
    cursor.execute('DELETE FROM players')

    # Список игроков: (имя, тир, победы, поражения)
    players = [
        ('Андудгеанге', 'SSS', 4, 2),
        ('Андрей Носков', 'SSS', 2, 5),
        ('Максончик', 'SS', 6, 2),
        ('Мемо', 'SS', 3, 3),
        ('Жираф', 'S', 3, 1),
        ('Мопс', 'S', 0, 0),  # нет данных, винрейт будет 50% при расчёте
        ('Гошанчик', 'A', 2, 0),
        ('Никита Горилла', 'A', 4, 4),
        ('Артём Пипиев', 'B', 2, 4),
        ('Андрей Деев', 'B', 1, 7),
        ('Никита Некрасов', 'B', 1, 0),
        ('Олег Крюков', 'B', 0, 1),
        ('Кирюха Борода', 'C', 2, 4),
        ('Хозяйка Клоуна', 'C', 2, 0),
        ('Славянка', 'C', 4, 2),
        ('Андрей Усач', 'D', 2, 5),
        ('Валерыч', 'D', 1, 1),
        ('Ксюха', 'D', 0, 0),  # нет данных, винрейт будет 50% при расчёте
    ]

    for name, tier, wins, losses in players:
        total_games = wins + losses
        cursor.execute('''
            INSERT INTO players (name, global_tier, total_games, total_wins)
            VALUES (?, ?, ?, ?)
        ''', (name, tier, total_games, wins))

    # Получаем id всех ролей
    cursor.execute('SELECT id, name FROM roles')
    roles = cursor.fetchall()
    role_dict = {name: id for id, name in roles}

    # Баллы по ролям: (имя, Top, Jungle, Mid, ADC, Support)
    scores = [
        ('Андудгеанге', 7, 7, 7, 5, 3),
        ('Андрей Носков', 5, 7, 5, 7, 3),
        ('Максончик', 4, 4, 6, 5, 7),
        ('Мемо', 6, 5, 4, 4, 3),
        ('Жираф', 4, 4, 6, 4, 2),
        ('Мопс', 6, 3, 4, 4, 5),
        ('Гошанчик', 3, 3, 4, 2, 2),
        ('Никита Горилла', 2, 1, 4, 3, 3),
        ('Артём Пипиев', 3, 1, 3, 3, 3),
        ('Андрей Деев', 1, 4, 3, 3, 4),
        ('Никита Некрасов', 2, 1, 3, 4, 2),
        ('Олег Крюков', 3, 3, 2, 1, 3),
        ('Кирюха Борода', 3, 1, 2, 3, 2),
        ('Хозяйка Клоуна', 0, 0, 2, 3, 4),  # прочерки = 0
        ('Славянка', 3, 1, 2, 3, 2),
        ('Андрей Усач', 1, 1, 1, 1, 2),
        ('Валерыч', 1, 1, 1, 1, 1),
        ('Ксюха', 1, 1, 1, 1, 1),
    ]

    role_names = ['Top', 'Jungle', 'Mid', 'ADC', 'Support']

    for row in scores:
        player_name = row[0]
        player_scores = row[1:]
        cursor.execute('SELECT id FROM players WHERE name = ?', (player_name,))
        player_id = cursor.fetchone()[0]

        for i, role_name in enumerate(role_names):
            score = player_scores[i]
            role_id = role_dict[role_name]
            cursor.execute('''
                INSERT INTO player_roles (player_id, role_id, score, is_banned, is_priority)
                VALUES (?, ?, ?, 0, 0)
            ''', (player_id, role_id, score))

    # Запреты на роли (только для тех, у кого явно указано, кроме ОТП)
    # Андудгеанге: Лес, Топ
    # Андрей Носков: Лес, АДК
    role_bans = [
        ('Андудгеанге', 'Jungle'),
        ('Андудгеанге', 'Top'),
        ('Андрей Носков', 'Jungle'),
        ('Андрей Носков', 'ADC'),
    ]

    for player_name, role_name in role_bans:
        cursor.execute('SELECT id FROM players WHERE name = ?', (player_name,))
        player_id = cursor.fetchone()[0]
        role_id = role_dict[role_name]
        cursor.execute('''
            UPDATE player_roles SET is_banned = 1
            WHERE player_id = ? AND role_id = ?
        ''', (player_id, role_id))

    # Вечные запреты на персонажей
    champion_bans = [
        ('Андудгеанге', ['Джин', 'Ривен', 'Ясуо', 'Зед', 'Вэйн', 'Дрэйвен', 'Афелий']),
        ('Андрей Носков', ['Ли Син', 'Джин', 'Ренгар', 'Грейвз', 'Гекарим', 'Виего', 'Катарина']),
        ('Максончик', ['Пайк', 'Пантеон', 'БЦ', 'Дариус', 'Сайлас']),
        ('Мемо', ['Рек’Сай', 'Ривен', 'Зед', 'Азир', 'Акали']),
        ('Жираф', ['Райз', 'Джейс', 'Атрокс']),
        ('Мопс', ['Атрокс', 'Пайк', 'Мордекайзер']),
    ]

    for player_name, champs in champion_bans:
        cursor.execute('SELECT id FROM players WHERE name = ?', (player_name,))
        player_id = cursor.fetchone()[0]
        for champ in champs:
            cursor.execute('''
                INSERT OR IGNORE INTO player_champions (player_id, champion_name)
                VALUES (?, ?)
            ''', (player_id, champ))

    conn.commit()
    conn.close()
    print("База данных заполнена 18 игроками, баллами, винрейтом и запретами.")

if __name__ == '__main__':
    seed_data()