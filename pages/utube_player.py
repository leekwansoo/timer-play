#Play youtube video using two methods
import webbrowser
import streamlit as st
import streamlit.components.v1 as components
from pytube import YouTube
import re

def extract_youtube_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def create_autoplay_html(video_id):
    """Create HTML with autoplay YouTube embed"""
    html = f"""
    <div style="position:relative;width:100%;padding-top:56.25%;">
      <iframe
        src="https://www.youtube.com/embed/{video_id}?autoplay=1&mute=0&controls=1&rel=0"
        title="YouTube video player"
        style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
        allow="autoplay; encrypted-media; picture-in-picture"
        allowfullscreen
      ></iframe>
    </div>
    """
    return html

st.title("파이썬 유튜브 플레이어")
youtube_url = st.text_input("유튜브 URL을 입력하세요:")
if youtube_url:
     try:
         yt = YouTube(youtube_url)
         
         # Try to get title with error handling
         try:
             video_title = yt.title
             st.title(video_title)
         except Exception as title_error:
             st.warning(f"제목을 가져올 수 없습니다: {title_error}")
             st.title("YouTube 비디오")
         
         # Extract video ID and create autoplay embed
         video_id = extract_youtube_video_id(youtube_url)
         if video_id:
             st.success("자동재생 비디오가 로드됩니다...")
             components.html(create_autoplay_html(video_id), height=500)
         else:
             # Fallback to regular video if ID extraction fails
             st.warning("비디오 ID를 추출할 수 없어 일반 플레이어를 사용합니다.")
             st.video(youtube_url)
         
         # Optional: Open in web browser
         if st.button("웹 브라우저에서 열기"):
             webbrowser.open(youtube_url)
         
         # Alternative method: Try to get stream URL
         try:
             stream_url = yt.streams.get_highest_resolution().url
             st.info("고화질 스트림 URL을 찾았습니다.")
         except Exception as stream_error:
             st.warning(f"스트림 정보를 가져올 수 없습니다: {stream_error}")
         
     except Exception as e:
         st.error(f"오류 발생: {e}")


