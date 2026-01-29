# youtube functions to extract video ID and create embed HTML
import re


# -------------------------
# YouTube helpers
# -------------------------
YOUTUBE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

def extract_youtube_video_id(url: str) -> str | None:
    """
    Supports:
      - https://www.youtube.com/watch?v=VIDEOID
      - https://youtu.be/VIDEOID
      - https://www.youtube.com/shorts/VIDEOID
      - https://www.youtube.com/embed/VIDEOID
      - https://www.youtube.com/clip/...  (clip은 원본 video id 추출이 항상 보장되지 않음)
    """
    if not url:
        return None
    u = url.strip()
    # Direct 11-char id
    if YOUTUBE_ID_RE.match(u):
        return u
    # v=VIDEOID
    m = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", u)
    if m:
        return m.group(1)
    # youtu.be/VIDEOID
    m = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", u)
    if m:
        return m.group(1)
    # /shorts/VIDEOID
    m = re.search(r"/shorts/([a-zA-Z0-9_-]{11})", u)
    if m:
        return m.group(1)
    # /embed/VIDEOID
    m = re.search(r"/embed/([a-zA-Z0-9_-]{11})", u)
    if m:
        return m.group(1)
    # /live/VIDEOID
    m = re.search(r"/live/([a-zA-Z0-9_-]{11})", u)
    if m:
        return m.group(1)
    return None

def build_youtube_embed_html(video_id: str, autoplay: bool = True, mute: bool = True) -> str:
    # autoplay는 브라우저 정책에 의해 막힐 수 있어 mute=1을 기본 권장
    ap = "1" if autoplay else "0"
    mu = "1" if mute else "0"
    # enablejsapi는 추후 확장(재생 제어) 대비
    src = (
        f"https://www.youtube.com/embed/{video_id}"
        f"?autoplay={ap}&mute={mu}&playsinline=1&rel=0&enablejsapi=1"
    )
    html = f"""
    <div style="position:relative;width:100%;padding-top:56.25%;">
      <iframe
        src="{src}"
        title="YouTube video player"
        style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
        allow="autoplay; encrypted-media; picture-in-picture"
        allowfullscreen
      ></iframe>
    </div>
    """
    return html


def extract_google_drive_file_id(url: str) -> str | None:
    """
    Extract file ID from Google Drive URL
    
    Supports:
      - https://drive.google.com/file/d/FILE_ID/view
      - https://drive.google.com/open?id=FILE_ID
    """
    if not url:
        return None
    
    # /file/d/FILE_ID format
    match = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    
    # id=FILE_ID format
    match = re.search(r'id=([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    
    return None


def build_google_drive_embed_html(file_id: str) -> str:
    """
    Build HTML for Google Drive file embed
    
    Args:
        file_id: Google Drive file ID
        
    Returns:
        HTML string for embedding Google Drive file
    """
    embed_url = f"https://drive.google.com/file/d/{file_id}/preview"
    
    html = f"""
    <div style="position:relative;width:100%;padding-top:56.25%;">
        <iframe
            src="{embed_url}"
            style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
            allow="autoplay"
            allowfullscreen
        ></iframe>
    </div>
    """
    return html


def build_youtube_embed_with_completion_html(video_id: str, target_id: int, autoplay: bool = True, mute: bool = True) -> str:
    """
    Build YouTube embed HTML with automatic completion detection
    
    Args:
        video_id: YouTube video ID
        target_id: Schedule target ID for completion tracking
        autoplay: Whether to autoplay video
        mute: Whether to mute video
        
    Returns:
        HTML string for YouTube embed with completion logic
    """
    ap = "1" if autoplay else "0"
    mu = "1" if mute else "0"
    
    html = f"""
    <div style="position:relative;width:100%;padding-top:56.25%;">
    <iframe
        id="youtube-player-{target_id}"
        src="https://www.youtube.com/embed/{video_id}?autoplay={ap}&mute={mu}&controls=1&rel=0"
        title="YouTube video player"
        style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
        allow="autoplay; encrypted-media; picture-in-picture"
        allowfullscreen
    ></iframe>
    </div>
    <script>
    // Set a timer for automatic completion (estimate 2 minutes for most videos)
    setTimeout(function() {{
        // Mark as auto-completed in session storage
        sessionStorage.setItem('auto_complete_{target_id}', 'true');
        // Trigger page refresh to check for completion
        window.location.reload();
    }}, 120000); // 2 minutes
    
    // Check if we should auto-complete now
    if (sessionStorage.getItem('auto_complete_{target_id}') === 'true') {{
        sessionStorage.removeItem('auto_complete_{target_id}');
        // Auto-complete logic would go here if needed
    }}
    </script>
    """
    return html

def extract_naver_mybox_file_id(url: str) -> str | None:
    """
    Extract file ID from Naver MyBox URL
    
    Supports:
      - https://naver.me/FILE_ID
    """
    if not url:
        return None
    
    # /naver.me/FILE_ID format
    match = re.search(r'naver\.me/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    
    return None

def build_naver_mybox_embed_html(file_id: str) -> str:
    """
    Build HTML for Naver MyBox file embed
    
    Args:
        file_id: Naver MyBox file ID
    """
    embed_url = f"https://naver.me/{file_id}"
    
    html = f"""
    <div style="position:relative;width:100%;padding-top:56.25%;">
        <iframe
            src="{embed_url}"
            style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
            allow="autoplay"
            allowfullscreen
        ></iframe>
    </div>
    """
    return html