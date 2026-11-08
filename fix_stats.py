import sqlite3

def fix_stats():
    conn = sqlite3.connect('lol_teams.db')
    cursor = conn.cursor()

    # Исходные данные: (имя, победы, поражения)
    stats = [
        ('Андудгеанге', 4, 2),
        ('Андрей Носков', 2, 5),
        ('Максончик', 6, 2),
        ('Мемо', 3, 3),
        ('Жираф', 3, 1),
        ('Мопс', 0, 0),
        ('Гошанчик', 2, 0),
        ('Никита Горилла', 4, 4),
        ('Артём Пипиев', 2, 4),
        ('Андрей Деев', 1, 7),
        ('Никита Некрасов', 1, 0),
        ('Олег Крюков', 0, 1),
        ('Кирюха Борода', 2, 4),
        ('Хозяйка Клоуна', 2, 0),
        ('Славянка', 4, 2),
        ('Андрей Усач', 2, 5),
        ('Валерыч', 1, 1),
        ('Ксюха', 0, 0),
    ]

    for name, wins, losses in stats:
        total_games = wins + losses
        cursor.execute('''
            UPDATE players SET total_games = ?, total_wins = ? WHERE name = ?
        ''', (total_games, wins, name))

    conn.commit()
    conn.close()
    print("Статистика игроков восстановлена к исходным значениям.")

if __name__ == '__main__':
    fix_stats()