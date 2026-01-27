import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import re

# 페이지 설정
st.set_page_config(
    page_title="동영상 스케줄러",
    page_icon="🎥",
    layout="wide"
)

# 세션 상태 초기화
if 'schedules' not in st.session_state:
    st.session_state.schedules = []

def extract_video_id(url):
    """YouTube URL에서 비디오 ID 추출"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_embed_url(url):
    """동영상 URL을 임베드 가능한 형태로 변환"""
    if 'youtube.com' in url or 'youtu.be' in url:
        video_id = extract_video_id(url)
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1"
    return url

def check_schedule():
    """현재 시간에 재생할 동영상 확인"""
    now = datetime.now()
    for schedule in st.session_state.schedules:
        scheduled_time = datetime.strptime(schedule['datetime'], '%Y-%m-%d %H:%M')
        # 예정 시간으로부터 1분 이내면 재생
        if abs((now - scheduled_time).total_seconds()) < 60:
            return schedule
    return None

# 타이틀
st.title("🎥 동영상 일정 스케줄러")
st.markdown("---")

# 2단 레이아웃
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 일정 등록")
    
    with st.form("schedule_form", clear_on_submit=True):
        # 날짜 선택
        schedule_date = st.date_input(
            "날짜",
            min_value=datetime.now().date()
        )
        
        # 시간 선택
        schedule_time = st.time_input(
            "시간",
            value=datetime.now().time()
        )
        
        # 동영상 URL
        video_url = st.text_input(
            "동영상 URL",
            placeholder="https://www.youtube.com/watch?v=..."
        )
        
        # 제목/메모
        title = st.text_input(
            "제목 (선택)",
            placeholder="예: 영어 강의 1강"
        )
        
        # 등록 버튼
        submitted = st.form_submit_button("일정 등록", width='stretch')
        
        if submitted:
            if video_url:
                datetime_str = f"{schedule_date} {schedule_time.strftime('%H:%M')}"
                new_schedule = {
                    'datetime': datetime_str,
                    'url': video_url,
                    'title': title if title else "제목 없음",
                    'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                st.session_state.schedules.append(new_schedule)
                st.success("✅ 일정이 등록되었습니다!")
            else:
                st.error("❌ 동영상 URL을 입력해주세요.")

with col2:
    st.header("📅 등록된 일정")
    
    if st.session_state.schedules:
        # 일정을 시간순으로 정렬
        sorted_schedules = sorted(
            st.session_state.schedules,
            key=lambda x: x['datetime']
        )
        
        # 데이터프레임 생성
        df = pd.DataFrame(sorted_schedules)
        df = df[['datetime', 'title', 'url']]
        df.columns = ['예정 시간', '제목', 'URL']
        
        # 테이블 표시
        st.dataframe(
            df,
            width='stretch',
            hide_index=True
        )
        
        # 전체 삭제 버튼
        if st.button("🗑️ 전체 일정 삭제", type="secondary"):
            st.session_state.schedules = []
            st.rerun()
    else:
        st.info("등록된 일정이 없습니다.")

st.markdown("---")

# 현재 재생 섹션
st.header("▶️ 재생 상태")

# 자동 새로고침 설정
auto_refresh = st.checkbox("자동 새로고침 (5초마다)", value=False)

if auto_refresh:
    time.sleep(5)
    st.rerun()

# 현재 시간 표시
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
st.info(f"현재 시간: **{current_time}**")

# 예정된 동영상 확인
scheduled_video = check_schedule()

if scheduled_video:
    st.success(f"🎬 지금 재생: **{scheduled_video['title']}**")
    
    # 동영상 임베드
    embed_url = get_embed_url(scheduled_video['url'])
    
    if 'youtube.com' in scheduled_video['url'] or 'youtu.be' in scheduled_video['url']:
        # YouTube 동영상 임베드
        st.markdown(
            f'<iframe width="100%" height="500" src="{embed_url}" '
            f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; '
            f'encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
            unsafe_allow_html=True
        )
    else:
        # 일반 URL은 링크로 표시
        st.markdown(f"[🔗 동영상 보기]({scheduled_video['url']})")
        st.warning("YouTube 외의 동영상은 링크를 클릭해서 시청하세요.")
else:
    # 다음 예정 동영상 표시
    if st.session_state.schedules:
        upcoming = None
        now = datetime.now()
        
        for schedule in sorted(st.session_state.schedules, key=lambda x: x['datetime']):
            scheduled_time = datetime.strptime(schedule['datetime'], '%Y-%m-%d %H:%M')
            if scheduled_time > now:
                upcoming = schedule
                time_diff = scheduled_time - now
                break
        
        if upcoming:
            st.warning(f"⏰ 다음 예정: **{upcoming['title']}** - {upcoming['datetime']}")
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            st.write(f"남은 시간: {time_diff.days}일 {hours}시간 {minutes}분")
        else:
            st.info("예정된 동영상이 없습니다.")
    else:
        st.info("등록된 일정이 없습니다.")

# 수동 재생 섹션
st.markdown("---")
st.header("🎮 수동 재생")

if st.session_state.schedules:
    selected_schedule = st.selectbox(
        "재생할 동영상 선택",
        options=range(len(st.session_state.schedules)),
        format_func=lambda x: f"{st.session_state.schedules[x]['datetime']} - {st.session_state.schedules[x]['title']}"
    )
    
    if st.button("▶️ 지금 재생", type="primary"):
        selected = st.session_state.schedules[selected_schedule]
        embed_url = get_embed_url(selected['url'])
        
        st.markdown(
            f'<iframe width="100%" height="500" src="{embed_url}" '
            f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; '
            f'encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
            unsafe_allow_html=True
        )

# 사용 안내
with st.expander("ℹ️ 사용 방법"):
    st.markdown("""
    ### 📖 사용 가이드
    
    1. **일정 등록**
       - 날짜와 시간을 선택하세요
       - YouTube 동영상 URL을 입력하세요
       - 제목을 입력하고 '일정 등록' 버튼을 클릭하세요
    
    2. **자동 재생**
       - '자동 새로고침' 체크박스를 활성화하세요
       - 예정된 시간(±1분 이내)이 되면 자동으로 동영상이 재생됩니다
    
    3. **수동 재생**
       - 하단의 '수동 재생' 섹션에서 원하는 동영상을 선택하세요
       - '지금 재생' 버튼을 클릭하세요
    
    4. **지원 사이트**
       - YouTube (자동 재생 지원)
       - 기타 사이트는 링크 형태로 제공됩니다
    """)