import sqlite3

conn = sqlite3.connect('data/notes.db')
cursor = conn.cursor()

# 检查 ai_config 表的索引
cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='ai_config'")
print('ai_config table indexes:', cursor.fetchall())

# 检查 ai_config 表的约束
cursor.execute("PRAGMA index_list(ai_config)")
print('ai_config table index list:', cursor.fetchall())

# 尝试手动插入一条数据测试
try:
    cursor.execute("""
        INSERT INTO ai_config (api_key, api_base, model, is_enabled, created_at, updated_at)
        VALUES ('test-key', 'https://test.com/v1', 'test-model', 0, datetime('now'), datetime('now'))
    """)
    conn.commit()
    print('Test insert successful')
    cursor.execute('SELECT * FROM ai_config WHERE api_key = "test-key"')
    print('Inserted row:', cursor.fetchone())
    # 删除测试数据
    cursor.execute('DELETE FROM ai_config WHERE api_key = "test-key"')
    conn.commit()
except Exception as e:
    print('Test insert failed:', e)
    conn.rollback()

conn.close()