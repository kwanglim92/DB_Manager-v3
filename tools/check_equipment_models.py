import sqlite3
import os

# Get absolute path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
db_path = os.path.join(project_dir, 'data', 'local_db.sqlite')

if not os.path.exists(db_path):
    print(f"Database file not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if Equipment_Models table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Equipment_Models'")
result = cursor.fetchone()
print(f"Equipment_Models table exists: {result is not None}")

if result:
    # Count rows
    cursor.execute("SELECT COUNT(*) FROM Equipment_Models")
    count = cursor.fetchone()[0]
    print(f"Equipment_Models count: {count}")

    # Get all models
    cursor.execute("SELECT id, model_name, display_order FROM Equipment_Models ORDER BY display_order, model_name")
    models = cursor.fetchall()
    print(f"Models:")
    for model in models:
        print(f"  ID: {model[0]}, Name: {model[1]}, Display Order: {model[2]}")
else:
    print("Equipment_Models table does not exist!")
    print("\nAll tables in database:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")

conn.close()
