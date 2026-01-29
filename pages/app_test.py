import os
import streamlit as st
import webbrowser
import re
from functions.youtube_function import build_youtube_embed_html 
from functions.youtube_function import (extract_youtube_video_id, build_youtube_embed_html)
from functions.youtube_function import (extract_google_drive_file_id, build_google_drive_embed_html)
from functions.youtube_function import (extract_naver_mybox_file_id, build_naver_mybox_embed_html)


st.title("앱 타이머 테스트")
video_path = st.text_input("비디오 파일 경로 입력 (예: path/to/video.mp4)")
if st.button("비디오 재생"):
    if video_path.startswith("uploaded_file:"):
        content_type = "uploaded"
    elif "youtube.com" in video_path or "youtu.be" in video_path:
        content_type = "youtube"
    elif "drive.google.com" in video_path or "docs.google.com" in video_path:
        content_type = "google_drive"
    elif "naver.me" in video_path:
        content_type = "naver_mybox"
    else:
        content_type = "other"
        
    if content_type == "uploaded":
            # Handle uploaded files
            file_name = video_path.replace("uploaded_file:", "")
            st.video(f"uploaded/{file_name}")

    elif content_type == "youtube":
            # Handle YouTube content
            vid = extract_youtube_video_id(video_path)
            if vid:
                # Create YouTube embed with automatic completion detection
                embed_html = build_youtube_embed_html(vid, video_path.id)
                st.components.v1.html(embed_html, height=420)
            else:
                st.error(
                    "YouTube URL에서 video id를 추출하지 못했어요. "
                    "지원 예: watch?v=, youtu.be/, shorts/ 형태"
                )
                st.write("입력 URL:", video_path)
                                
        
    elif content_type == "google_drive":
        # Handle Google Drive content
       
        
        # Extract file ID from Google Drive URL and create embed
        file_id = extract_google_drive_file_id(video_path)
        
        if file_id:
            # Create Google Drive embed
            embed_html = build_google_drive_embed_html(file_id)
            st.components.v1.html(embed_html, height=420)
        else:
            st.error("Google Drive URL에서 파일 ID를 추출하지 못했어요.")
            st.write("입력 URL:", video_path)
            if st.button("🌐 브라우저에서 열기", width='stretch'):
                webbrowser.open(video_path)
     
    elif content_type == "naver_mybox":
        # Handle Naver MyBox content
       
        
        # Extract file ID from Naver MyBox URL and create embed
        file_id = extract_naver_mybox_file_id(video_path)
        
        if file_id:
            # Create Naver MyBox embed
            embed_html = build_naver_mybox_embed_html(file_id)
            print(embed_html)
            st.components.v1.html(embed_html, height=420)
        else:
            st.error("Naver MyBox URL에서 파일 ID를 추출하지 못했어요.")
            st.write("입력 URL:", video_path)
            if st.button("🌐 브라우저에서 열기", width='stretch'):
                webbrowser.open(video_path)   
    else:
        # Handle other video files
        try:
            st.video(video_path)
        except Exception as e:
            st.error(f"비디오 재생 중 오류가 발생했어요: {e}")
            if st.button("🌐 브라우저에서 열기", width='stretch'):
                webbrowser.open(video_path)
       
        
st.markdown("---")
st.subheader("File Uploader 테스트 섹션")
name = st.text_input("작업 이름 입력")
if name:
    st.write(f"안녕하세요, {name}님! 앱 타이머 테스트에 오신 것을 환영합니다.")
# Testing file uploader and video display
uploaded = st.file_uploader("파일 업로드", type=["mp4", "avi", "mov"])
if uploaded:
    file_name = uploaded.name
    if uploaded.name.split(".")[1] not in ["mp4", "avi", "mov"]:
        st.error("지원하지 않는 파일 형식입니다. mp4, avi, mov 파일만 업로드해주세요.")
    file_name = uploaded.name if uploaded else "No file uploaded"
    # store the uploaded file in the uploaded folder
    with open(f"uploaded/{file_name}", "wb") as f:
        f.write(uploaded.getbuffer())
    st.success(f"파일 '{file_name}'이(가) 업로드되었습니다.")
    print(f"uploaded file: {file_name} is stored in uploaded folder")
    st.video(f"uploaded/{file_name}")
 
# Audio Function Testing   
from functions.audio_function import generate_announcement_html

st.subheader("Audio Announcement 테스트 섹션")

st.sidebar.header("오디오 공지 설정")
audio_announcement = st.sidebar.checkbox("오디오 공지 재생", value=True)
announcement_type = st.sidebar.radio(
    "공지 유형 선택",
    ["텍스트 음성 변환", "미리 녹음된 오디오"],
    horizontal=True    
)

tts_rate = st.sidebar.slider("TTS 속도", 0.5, 1.5, 0.9)
tts_volume = st.sidebar.slider("TTS 볼륨", 0.0, 1.0, 0.8)
tts_pitch = st.sidebar.slider("TTS 음높이", 0.5, 2.0, 1.0)

custom_announcement = st.text_area(
    "맞춤 공지 템플릿 (선택 사항)", '')
if st.button("공지 생성 및 재생"):
    class Schedule:
        def __init__(self, title, run_at):
            self.title = title
            self.run_at = run_at

    from datetime import datetime
    test_schedule = Schedule(title="테스트 미디어", run_at=datetime.now())
    
    announcement_html = generate_announcement_html(
        target=test_schedule,
        audio_announcement=audio_announcement,
        announcement_type=announcement_type,
        custom_announcement=custom_announcement if custom_announcement else None,
        tts_rate=tts_rate,
        tts_volume=tts_volume,
        tts_pitch=tts_pitch,
        uploaded_audio=uploaded_audio if announcement_type == "미리 녹음된 오디오" else None
    )
    
    if announcement_html:
        st.components.v1.html(announcement_html, height=0)
    else:
        st.info("오디오 공지가 생성되지 않았습니다.")

st.sidebar.markdown("### 미리 녹음된 오디오 업로드")
uploaded_audio = st.sidebar.file_uploader("오디오 파일 업로드", type=["mp3", "wav", "ogg"])
if uploaded_audio:
    # Save uploaded audio file to uploaded_audio/audio folder
    audio_path = os.path.join("uploaded_audio/audio", uploaded_audio.name)
    with open(audio_path, "wb") as f:
        f.write(uploaded_audio.getbuffer())
    st.sidebar.success(f"오디오 파일 '{uploaded_audio.name}'이(가) 업로드되었습니다.")