import sqlite3

conn = sqlite3.connect('data/notes.db')
cursor = conn.cursor()

# 检查 ai_config 表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_config'")
print('ai_config table exists:', cursor.fetchone())

# 检查表结构
cursor.execute("PRAGMA table_info(ai_config)")
print('ai_config table structure:', cursor.fetchall())

# 检查表中的数据
try:
    cursor.execute('SELECT * FROM ai_config')
    print('ai_config data:', cursor.fetchall())
except Exception as e:
    print('Error querying ai_config:', e)

conn.close()