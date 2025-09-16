from app import app
from models.exts import db

app.app_context().push()

# Check current table structure
result = db.engine.execute('PRAGMA table_info(orders)')
print('Current orders table structure:')
for row in result:
    print(row)