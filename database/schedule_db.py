# Database handler for schedule_db 
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("Asia/Seoul")
DB_PATH = "schedule.db"

# -------------------------
# DB
# -------------------------
def db_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def db_init():
    with db_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at_iso TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                memo TEXT,
                created_at_iso TEXT NOT NULL,
                played INTEGER NOT NULL DEFAULT 0,
                played_at_iso TEXT,
                announcement TEXT
            )
            """
        )
        
        # Add the announcement column if it doesn't exist (for existing databases)
        try:
            conn.execute("ALTER TABLE schedules ADD COLUMN announcement TEXT DEFAULT ''")
            print("Added 'announcement' column to existing database")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                # Column already exists, that's fine
                pass
            else:
                # Some other error, re-raise it
                raise
        
        conn.commit()

def db_add(run_at: datetime, url: str, title: str, memo: str):
    with db_conn() as conn:
        conn.execute(
            """
            INSERT INTO schedules (run_at_iso, url, title, memo, created_at_iso, played, announcement)
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (
                run_at.astimezone(APP_TZ).isoformat(),
                url,
                title.strip(),
                memo.strip(),
                datetime.now(APP_TZ).isoformat(),
                "",
            ),
        )
        conn.commit()

def db_list():
    with db_conn() as conn:
        cur = conn.execute(
            """
            SELECT id, run_at_iso, url, title, memo, created_at_iso, played, played_at_iso, announcement
            FROM schedules
            ORDER BY run_at_iso ASC
            """
        )
        rows = cur.fetchall()
    return rows

def db_delete(schedule_id: int):
    with db_conn() as conn:
        conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
        conn.commit()

def db_mark_played(schedule_id: int):
    with db_conn() as conn:
        conn.execute(
            """
            UPDATE schedules
            SET played = 1, played_at_iso = ?
            WHERE id = ?
            """,
            (datetime.now(APP_TZ).isoformat(), schedule_id),
        )
        conn.commit()

def db_reset_played(schedule_id: int):
    with db_conn() as conn:
        conn.execute(
            """
            UPDATE schedules
            SET played = 0, played_at_iso = NULL
            WHERE id = ?
            """,
            (schedule_id,),
        )
        conn.commit()

# -------------------------
# Logic
# -------------------------           
@dataclass
class Schedule:
    id: int
    run_at: datetime
    url: str
    title: str
    memo: str
    created_at: datetime
    played: bool
    played_at: datetime | None
    announcement: str
    
def to_schedule(row) -> Schedule:
    (sid, run_at_iso, url, title, memo, created_iso, played, played_at_iso, announcement) = row
    run_at = datetime.fromisoformat(run_at_iso).astimezone(APP_TZ)
    created_at = datetime.fromisoformat(created_iso).astimezone(APP_TZ)
    played_at = datetime.fromisoformat(played_at_iso).astimezone(APP_TZ) if played_at_iso else None
    return Schedule(
        id=int(sid),
        run_at=run_at,
        url=url,
        title=title or "",
        memo=memo or "",
        created_at=created_at,
        played=bool(played),
        played_at=played_at,
        announcement =  announcement or "",
    )

def find_due_schedules(schedules: list[Schedule], now: datetime, window_seconds: int = 60) -> list[Schedule]:
    due = []
    for s in schedules:
        if s.played:
            continue
        diff = abs((s.run_at - now).total_seconds())
        if diff <= window_seconds:
            due.append(s)
    # 여러 개가 동시에 걸리면 가장 이른 시간부터
    due.sort(key=lambda x: x.run_at)
    return due