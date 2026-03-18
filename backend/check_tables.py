from app.core.db.database import engine
from sqlalchemy import text

result = engine.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
tables = [row[0] for row in result]
print("数据库表列表:")
for table in tables:
    print(f"  - {table}")

if "asset" in tables:
    print("\n✅ asset 表已创建")
else:
    print("\n❌ asset 表未创建")