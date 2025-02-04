import sqlite3

connection = sqlite3.connect("bot_database.db")
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS gold  (
    mopa BLOB,
    id INTEGER PRIMARY KEY AUTOINCREMENT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS gold  (
    mopa BLOB,
    id INTEGER PRIMARY KEY AUTOINCREMENT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS industrial  (
    fiber BLOB,
    id INTEGER PRIMARY KEY AUTOINCREMENT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS ads  (
    fiber BLOB,
    diod BLOB,
    id INTEGER PRIMARY KEY AUTOINCREMENT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS wood  (
    fiber BLOB,
    diod BLOB,
    id INTEGER PRIMARY KEY AUTOINCREMENT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS mirror  (
    fiber BLOB,
    diod BLOB,
    uv BLOB,
    id INTEGER PRIMARY KEY AUTOINCREMENT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS stone  (
    fiber BLOB,
    diod BLOB,
    id INTEGER PRIMARY KEY AUTOINCREMENT
)
''')
connection.commit()

connection.close()

print("Tables created successfully!")
