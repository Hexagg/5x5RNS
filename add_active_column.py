import sqlite3

conn = sqlite3.connect('lol_teams.db')
cursor = conn.cursor()
try:
    cursor.execute('ALTER TABLE players ADD COLUMN is_active_session INTEGER DEFAULT 0')
    print("Колонка is_active_session добавлена.")
except sqlite3.OperationalError as e:
    print(f"Ошибка (возможно, колонка уже есть): {e}")
conn.commit()
conn.close()