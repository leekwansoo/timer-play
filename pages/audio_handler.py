import streamlit as st 
import streamlit.components.v1
import os
import sys

# Add the parent directory to the path so we can import functions
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from functions.audio_function import generate_announcement_html

# Initialize session state with default values
if 'audio_announcement' not in st.session_state:
    st.session_state.audio_announcement = True
if 'announcement_type' not in st.session_state:
    st.session_state.announcement_type = "텍스트 음성 변환"
if 'tts_rate' not in st.session_state:
    st.session_state.tts_rate = 0.9
if 'tts_volume' not in st.session_state:
    st.session_state.tts_volume = 0.8
if 'tts_pitch' not in st.session_state:
    st.session_state.tts_pitch = 1.0
if 'tts_engine' not in st.session_state:
    st.session_state.tts_engine = "gtts"  # Default to gTTS for better quality
if 'custom_announcement' not in st.session_state:
    st.session_state.custom_announcement = "Your scheduled media {title} starts playing at {date_time}"
if 'uploaded_audio_name' not in st.session_state:
    st.session_state.uploaded_audio_name = None
if 'uploaded_audio_path' not in st.session_state:
    st.session_state.uploaded_audio_path = None

st.title ("🎵 Audio Handler Settings")
title = "Your Sample Media"
st.subheader(f"Media Title: {title}")
# check currently available audio_file in the session state

if st.session_state.get('uploaded_audio_name') and st.session_state.get('uploaded_audio_path'):
    st.info(f"현재 업로드된 오디오 파일: {st.session_state.uploaded_audio_name}")
else:
    st.info("업로드된 오디오 파일이 없습니다.")

with st.sidebar:
    st.subheader("⚙️ Audio옵션")
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    # Audio announcement options
    st.session_state.audio_announcement = st.toggle("음성 알림", value=st.session_state.audio_announcement, help="예약된 미디어 시작 전 음성으로 안내")
    
    if st.session_state.audio_announcement:
        st.markdown("**🔊 음성 알림 설정**")
        st.session_state.announcement_type = st.radio(
            "알림 방식",
            ["텍스트 음성 변환", "미리 녹음된 오디오"],
            index=0 if st.session_state.announcement_type == "텍스트 음성 변환" else 1,
            horizontal=True,
            help="TTS 또는 업로드된 오디오 파일 사용"
        )
        
        if st.session_state.announcement_type == "텍스트 음성 변환":
            # Custom announcement text
            st.session_state.custom_announcement = st.text_area(
                "알림 문구 (사용 가능한 변수: {title}, {date_time})",
                value=st.session_state.custom_announcement,
                height=60,
                help="제목은 {title}, 날짜/시간은 {date_time}으로 자동 대체됩니다"
            )
            
            # TTS settings
            st.markdown("**TTS 설정**")
            
            # TTS Engine selection
            st.session_state.tts_engine = st.selectbox(
                "TTS 엔진 (English text)",
                ["gtts", "browser"],
                index=0 if st.session_state.tts_engine == "gtts" else 1,
                help="gTTS: Better quality for English (requires internet), Browser: Local but variable quality"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.tts_rate = st.slider("말하기 속도", 0.5, 2.0, st.session_state.tts_rate, 0.1)
                st.session_state.tts_pitch = st.slider("음성 높이", 0.0, 2.0, st.session_state.tts_pitch, 0.1)
            with col2:
                st.session_state.tts_volume = st.slider("음량", 0.0, 1.0, st.session_state.tts_volume, 0.1)
        
        else:  # Pre-recorded audio
            uploaded_audio = st.file_uploader(
                "오디오 파일 업로드 (.mp3, .wav, .ogg)",
                type=['mp3', 'wav', 'ogg'],
                help="업로드된 오디오가 알림음으로 재생됩니다"
            )
            
            if uploaded_audio:
                # Store audio file information in session state
                st.session_state.uploaded_audio_name = uploaded_audio.name
                
                # Save the audio file
                import os
                os.makedirs("uploads/audio", exist_ok=True)
                audio_path = os.path.join("uploads/audio", uploaded_audio.name)
                st.session_state.uploaded_audio_path = audio_path
                
                with open(audio_path, "wb") as f:
                    f.write(uploaded_audio.getbuffer())
                st.success(f"오디오 파일이 저장되었습니다: {uploaded_audio.name}")
                
                # Preview audio
                st.audio(audio_path)
            elif st.session_state.uploaded_audio_name and st.session_state.uploaded_audio_path:
                # Display previously uploaded file info
                st.info(f"이전에 업로드된 파일: {st.session_state.uploaded_audio_name}")
                if os.path.exists(st.session_state.uploaded_audio_path):
                    st.audio(st.session_state.uploaded_audio_path)
                else:
                    st.warning("이전에 업로드된 파일을 찾을 수 없습니다. 다시 업로드해주세요.")
                    st.session_state.uploaded_audio_name = None
                    st.session_state.uploaded_audio_path = None
            else:
                # Clear session state if no file is uploaded
                st.session_state.uploaded_audio_name = None
                st.session_state.uploaded_audio_path = None
    
    window = st.slider("재생 허용 범위(±초)", min_value=10, max_value=120, value=60, step=5)
    st.caption(f"현재 시간: **{now.strftime('%Y-%m-%d %H:%M:%S')} (KST)**")
    
from functions.audio_function import generate_announcement_html


# Test TTS section
st.subheader("🔊 TTS 품질 테스트")
if st.session_state.audio_announcement and st.session_state.announcement_type == "텍스트 음성 변환":
    test_text = st.text_input(
        "테스트 텍스트 (English text works best with gTTS)",
        value="Hello, this is a test of the text-to-speech system. The scheduled media will start playing soon.",
        help="Enter text to test the selected TTS engine"
    )
    
    if st.button("🎵 TTS 테스트"):
        if test_text.strip():
            # Create a mock target object for testing
            class MockTarget:
                def __init__(self):
                    self.title = "Test Media"
                    from datetime import datetime
                    self.run_at = datetime.now()
            
            mock_target = MockTarget()
            
            # Generate test HTML
            test_html = generate_announcement_html(
                target=mock_target,
                audio_announcement=True,
                announcement_type="텍스트 음성 변환",
                custom_announcement=test_text,
                tts_rate=st.session_state.tts_rate,
                tts_volume=st.session_state.tts_volume,
                tts_pitch=st.session_state.tts_pitch,
                tts_engine=st.session_state.tts_engine
            )
            
            if test_html:
                # Display the HTML (this will play the audio)
                st.components.v1.html(test_html, height=0)
                if st.session_state.tts_engine == "gtts":
                    st.success("🎵 gTTS audio generated and played! (High quality)")
                else:
                    st.success("🎵 Browser TTS played! (May vary by browser)")
            else:
                st.error("Failed to generate audio. Check your internet connection if using gTTS.")
        else:
            st.warning("Please enter some text to test.")

st.divider()

# Additional information about TTS engines
st.subheader("📋 TTS 엔진 정보")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🌐 gTTS (Google Text-to-Speech)**")
    st.markdown("""
    - ✅ 고품질 음성
    - ✅ 자연스러운 발음
    - ✅ 일관된 품질
    - ❌ 인터넷 연결 필요
    - ❌ 영어 텍스트에 최적화
    """)

with col2:
    st.markdown("**🌍 Browser TTS**")
    st.markdown("""
    - ✅ 인터넷 연결 불필요
    - ✅ 다양한 언어 지원
    - ✅ 속도/높이 조절 가능
    - ❌ 브라우저별 품질 차이
    - ❌ 일관성 부족
    """)

st.info("💡 **추천**: 영어 텍스트의 경우 gTTS를 사용하면 더 나은 음질을 경험할 수 있습니다.")