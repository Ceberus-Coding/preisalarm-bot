import sqlite3

conn = sqlite3.connect("alerts.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    symbol TEXT,
    target REAL,
    direction TEXT,
    note TEXT,
    triggered INTEGER DEFAULT 0
)
""")
conn.commit()

def add_alert(chat_id, symbol, target, direction, note):
    cursor.execute("INSERT INTO alerts (chat_id, symbol, target, direction, note) VALUES (?, ?, ?, ?, ?)",
                   (chat_id, symbol, target, direction, note))
    conn.commit()

def get_active_alerts():
    cursor.execute("SELECT id, chat_id, symbol, target, direction, note FROM alerts WHERE triggered = 0")
    return cursor.fetchall()

def mark_as_triggered(alert_id):
    cursor.execute("UPDATE alerts SET triggered = 1 WHERE id = ?", (alert_id,))
    conn.commit()

def get_all_alarms(chat_id):
    conn = sqlite3.connect("alerts.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, symbol, target, note FROM alerts WHERE chat_id = ?", (chat_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_alert(alert_id):
    conn = sqlite3.connect("alerts.db")
    c = conn.cursor()
    c.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()

def clear_user_alarms(chat_id):
    conn = sqlite3.connect("alerts.db")
    c = conn.cursor()
    c.execute("DELETE FROM alerts WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

