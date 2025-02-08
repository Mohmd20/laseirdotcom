import sqlite3
conn = sqlite3.connect("bot_database.db")
cur = conn.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        name TEXT
    )
''')
conn.commit()
conn.close()