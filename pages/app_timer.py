# pip install streamlit
# pip install pytube # 스트림릿에서 pytube 사용 시 필요
import streamlit as st
st.title("Timer Manager")
name = st.text_input("Enter Your Task Name")
        
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import streamlit as st
from streamlit_autorefresh import st_autorefresh

APP_TZ = ZoneInfo("Asia/Seoul")
DB_PATH = "task.db"

# -------------------------
# DB
# -------------------------
def db_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def db_init():
    with db_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS timer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at_iso TEXT NOT NULL,
                action TEXT,
                task_name TEXT NOT NULL,
                interval_type TEXT NOT NULL,
                memo TEXT NOT NULL,
                created_at_iso TEXT NOT NULL,
                timer_running BOOLEAN NOT NULL DEFAULT 0,
                timer_started_at_iso TEXT,
                run_type TEXT DEFAULT 'python'
            )
            """
        )
        
        # Check if columns exist, if not add them
        cursor = conn.execute("PRAGMA table_info(timer)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'action' not in columns:
            conn.execute("ALTER TABLE timer ADD COLUMN action TEXT")
        if 'run_type' not in columns:
            conn.execute("ALTER TABLE timer ADD COLUMN run_type TEXT DEFAULT 'python'")
        
        conn.commit()

def db_add(run_at: datetime, action: str, task_name: str, interval_type: str, memo: str, run_type: str = 'python'):
    with db_conn() as conn:
        conn.execute(
            """
            INSERT INTO timer (run_at_iso, action, task_name, interval_type, memo, created_at_iso, timer_running, run_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_at.astimezone(APP_TZ).isoformat(),
                action.strip(),
                task_name.strip(),
                interval_type,
                memo.strip(),
                datetime.now(APP_TZ).isoformat(),
                0,
                run_type,
            ),
        )
        conn.commit()

def db_list():
    with db_conn() as conn:
        cur = conn.execute(
            """
            SELECT id, run_at_iso, action, task_name, interval_type, memo, created_at_iso, timer_running, timer_started_at_iso, run_type
            FROM timer
            ORDER BY run_at_iso ASC
            """
        )
        rows = cur.fetchall()
    return rows

def db_delete(timer_id: int):
    with db_conn() as conn:
        conn.execute("DELETE FROM timer WHERE id = ?", (timer_id,))
        conn.commit()

def db_mark_timer_running(timer_id: int):
    with db_conn() as conn:
        conn.execute(
            """
            UPDATE timer
            SET timer_running = 1, timer_started_at_iso = ?
            WHERE id = ?
            """,
            (datetime.now(APP_TZ).isoformat(), timer_id),
        )
        conn.commit()

def db_reset_timer_running(timer_id: int):
    with db_conn() as conn:
        conn.execute(
            """
            UPDATE timer
            SET timer_running = 0
            WHERE id = ?
            """,
            (timer_id,),
        )
        conn.commit()

# -------------------------
# Logic
# -------------------------
@dataclass
class Timer:
    id: int
    run_at: datetime
    action: str
    task_name: str
    interval_type: str
    memo: str
    created_at: datetime
    timer_running: bool
    timer_started_at: datetime | None
    run_type: str = 'python'

def to_timer(row) -> Timer:
    # Handle both old format (9 fields) and new format (10 fields) for backward compatibility
    if len(row) == 10:
        (sid, run_at_iso, action, task_name, interval_type, memo, created_iso, timer_running, timer_started_at_iso, run_type) = row
    else:
        (sid, run_at_iso, action, task_name, interval_type, memo, created_iso, timer_running, timer_started_at_iso) = row
        run_type = 'python'  # default for old records
    run_at = datetime.fromisoformat(run_at_iso).astimezone(APP_TZ)
    created_at = datetime.fromisoformat(created_iso).astimezone(APP_TZ)
    timer_started_at = datetime.fromisoformat(timer_started_at_iso).astimezone(APP_TZ) if timer_started_at_iso else None
    return Timer(
        id=int(sid),
        run_at=run_at,
        action=action,
        task_name=task_name,
        interval_type=interval_type,
        memo=memo or "",
        created_at=created_at,
        timer_running=bool(timer_running),
        timer_started_at=timer_started_at,
    )

def find_due_timers(timers: list[Timer], now: datetime, window_seconds: int = 60) -> list[Timer]:
    due = []
    for t in timers:
        if t.timer_running:
            continue
        diff = abs((t.run_at - now).total_seconds())
        if diff <= window_seconds:
            due.append(t)
    # 여러 개가 동시에 걸리면 가장 이른 시간부터
    due.sort(key=lambda x: x.run_at)
    return due

# -------------------------
# UI
# -------------------------
st.set_page_config(page_title="예약 Task 자동 재생", layout="wide")
db_init()
st.title("⏰ 예약 시간에 Task 자동 재생 (Streamlit)")
now = datetime.now(APP_TZ)
with st.sidebar:
    st.subheader("⚙️ 옵션")
    auto_refresh = st.toggle("5초마다 자동 새로고침", value=True)
    autoplay = st.toggle("자동재생 시도(autoplay=1)", value=True)
    window = st.slider("재생 허용 범위(±초)", min_value=10, max_value=120, value=60, step=5)
    st.caption(f"현재 시간: **{now.strftime('%Y-%m-%d %H:%M:%S')} (KST)**")
if auto_refresh:
    st_autorefresh(interval=5000, key="autorefresh_5s")
# Load timers
rows = db_list()
timers = [to_timer(r) for r in rows]
# Auto play section
due = find_due_timers(timers, now, window_seconds=window)
st.markdown("---")
st.subheader("▶️ 자동 재생 영역")
if due:
    # 첫 번째 스케줄을 재생 대상으로 선택
    target = due[0]
    print(target)
    action = target.action
    vid = action
    if vid.startswith("https://") or vid.startswith("http://"):
        url = vid
        if autoplay:
            if "?" in url:
                url += "&autoplay=1"
            else:
                url += "?autoplay=1"
        cols = st.columns([2, 1])
        with cols[0]:
            st.success(
                f"예정 시간 도달!  "
                f"**{target.run_at.strftime('%Y-%m-%d %H:%M:%S')}**  |  "
                f"제목: **{target.task_name or '(제목 없음)'}**"
            )
            if target.memo:
                st.info(target.memo)
            if vid:
                st.video(url)
            else:
                st.error(
                    "url error"                
                )
                st.write("입력 URL:", target.url)
        with cols[1]:
            st.write("### 제어")
            st.write(f"- 일정 ID: `{target.id}`")
            st.write(f"- URL: {target.url}")
            if st.button("✅ 이 일정 재생 완료 처리", width='stretch'):
                db_mark_timer_running(target.id)
                st.rerun()
            if st.button("↩️ 재생 완료 해제(다시 재생)", width='stretch'):
                db_reset_timer_running(target.id)
                st.rerun()
            st.caption("※ 여러 일정이 동시에 걸리면 가장 이른 시간 1개를 우선 재생합니다.")
    else:
        st.info(f"running action app {target.action} as {target.run_type}")
        # Run external Python script
        import subprocess
        import os
        import threading
        import importlib.util
        import sys
        
        # Check if the action is a Python file
        if target.action.endswith('.py') and os.path.exists(target.action):
            try:
                if target.run_type == 'streamlit':
                    # Run Streamlit app inline within current window
                    st.markdown("---")
                    st.subheader(f"🚀 Running: {target.action}")
                    
                    # Create a container for the sub-app
                    with st.container(border=True):
                        try:
                            # Read and execute the Streamlit app code inline
                            with open(target.action, 'r', encoding='utf-8') as f:
                                code = f.read()
                            
                            # Create a new module namespace to avoid conflicts
                            spec = importlib.util.spec_from_file_location("sub_app", target.action)
                            module = importlib.util.module_from_spec(spec)
                            
                            # Execute the code in the current Streamlit context
                            old_globals = globals().copy()
                            exec(code, globals())
                            
                        except Exception as e:
                            st.error(f"Error running {target.action}: {str(e)}")
                    
                    st.markdown("---")
                    
                    # Add control buttons to manage the sub-app
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🔄 Refresh Sub-App", key=f"refresh_{target.id}"):
                            st.rerun()
                    with col2:
                        if st.button("✅ Mark Complete", key=f"complete_{target.id}"):
                            db_mark_timer_running(target.id)
                            st.rerun()
                    with col3:
                        if st.button("❌ Close Sub-App", key=f"close_{target.id}"):
                            db_mark_timer_running(target.id)
                            st.rerun()
                    
                    st.info("💡 Sub-app is running above. Use the buttons to control it.")
                    # Don't auto-rerun to keep the sub-app visible
                    
                else:  # target.run_type == 'python'
                    # Run as regular Python script
                    result = subprocess.run(['python', target.action], 
                                          capture_output=True, text=True, 
                                          cwd=os.getcwd())
                    if result.returncode == 0:
                        st.success(f"Successfully executed {target.action}")
                        if result.stdout:
                            st.text("Output:")
                            st.code(result.stdout)
                    else:
                        st.error(f"Error executing {target.action}")
                        if result.stderr:
                            st.error(result.stderr)
                    
                    # Mark timer as running and rerun for regular Python scripts
                    db_mark_timer_running(target.id)
                    st.rerun()
                            
            except Exception as e:
                st.error(f"Failed to run {target.action}: {str(e)}")
                db_mark_timer_running(target.id)
                st.rerun()
        else:
            st.warning(f"Action '{target.action}' is not a valid Python file or doesn't exist")
            db_mark_timer_running(target.id)
            st.rerun()
        
else:
    st.info("지금은 예정 시간(±범위) 안에 들어온 일정이 없어요.")
st.markdown("---")
st.subheader("🗓️ 타이머 등록")
with st.form("add_timer", clear_on_submit=True):
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        d = st.date_input("날짜", value=now.date())
    with c2:
        t = st.time_input("시간", value=now.time().replace(second=0, microsecond=0))
    with c3:
        action = st.text_input("Action ", placeholder="action task or App")
    task_name = st.text_input("제목", placeholder="예: 영어 대사 반 학습")
    memo = st.text_area("메모", placeholder="예: 1시간 단위로 반복 체크", height=80)
    col1, col2 = st.columns(2)
    with col1:
        interval_type = st.radio("반복 주기", options= ["한번", "매시간","매일"], horizontal=True)
    with col2:
        run_type = st.radio("실행 방식", options=["python", "streamlit"], horizontal=True, help="Python: 일반 스크립트로 실행\nStreamlit: 웹앱으로 실행")
    submitted = st.form_submit_button("➕ 등록")
    if submitted:
        run_at = datetime.combine(d, t, tzinfo=APP_TZ)
        if not action.strip():
            st.error("Action을 입력해 주세요.")
        else:
            # Media URL 검증(느슨하게): 추후 재생 실패 가능성 있음
            vid = action
            if vid is None:
                st.warning("Media URL 재이 안 됐어요. 그래도 저장은 합니다(추후 재생 실패 가능).")
            db_add(run_at, action, task_name, interval_type, memo, run_type)
            st.success("일정을 등록했어요!")
            st.rerun()
st.markdown("---")
st.subheader("📋 등록된 일정 테이블")

# Table header
header_cols = st.columns([0.5, 1.5, 1, 1.5, 0.8, 1, 0.75, 1.5, 0.4])
headers = ["ID", "예정시간(KST)", "제목", "Action", "실행방식", "메모", "재생여부", "재생시각", "삭제"]
for col, header in zip(header_cols, headers):
    with col:
        st.write(f"**{header}**")

st.markdown("---")

# Table rows with buttons
for i, t in enumerate(timers):
    cols = st.columns([0.5, 1.5, 1, 1.5, 0.8, 1, 0.75, 1.5, 0.4])
    
    with cols[0]:  # ID
        st.write(t.id)
    with cols[1]:  # 예정시간(KST)
        st.write(t.run_at.strftime("%Y-%m-%d %H:%M:%S"))
    with cols[2]:  # 제목
        st.write(t.task_name)
    with cols[3]:  # Action
        action_text = t.action or ""
        st.write(action_text[:20] + "..." if len(action_text) > 20 else action_text)
    with cols[4]:  # 실행방식
        st.write(t.run_type or "")
    with cols[5]:  # 메모
        memo_text = t.memo or ""
        st.write(memo_text[:15] + "..." if len(memo_text) > 15 else memo_text)
    with cols[6]:  # 재생여부 + Reset button
        status_cols = st.columns([1, 1])
        with status_cols[0]:
            st.write("✅" if t.timer_running else "⏳")
        with status_cols[1]:
            if t.timer_running:  # Only show reset button when timer is running
                if st.button("↩️", key=f"reset_{t.id}_{i}", help="재생 완료 해제", use_container_width=True):
                    db_reset_timer_running(t.id)
                    st.success(f"ID {t.id} 재생 상태를 리셋했어요.")
                    st.rerun()
    with cols[7]:  # 재생시각
        st.write(t.timer_started_at.strftime("%Y-%m-%d %H:%M:%S") if t.timer_started_at else "")
    with cols[8]:  # 삭제 버튼
        if st.button("🗑️", key=f"del_{t.id}_{i}", help="삭제", use_container_width=True):
            db_delete(t.id)
            st.success(f"ID {t.id} 삭제했어요.")
            st.rerun()
    
    # Add separator between rows
    st.markdown("---")
st.caption(
    "참고: 자동재생은 브라우저 정책(특히 소리 포함)에 따라 차단될 수 있어요. "
    "이 앱은 기본적으로 mute=1 옵션을 제공해 자동재생 성공률을 높입니다."
)
