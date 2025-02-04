import sqlite3

# اتصال به پایگاه داده
conn = sqlite3.connect("bot_database.db")
cursor = conn.cursor()

# خواندن فایل باینری (مثلاً یک تصویر یا PDF)
with open("mopa.pdf", "rb") as file:
    mopa = file.read()
with open("FIBER.pdf", "rb") as file:
    fiber = file.read()
with open("DIODE.pdf", "rb") as file:
    diod = file.read()
with open("UV.pdf", "rb") as file:
    uv = file.read()

# درج مقدار در جدول
cursor.execute('''
INSERT INTO gold (mopa) VALUES (?)
''', (mopa,))
cursor.execute('''
INSERT INTO industrial (fiber) VALUES (?)
''', (fiber,))
cursor.execute('''
INSERT INTO ads (fiber,diod) VALUES (?,?)
''', (fiber, diod,))
cursor.execute('''
INSERT INTO wood (fiber,diod) VALUES (?,?)
''', (fiber,diod))
cursor.execute('''
INSERT INTO mirror (fiber,diod,uv) VALUES (?,?,?)
''', (fiber,diod,uv))
cursor.execute('''
INSERT INTO stone (fiber,diod) VALUES (?,?)
''', (fiber,diod))

conn.commit()
conn.close()
