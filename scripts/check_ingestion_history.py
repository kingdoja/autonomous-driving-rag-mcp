#!/usr/bin/env python
"""Check ingestion history for a collection."""

import sqlite3
import sys

collection = sys.argv[1] if len(sys.argv) > 1 else "ad_knowledge_v01"

conn = sqlite3.connect('data/db/ingestion_history.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT file_path, collection, status, timestamp 
    FROM ingestion_history 
    WHERE collection = ? 
    ORDER BY timestamp DESC
''', (collection,))

rows = cursor.fetchall()

print(f"\n=== Ingestion History for Collection: {collection} ===\n")
print(f"Total records: {len(rows)}\n")

success_count = 0
failed_count = 0

for row in rows:
    file_path, coll, status, timestamp = row
    status_symbol = "✅" if status == "success" else "❌"
    print(f"{status_symbol} {file_path}")
    if status == "success":
        success_count += 1
    else:
        failed_count += 1

print(f"\n=== Summary ===")
print(f"Success: {success_count}")
print(f"Failed: {failed_count}")

conn.close()
