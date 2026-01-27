# pip install streamlit
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import webbrowser

APP_TZ = ZoneInfo("Asia/Seoul")
# DB_PATH = "schedule.db"
from database.schedule_db import (
    db_conn,
    db_init,
    db_add,
    db_list,
    db_mark_played,
    db_reset_played,
    db_delete,
    Schedule,
    to_schedule,
    find_due_schedules,
)
from functions.youtube_function import (
    extract_youtube_video_id,
    build_youtube_embed_html,
    extract_google_drive_file_id,
    build_google_drive_embed_html,
    build_youtube_embed_with_completion_html,
)
from functions.audio_function import (
    generate_announcement_html,
)

# Initialize TTS variables with default values
tts_rate = 0.9
tts_volume = 0.8
tts_pitch = 1.0
custom_announcement = "Your scheduled media {title} starts playing at {date_time}"
uploaded_audio = None

def create_repeat_schedules(initial_run_at: datetime, url: str, title: str, memo: str, repeat_option: str) -> int:
    """
    Store repeat information with the schedule (no longer creates multiple entries)
    
    Args:
        initial_run_at: The first scheduled time
        url: Video URL
        title: Schedule title
        memo: Schedule memo
        repeat_option: "hourly", "daily", or "weekly"
    
    Returns:
        Always returns 0 (no additional schedules created)
    """
    # Store repeat option in memo field
    enhanced_memo = f"{memo} [REPEAT:{repeat_option}]"
    
    # Update the original schedule with repeat information
    with db_conn() as conn:
        conn.execute(
            """
            UPDATE schedules 
            SET memo = ?
            WHERE run_at_iso = ? AND url = ? AND title = ?
            ORDER BY id DESC LIMIT 1
            """,
            (enhanced_memo, initial_run_at.isoformat(), url, title)
        )
        conn.commit()
    
    return 0  # No additional schedules created

def auto_complete_repeat_schedule(schedule_id: int):
    """
    Automatically handle repeat schedule completion
    """
    with db_conn() as conn:
        # Get schedule info
        cur = conn.execute(
            "SELECT memo FROM schedules WHERE id = ?",
            (schedule_id,)
        )
        result = cur.fetchone()
        if result and result[0]:
            memo = result[0]
            # Check if this is a repeat schedule
            if "[REPEAT:" in memo:
                import re
                match = re.search(r'\[REPEAT:(\w+)\]', memo)
                if match:
                    repeat_opt = match.group(1)
                    update_repeat_schedule(schedule_id, repeat_opt)
                    print(f"Auto-completed repeat schedule {schedule_id} with option {repeat_opt}")
                    return True
    return False

def update_repeat_schedule(schedule_id: int, repeat_option: str):
    """
    Update the schedule's run_at time based on repeat option
    
    Args:
        schedule_id: ID of the schedule to update
        repeat_option: "hourly", "daily", or "weekly"
    """
    with db_conn() as conn:
        # Get current schedule
        cur = conn.execute(
            "SELECT run_at_iso FROM schedules WHERE id = ?",
            (schedule_id,)
        )
        result = cur.fetchone()
        if result:
            current_run_at = datetime.fromisoformat(result[0]).astimezone(APP_TZ)
            
            # Calculate next run time
            if repeat_option == "hourly":
                next_run_at = current_run_at + timedelta(hours=1)
            elif repeat_option == "daily":
                next_run_at = current_run_at + timedelta(days=1)
            elif repeat_option == "weekly":
                next_run_at = current_run_at + timedelta(weeks=1)
            else:
                return  # No repeat
            
            # Update the schedule with new time and reset played status
            conn.execute(
                """
                UPDATE schedules 
                SET run_at_iso = ?, played = 0, played_at_iso = NULL
                WHERE id = ?
                """,
                (next_run_at.isoformat(), schedule_id)
            )
            conn.commit()
            
            # Debug: Print the update
            print(f"Updated schedule {schedule_id}: {current_run_at} -> {next_run_at} (repeat: {repeat_option})")

st.set_page_config(page_title="예약 YouTube 자동 재생", layout="wide")
db_init()
st.title("⏰ 예약 시간에 YouTube 자동 재생 (Streamlit)")
now = datetime.now(APP_TZ)
with st.sidebar:
    st.subheader("⚙️ 옵션")
    auto_refresh = st.toggle("5초마다 자동 새로고침", value=True)
    autoplay = st.toggle("자동재생 시도(autoplay=1)", value=True)
    mute = st.toggle("음소거(mute=1)로 재생", value=False, help="브라우저 자동재생 제한 때문에 권장")
    
    
    
    window = st.slider("재생 허용 범위(±초)", min_value=10, max_value=120, value=60, step=5)
    st.caption(f"현재 시간: **{now.strftime('%Y-%m-%d %H:%M:%S')} (KST)**")
    
    st.markdown("---")
    st.subheader("📁 파일 업로드")
    uploaded_file = st.file_uploader(
        "미디어 파일 업로드 (선택사항)",
        type=['mp4', 'avi', 'mov', 'mkv', 'webm', "jpg"],
        help="업로드된 파일은 일정 등록 시 URL 대신 사용됩니다"
    )
   
if auto_refresh:
    st_autorefresh(interval=5000, key="autorefresh_5s")
# Load schedules
rows = db_list()
schedules = [to_schedule(r) for r in rows]
# Auto play section
due = find_due_schedules(schedules, now, window_seconds=window)
st.markdown("---")
st.subheader("▶️ 자동 재생 영역")
if due:
    # 첫 번째 스케줄을 재생 대상으로 선택
    target = due[0]
    print(target.url)
    
    # Determine content type based on URL
    if target.url.startswith("uploaded_file:"):
        content_type = "uploaded"
    elif "youtube.com" in target.url or "youtu.be" in target.url:
        content_type = "youtube"
    elif "drive.google.com" in target.url or "docs.google.com" in target.url:
        content_type = "google_drive"
    else:
        content_type = "other"
    
    # Process based on content type
    if content_type == "uploaded":
        # Handle uploaded files
        file_name = target.url.replace("uploaded_file:", "")
        st.success(
            f"예정 시간 도달!  "
            f"**{target.run_at.strftime('%Y-%m-%d %H:%M:%S')}**  |  "
            f"제목: **{target.title or '(제목 없음)'}** | 타입: 업로드된 파일"
        )
        if target.memo:
            st.info(target.memo)
        
        # Get audio settings from session state with defaults
        audio_announcement = st.session_state.get('audio_announcement', True)
        announcement_type = st.session_state.get('announcement_type', "텍스트 음성 변환")
        custom_announcement = st.session_state.get('custom_announcement', "Your scheduled media {title} starts playing at {date_time}")
        tts_rate = st.session_state.get('tts_rate', 0.9)
        tts_volume = st.session_state.get('tts_volume', 0.8)
        tts_pitch = st.session_state.get('tts_pitch', 1.0)
        
        # Handle uploaded audio from session state
        uploaded_audio = None
        if st.session_state.get('uploaded_audio_name') and st.session_state.get('uploaded_audio_path'):
            # Create a simple mock object with name attribute for audio_function compatibility
            class MockAudioFile:
                def __init__(self, name):
                    self.name = name
            uploaded_audio = MockAudioFile(st.session_state.uploaded_audio_name)
        
        # Add audio announcement
        announcement_html = generate_announcement_html(
            target, audio_announcement, 
            announcement_type=announcement_type if audio_announcement else None,
            custom_announcement=custom_announcement if audio_announcement and announcement_type == "텍스트 음성 변환" else None,
            tts_rate=tts_rate if audio_announcement and announcement_type == "텍스트 음성 변환" else 0.9,
            tts_volume=tts_volume if audio_announcement else 0.8,
            tts_pitch=tts_pitch if audio_announcement and announcement_type == "텍스트 음성 변환" else 1.0,
            uploaded_audio=uploaded_audio if audio_announcement and announcement_type == "미리 녹음된 오디오" else None
        )
        if announcement_html:
            st.components.v1.html(announcement_html, height=0)
        
        st.video(f"uploads/{file_name}", start_time=0)
        
        # Control buttons for uploaded content
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 이 일정 재생 완료 처리", width='stretch'):
                if "[REPEAT:" in (target.memo or ""):
                    import re
                    match = re.search(r'\[REPEAT:(\w+)\]', target.memo)
                    if match:
                        repeat_opt = match.group(1)
                        update_repeat_schedule(target.id, repeat_opt)
                        st.success(f"재생 완료! 다음 시간으로 업데이트되었습니다. (반복: {repeat_opt})")
                    else:
                        db_mark_played(target.id)
                        st.success("재생 완료!")
                else:
                    db_mark_played(target.id)
                    st.success("재생 완료!")
                st.rerun()
        with col2:
            if st.button("↩️ 재생 완료 해제(다시 재생)", width='stretch'):
                db_reset_played(target.id)
                st.rerun()
    
    elif content_type == "youtube":
        # Handle YouTube content
        vid = extract_youtube_video_id(target.url)
        cols = st.columns([2, 1])
        with cols[0]:
            st.success(
                f"예정 시간 도달!  "
                f"**{target.run_at.strftime('%Y-%m-%d %H:%M:%S')}**  |  "
                f"제목: **{target.title or '(제목 없음)'}** | 타입: YouTube"
            )
            if target.memo:
                st.info(target.memo)
                    # Get audio settings from session state with defaults
        audio_announcement = st.session_state.get('audio_announcement', True)
        announcement_type = st.session_state.get('announcement_type', "텍스트 음성 변환")
        custom_announcement = st.session_state.get('custom_announcement', "Your scheduled media {title} starts playing at {date_time}")
        tts_rate = st.session_state.get('tts_rate', 0.9)
        tts_volume = st.session_state.get('tts_volume', 0.8)
        tts_pitch = st.session_state.get('tts_pitch', 1.0)
        
        # Handle uploaded audio from session state
        uploaded_audio = None
        if st.session_state.get('uploaded_audio_name') and st.session_state.get('uploaded_audio_path'):
            # Create a simple mock object with name attribute for audio_function compatibility
            class MockAudioFile:
                def __init__(self, name):
                    self.name = name
            uploaded_audio = MockAudioFile(st.session_state.uploaded_audio_name)
                    # Add audio announcement
        announcement_html = generate_announcement_html(
            target, audio_announcement,
            announcement_type=announcement_type if audio_announcement else None,
            custom_announcement=custom_announcement if audio_announcement and announcement_type == "텍스트 음성 변환" else None,
            tts_rate=tts_rate if audio_announcement and announcement_type == "텍스트 음성 변환" else 0.9,
            tts_volume=tts_volume if audio_announcement else 0.8,
            tts_pitch=tts_pitch if audio_announcement and announcement_type == "텍스트 음성 변환" else 1.0,
            uploaded_audio=uploaded_audio if audio_announcement and announcement_type == "미리 녹음된 오디오" else None
        )
        if announcement_html:
            st.components.v1.html(announcement_html, height=0)
        
        if vid:
            # Create YouTube embed with automatic completion detection
            embed_html = build_youtube_embed_with_completion_html(vid, target.id, autoplay, mute)
            st.components.v1.html(embed_html, height=420)
        else:
            st.error(
                "YouTube URL에서 video id를 추출하지 못했어요. "
                "지원 예: watch?v=, youtu.be/, shorts/ 형태"
            )
            st.write("입력 URL:", target.url)
        with cols[1]:
            st.write("### 제어")
            st.write(f"- 일정 ID: `{target.id}`")
            st.write(f"- URL: {target.url}")
            
            # Check for auto-completion trigger
            if f"auto_complete_{target.id}" in st.query_params:
                st.session_state[f"auto_completed_{target.id}"] = True
                st.rerun()
                    
            if st.button("✅ 이 일정 재생 완료 처리", width='stretch'):
                if "[REPEAT:" in (target.memo or ""):
                    import re
                    match = re.search(r'\[REPEAT:(\w+)\]', target.memo)
                    if match:
                        repeat_opt = match.group(1)
                        update_repeat_schedule(target.id, repeat_opt)
                        st.success(f"재생 완료! 다음 시간으로 업데이트되었습니다. (반복: {repeat_opt})")
                    else:
                        db_mark_played(target.id)
                        st.success("재생 완료!")
                else:
                    db_mark_played(target.id)
                    st.success("재생 완료!")
                st.rerun()
            if st.button("↩️ 재생 완료 해제(다시 재생)", width='stretch'):
                db_reset_played(target.id)
                st.rerun()
            st.caption("※ 여러 일정이 동시에 걸리면 가장 이른 시간 1개를 우선 재생합니다.")
    
    elif content_type == "google_drive":
        # Handle Google Drive content
        st.success(
            f"예정 시간 도달!  "
            f"**{target.run_at.strftime('%Y-%m-%d %H:%M:%S')}**  |  "
            f"제목: **{target.title or '(제목 없음)'}** | 타입: Google Drive"
        )
        if target.memo:
            st.info(target.memo)
        
        # Get audio settings from session state with defaults
        audio_announcement = st.session_state.get('audio_announcement', True)
        announcement_type = st.session_state.get('announcement_type', "텍스트 음성 변환")
        custom_announcement = st.session_state.get('custom_announcement', "Your scheduled media {title} starts playing at {date_time}")
        tts_rate = st.session_state.get('tts_rate', 0.9)
        tts_volume = st.session_state.get('tts_volume', 0.8)
        tts_pitch = st.session_state.get('tts_pitch', 1.0)
        
        # Handle uploaded audio from session state
        uploaded_audio = None
        if st.session_state.get('uploaded_audio_name') and st.session_state.get('uploaded_audio_path'):
            # Create a simple mock object with name attribute for audio_function compatibility
            class MockAudioFile:
                def __init__(self, name):
                    self.name = name
            uploaded_audio = MockAudioFile(st.session_state.uploaded_audio_name)
        
        # Add audio announcement
        announcement_html = generate_announcement_html(
            target, audio_announcement,
            announcement_type=announcement_type if audio_announcement else None,
            custom_announcement=custom_announcement if audio_announcement and announcement_type == "텍스트 음성 변환" else None,
            tts_rate=tts_rate if audio_announcement and announcement_type == "텍스트 음성 변환" else 0.9,
            tts_volume=tts_volume if audio_announcement else 0.8,
            tts_pitch=tts_pitch if audio_announcement and announcement_type == "텍스트 음성 변환" else 1.0,
            uploaded_audio=uploaded_audio if audio_announcement and announcement_type == "미리 녹음된 오디오" else None
        )
        if announcement_html:
            st.components.v1.html(announcement_html, height=0)
        
        # Extract file ID from Google Drive URL and create embed
        file_id = extract_google_drive_file_id(target.url)
        
        if file_id:
            # Create Google Drive embed
            embed_html = build_google_drive_embed_html(file_id)
            st.components.v1.html(embed_html, height=420)
        else:
            st.error("Google Drive URL에서 파일 ID를 추출하지 못했어요.")
            st.write("입력 URL:", target.url)
            if st.button("🌐 브라우저에서 열기", width='stretch'):
                webbrowser.open(target.url)
        
        # Control buttons for Google Drive content
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 이 일정 재생 완료 처리", width='stretch'):
                if "[REPEAT:" in (target.memo or ""):
                    import re
                    match = re.search(r'\[REPEAT:(\w+)\]', target.memo)
                    if match:
                        repeat_opt = match.group(1)
                        update_repeat_schedule(target.id, repeat_opt)
                        st.success(f"재생 완료! 다음 시간으로 업데이트되었습니다. (반복: {repeat_opt})")
                    else:
                        db_mark_played(target.id)
                        st.success("재생 완료!")
                else:
                    db_mark_played(target.id)
                    st.success("재생 완료!")
                st.rerun()
        with col2:
            if st.button("↩️ 재생 완료 해제(다시 재생)", width='stretch'):
                db_reset_played(target.id)
                st.rerun()
    
    else:
        # Handle other/unknown URL types
        st.success(
            f"예정 시간 도달!  "
            f"**{target.run_at.strftime('%Y-%m-%d %H:%M:%S')}**  |  "
            f"제목: **{target.title or '(제목 없음)'}** | 타입: 기타 링크"
        )
        if target.memo:
            st.info(target.memo)
        
        st.info("일반 웹 링크입니다. 브라우저에서 열어보세요.")
        st.write(f"URL: {target.url}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🌐 브라우저에서 열기", width='stretch'):
                webbrowser.open(target.url)
        with col2:
            if st.button("✅ 이 일정 재생 완료 처리", width='stretch'):
                if "[REPEAT:" in (target.memo or ""):
                    import re
                    match = re.search(r'\[REPEAT:(\w+)\]', target.memo)
                    if match:
                        repeat_opt = match.group(1)
                        update_repeat_schedule(target.id, repeat_opt)
                        st.success(f"재생 완료! 다음 시간으로 업데이트되었습니다. (반복: {repeat_opt})")
                    else:
                        db_mark_played(target.id)
                        st.success("재생 완료!")
                else:
                    db_mark_played(target.id)
                    st.success("재생 완료!")
                st.rerun()
        with col3:
            if st.button("↩️ 재생 완료 해제(다시 재생)", width='stretch'):
                db_reset_played(target.id)
                st.rerun()
else:
    st.info("지금은 예정 시간(±범위) 안에 들어온 일정이 없어요.")
st.markdown("---")
st.subheader("🗓️ 일정 등록")
with st.form("add_schedule", clear_on_submit=True):
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        d = st.date_input("날짜", value=now.date())
    with c2:
        time_str = st.text_input("시간 (HH:MM)", value=now.time().strftime("%H:%M"), placeholder="14:30")
    with c3:
        # Check if file was uploaded in sidebar
        if 'uploaded_file' in locals() and uploaded_file is not None:
            st.info(f"업로드된 파일: {uploaded_file.name}")
            url = f"uploaded_file:{uploaded_file.name}"
            st.text_input("동영상 URL (YouTube)", value=url, disabled=True, help="사이드바에서 업로드된 파일이 사용됩니다")
        else:
            url = st.text_input("동영상 URL (YouTube)", placeholder="https://www.youtube.com/watch?v=... (또는 사이드바에서 파일 업로드)")
    
    # Add repeat options field
    repeat_display = st.radio("반복 옵션", options=["반복 안함", "매시간", "매일", "매주"], horizontal=True)
    # Map display values back to internal values
    repeat_option = {"반복 안함": "none", "매시간": "hourly", "매일": "daily", "매주": "weekly"}[repeat_display]
    
    title = st.text_input("제목", placeholder="예: 영어 대사 반복 학습")
    memo = st.text_area("메모", placeholder="예: 1시간 단위로 반복 체크", height=80)
    submitted = st.form_submit_button("➕ 등록")
    if submitted:
        # Parse time string
        try:
            from datetime import time
            hour, minute = map(int, time_str.split(":"))
            t = time(hour, minute)
            run_at = datetime.combine(d, t, tzinfo=APP_TZ)
        except ValueError:
            st.error("시간 형식이 잘못되었습니다. HH:MM 형식으로 입력해주세요. (예: 14:30)")
            st.stop()
        
        # Handle uploaded file
        if 'uploaded_file' in locals() and uploaded_file is not None:
            # Save uploaded file
            import os
            os.makedirs("uploads", exist_ok=True)
            file_path = os.path.join("uploads", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            url = file_path
            st.success(f"파일이 업로드되었습니다: {uploaded_file.name}")
        
        if not url.strip():
            st.error("URL을 입력하거나 파일을 업로드해 주세요.")
        else:
            # YouTube 검증 (URL의 경우에만)
            if url.startswith("http"):
                vid = extract_youtube_video_id(url)
                if vid is None:
                    st.warning("YouTube ID 추출이 안 됐어요. 그래도 저장은 합니다(추후 재생 실패 가능).")
            
            # Add the initial schedule
            if repeat_option != "none":
                # Store repeat option in memo for single-schedule repeat functionality
                enhanced_memo = f"{memo} [REPEAT:{repeat_option}]"
                db_add(run_at, url, title, enhanced_memo)
                st.success(f"일정을 등록했어요! (반복 옵션: {repeat_display})")
            else:
                db_add(run_at, url, title, memo)
                st.success("일정을 등록했어요!")
            st.rerun()
st.markdown("---")
st.subheader("📋 등록된 일정 테이블")

# Table header
header_cols = st.columns([0.5, 1.5, 1, 1.5, 1, 0.75, 0.8, 0.4, 0.4, 0.4])
headers = ["ID", "예정시간(KST)", "제목", "URL", "메모", "재생여부", "반복옵션", "재생", "편집", "삭제"]
for col, header in zip(header_cols, headers):
    with col:
        st.write(f"**{header}**")

st.markdown("---")

# Table rows with buttons
for i, s in enumerate(schedules):
    cols = st.columns([0.5, 1.5, 1, 1.5, 1, 0.75, 0.8, 0.4, 0.4, 0.4])
    
    with cols[0]:  # ID
        st.write(s.id)
    with cols[1]:  # 예정시간(KST)
        st.write(s.run_at.strftime("%Y-%m-%d %H:%M:%S"))
    with cols[2]:  # 제목
        title_text = s.title or ""
        st.write(title_text[:15] + "..." if len(title_text) > 15 else title_text)
    with cols[3]:  # URL
        url_text = s.url or ""
        st.write(url_text[:20] + "..." if len(url_text) > 20 else url_text)
    with cols[4]:  # 메모
        memo_text = s.memo or ""
        st.write(memo_text[:15] + "..." if len(memo_text) > 15 else memo_text)
    with cols[5]:  # 재생여부 + Reset button
        status_cols = st.columns([1, 1])
        with status_cols[0]:
            st.write("✅" if s.played else "⏳")
        with status_cols[1]:
            if s.played:  # Only show reset button when played is True
                if st.button("↩️", key=f"reset_{s.id}_{i}", help="재생 완료 해제", use_container_width=True):
                    db_reset_played(s.id)
                    st.success(f"ID {s.id} 재생 상태를 리셋했어요.")
                    st.rerun()
   
    with cols[6]:  # 반복옵션
        # Extract repeat option from memo field
        if "[REPEAT:" in (s.memo or ""):
            import re
            match = re.search(r'\[REPEAT:(\w+)\]', s.memo)
            if match:
                repeat_opt = match.group(1)
                repeat_display = {"hourly": "매시간", "daily": "매일", "weekly": "매주"}.get(repeat_opt, "반복")
                repeat_text = repeat_display
            else:
                repeat_text = "반복"
        else:
            repeat_text = "반복 안함"
        st.write(repeat_text)
    with cols[7]:  # 재생 버튼
        if st.button("▶️", key=f"play_{s.id}_{i}", help="재생", use_container_width=True):
            # Play the video
            st.session_state[f"playing_{s.id}"] = True
            st.rerun()
    with cols[8]:  # 편집 버튼
        if st.button("✏️", key=f"edit_{s.id}_{i}", help="편집", use_container_width=True):
            # Set edit mode for this schedule
            st.session_state[f"editing_{s.id}"] = True
            st.rerun()
    with cols[9]:  # 삭제 버튼
        if st.button("🗑️", key=f"del_{s.id}_{i}", help="삭제", use_container_width=True):
            db_delete(s.id)
            st.success(f"ID {s.id} 삭제했어요.")
            st.rerun()
    
    # Show edit form if this item is being edited
    if st.session_state.get(f"editing_{s.id}", False):
        with st.expander(f"✏️ 편집 중: {s.title or '제목 없음'}", expanded=True):
            with st.form(f"edit_form_{s.id}"):
                col1, col2 = st.columns(2)
                with col1:
                    edit_date = st.date_input("날짜", value=s.run_at.date(), key=f"edit_date_{s.id}")
                with col2:
                    edit_time = st.text_input("시간 (HH:MM)", value=s.run_at.strftime("%H:%M"), key=f"edit_time_{s.id}")
                
                # Add repeat options field to edit form
                # Detect current repeat option from memo field
                current_repeat_option = "none"
                if "[REPEAT:" in (s.memo or ""):
                    import re
                    match = re.search(r'\[REPEAT:(\w+)\]', s.memo)
                    if match:
                        current_repeat_option = match.group(1)
                
                # Map internal option to display value and get index
                repeat_options = ["반복 안함", "매시간", "매일", "매주"]
                repeat_mapping = {"none": "반복 안함", "hourly": "매시간", "daily": "매일", "weekly": "매주"}
                current_repeat_display = repeat_mapping.get(current_repeat_option, "반복 안함")
                current_index = repeat_options.index(current_repeat_display)
                
                edit_repeat_display = st.radio("반복 옵션", options=repeat_options, 
                                             index=current_index, horizontal=True, 
                                             key=f"edit_repeat_{s.id}")
                
                edit_title = st.text_input("제목", value=s.title or "", key=f"edit_title_{s.id}")
                edit_url = st.text_input("URL", value=s.url or "", key=f"edit_url_{s.id}")
                edit_memo = st.text_area("메모", value=s.memo or "", key=f"edit_memo_{s.id}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("💾 저장"):
                        try:
                            from datetime import time
                            hour, minute = map(int, edit_time.split(":"))
                            t = time(hour, minute)
                            new_run_at = datetime.combine(edit_date, t, tzinfo=APP_TZ)
                            
                            # Map display values back to internal values
                            edit_repeat_option = {"반복 안함": "none", "매시간": "hourly", "매일": "daily", "매주": "weekly"}[edit_repeat_display]
                            
                            # Handle repeat option in memo field
                            # First, remove any existing repeat option from memo
                            import re
                            clean_memo = re.sub(r'\s*\[REPEAT:\w+\]', '', edit_memo).strip()
                            
                            # Add new repeat option if not "none"
                            if edit_repeat_option != "none":
                                final_memo = f"{clean_memo} [REPEAT:{edit_repeat_option}]" if clean_memo else f"[REPEAT:{edit_repeat_option}]"
                            else:
                                final_memo = clean_memo
                            
                            # Update the schedule in database
                            with db_conn() as conn:
                                conn.execute(
                                    """
                                    UPDATE schedules 
                                    SET run_at_iso = ?, title = ?, url = ?, memo = ?
                                    WHERE id = ?
                                    """,
                                    (new_run_at.isoformat(), edit_title, edit_url, final_memo, s.id)
                                )
                                conn.commit()
                            
                            st.session_state[f"editing_{s.id}"] = False
                            st.success(f"ID {s.id} 일정이 수정되었습니다.")
                            st.rerun()
                        except ValueError:
                            st.error("시간 형식이 잘못되었습니다. HH:MM 형식으로 입력해주세요.")
                        except Exception as e:
                            st.error(f"수정 중 오류가 발생했습니다: {str(e)}")
                with col2:
                    if st.form_submit_button("❌ 취소"):
                        st.session_state[f"editing_{s.id}"] = False
                        st.rerun()
    
    # Show video player if this item is being played
    if st.session_state.get(f"playing_{s.id}", False):
        with st.expander(f"🎵 재생 중: {s.title or '제목 없음'}", expanded=True):
            vid = extract_youtube_video_id(s.url)
            if vid:
                url = s.url
                if "?" in url:
                    url += "&autoplay=1"
                else:
                    url += "?autoplay=1"
                st.video(url)
            else:
                st.error("YouTube URL에서 video id를 추출하지 못했어요.")
                st.write("URL:", s.url)
            
            # Control buttons for the player
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("⏹️ 정지", key=f"stop_{s.id}_{i}"):
                    st.session_state[f"playing_{s.id}"] = False
                    st.rerun()
            with col2:
                if st.button("✅ 재생 완료", key=f"complete_{s.id}_{i}"):
                    # For manual playback, check if this is a repeat schedule and update immediately
                    if "[REPEAT:" in (s.memo or ""):
                        import re
                        match = re.search(r'\[REPEAT:(\w+)\]', s.memo)
                        if match:
                            repeat_opt = match.group(1)
                            update_repeat_schedule(s.id, repeat_opt)
                            st.session_state[f"playing_{s.id}"] = False
                            st.success(f"재생 완료! 다음 시간으로 업데이트되었습니다. (반복: {repeat_opt})")
                        else:
                            db_mark_played(s.id)
                            st.session_state[f"playing_{s.id}"] = False
                            st.success("재생 완료 처리했어요.")
                    else:
                        db_mark_played(s.id)
                        st.session_state[f"playing_{s.id}"] = False
                        st.success("재생 완료 처리했어요.")
                    st.rerun()
            with col3:
                if st.button("🔄 다시 재생", key=f"replay_{s.id}_{i}"):
                    st.rerun()
    
    # Add separator between rows
    st.markdown("---")
st.caption(
    "참고: 자동재생은 브라우저 정책(특히 소리 포함)에 따라 차단될 수 있어요. "
    "이 앱은 기본적으로 mute=1 옵션을 제공해 자동재생 성공률을 높입니다."
)
