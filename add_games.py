import sqlite3

def add_games():
    conn = sqlite3.connect('lol_teams.db')
    cursor = conn.cursor()

    # Получаем id игроков и ролей
    cursor.execute('SELECT id, name FROM players')
    players = {name: pid for pid, name in cursor.fetchall()}
    cursor.execute('SELECT id, name FROM roles')
    roles = {name: rid for rid, name in cursor.fetchall()}

    games = [
        {
            'date': '2026-11-02',
            'winner_team': 1,
            'teams': {
                1: [('Максончик', 'ADC', 'Кейтлин'), ('Славянка', 'Top', 'Мундо'), ('Андудгеанге', 'Jungle', 'Ли Син'), ('Гошанчик', 'Mid', 'Киана'), ('Хозяйка Клоуна', 'Support', 'Лулу')],
                2: [('Андрей Носков', 'Top', 'ГП'), ('Андрей Деев', 'Jungle', 'Ренгар'), ('Никита Горилла', 'Mid', 'Кассадин'), ('Кирюха Борода', 'ADC', 'Кай\'Са'), ('Андрей Усач', 'Support', 'Леона')]
            }
        },
        {
            'date': '2026-11-02',
            'winner_team': 2,
            'teams': {
                1: [('Максончик', 'Support', 'Пайк'), ('Андрей Усач', 'Top', 'Таам Кенч'), ('Андрей Деев', 'Jungle', 'Ренгар'), ('Никита Горилла', 'Mid', 'Кассадин'), ('Андрей Носков', 'ADC', 'Дрейвен')],
                2: [('Славянка', 'Top', 'Мордекайзер'), ('Андудгеанге', 'Jungle', 'Ривен'), ('Гошанчик', 'Mid', 'Киана'), ('Кирюха Борода', 'ADC', 'Тристана'), ('Хозяйка Клоуна', 'Support', 'Сорака')]
            }
        },
        {
            'date': '2026-11-05',
            'winner_team': 2,
            'teams': {
                1: [('Максончик', 'ADC', 'Кейтлин'), ('Валерыч', 'Top', 'Сетт'), ('Мемо', 'Jungle', 'Наафири'), ('Артём Пипиев', 'Mid', 'Орианна'), ('Андрей Усач', 'Support', 'Трэш')],
                2: [('Славянка', 'Top', 'Мундо'), ('Андудгеанге', 'Jungle', 'Бел\'Вет'), ('Андрей Деев', 'Mid', 'Ари'), ('Кирюха Борода', 'ADC', 'Зиггс'), ('Никита Горилла', 'Support', 'БЦ')]
            }
        },
        {
            'date': '2026-11-05',
            'winner_team': 1,
            'teams': {
                1: [('Максончик', 'ADC', 'Сайлас'), ('Валерыч', 'Top', 'Сетт'), ('Мемо', 'Jungle', 'Вуконг'), ('Артём Пипиев', 'Mid', 'ТФ'), ('Андрей Усач', 'Support', 'Трэш')],
                2: [('Славянка', 'Mid', 'Ари'), ('Андрей Носков', 'Top', 'Джейс'), ('Андрей Деев', 'Jungle', 'Зак'), ('Кирюха Борода', 'ADC', 'Мел'), ('Никита Горилла', 'Support', 'БЦ')]
            }
        },
        {
            'date': '2026-11-06',
            'winner_team': 1,
            'teams': {
                1: [('Максончик', 'Jungle', 'Виего'), ('Славянка', 'Top', 'Мордекайзер'), ('Мемо', 'Mid', 'Кассиопея'), ('Никита Горилла', 'ADC', 'Джин'), ('Андрей Носков', 'Support', 'Нами')],
                2: [('Андрей Усач', 'Top', 'Трэш'), ('Андрей Деев', 'Jungle', 'Атрокс'), ('Артём Пипиев', 'Mid', 'Мальзахар'), ('Жираф', 'ADC', 'Сивир'), ('Андудгеанге', 'Support', 'Юми')]
            }
        },
        {
            'date': '2026-11-06',
            'winner_team': 1,
            'teams': {
                1: [('Максончик', 'Mid', 'Сайлас'), ('Артём Пипиев', 'Top', 'Мордекайзер'), ('Жираф', 'Jungle', 'Джакс'), ('Андрей Усач', 'ADC', 'Эш'), ('Мемо', 'Support', 'Алистар')],
                2: [('Андрей Носков', 'Top', 'Сетт'), ('Андрей Деев', 'Jungle', 'Талон'), ('Славянка', 'Mid', 'Зиггс'), ('Кирюха Борода', 'ADC', 'Джин'), ('Никита Горилла', 'Support', 'БЦ')]
            }
        },
        {
            'date': '2026-11-06',
            'winner_team': 1,
            'teams': {
                1: [('Максончик', 'Top', 'Мундо'), ('Жираф', 'Jungle', 'Амбесса'), ('Никита Некрасов', 'Mid', 'Люкс'), ('Никита Горилла', 'ADC', 'Виктор'), ('Андудгеанге', 'Support', 'Карма')],
                2: [('Кирюха Борода', 'Top', 'Мундо'), ('Мемо', 'Jungle', 'Гекарим'), ('Андрей Деев', 'Mid', 'Вел\'Коз'), ('Артём Пипиев', 'ADC', 'ТФ'), ('Андрей Носков', 'Support', 'Сона')]
            }
        },
        {
            'date': '2026-11-07',
            'winner_team': 1,
            'teams': {
                1: [('Максончик', 'Jungle', 'Виего'), ('Артём Пипиев', 'Top', 'Гарен'), ('Андрей Носков', 'Mid', 'Виктор'), ('Никита Горилла', 'ADC', 'Синдра'), ('Жираф', 'Support', 'Милио')],
                2: [('Олег Крюков', 'Top', 'Камилла'), ('Андрей Деев', 'Jungle', 'Талон'), ('Мемо', 'Mid', 'Кассиопея'), ('Андудгеанге', 'ADC', 'Твич'), ('Андрей Усач', 'Support', 'Трэш')]
            }
        }
    ]

    for game in games:
        cursor.execute('INSERT INTO games (date, winner_team, max_score_threshold) VALUES (?, ?, ?)', (game['date'], game['winner_team'], 30))
        game_id = cursor.lastrowid

        for team_num, team_players in game['teams'].items():
            for player_name, role_name, champion in team_players:
                pid = players.get(player_name)
                rid = roles.get(role_name)
                if not pid or not rid:
                    print(f"ПРОПУСК: {player_name} / {role_name} — не найдено")
                    continue
                cursor.execute('''
                    INSERT INTO game_players (game_id, player_id, team, role_id, champion_name, is_random_sss)
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (game_id, pid, team_num, rid, champion))

                # Обновляем статистику игрока
                if team_num == game['winner_team']:
                    cursor.execute('UPDATE players SET total_games = total_games + 1, total_wins = total_wins + 1 WHERE id = ?', (pid,))
                else:
                    cursor.execute('UPDATE players SET total_games = total_games + 1 WHERE id = ?', (pid,))

    conn.commit()
    conn.close()
    print("8 игр добавлены, статистика обновлена.")

if __name__ == '__main__':
    add_games()