import sqlite3

conn = sqlite3.connect('schedule.db')
print('Table structure:')
for row in conn.execute('PRAGMA table_info(schedules)'):
    print(f"Column {row[0]}: {row[1]} ({row[2]})")
conn.close()