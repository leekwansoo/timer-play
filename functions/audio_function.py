# Audio-related functions for TTS and audio playback
import os
import base64
import tempfile
import re
from gtts import gTTS
from io import BytesIO
from datetime import datetime

uploaded_audio = "uploaded_audio/alert.mp3"

def is_english_text(text):
    """
    Simple check to determine if text is primarily English
    """
    # Remove punctuation and check if most characters are ASCII
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    total_chars = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
    if total_chars == 0:
        return True
    return ascii_chars / total_chars > 0.8


def generate_gtts_audio_html(text, volume=0.8):
    """
    Generate HTML audio element using gTTS for better English audio quality
    """
    try:
        # Create gTTS object
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Use BytesIO instead of temporary file to avoid file conflicts
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Encode to base64
        audio_data = base64.b64encode(audio_buffer.getvalue()).decode()
        
        return f"""
        <script>
        const audio = new Audio('data:audio/mpeg;base64,{audio_data}');
        audio.volume = {volume};
        audio.play().catch(e => console.log('gTTS Audio play failed:', e));
        </script>
        """
    except Exception as e:
        print(f"gTTS generation failed: {e}")
        return None


def generate_announcement_html(target, audio_announcement=True, announcement_type=None, custom_announcement=None, 
                             tts_rate=0.9, tts_volume=0.8, tts_pitch=1.0, uploaded_audio=None, tts_engine="gtts"):
    """
    Generate HTML for audio announcement based on user settings
    
    Args:
        target: Schedule object with title and run_at
        audio_announcement: Whether to play announcement
        announcement_type: "텍스트 음성 변환" or "미리 녹음된 오디오"
        custom_announcement: Custom text template
        tts_rate, tts_volume, tts_pitch: TTS settings
        uploaded_audio: Uploaded audio file object
        tts_engine: "gtts" for Google TTS or "browser" for browser TTS
    
    Returns:
        HTML string for announcement or empty string
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] generate_announcement_html received")
    if not audio_announcement:
        return ""
    
    if announcement_type == "음성화일" and uploaded_audio:
        # Use uploaded audio file
        audio_path = os.path.join("uploads/audio", uploaded_audio.name)
        # Convert to base64 for embedding
        try:
            with open(audio_path, "rb") as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode()
                audio_type = "mpeg" if uploaded_audio.name.endswith('.mp3') else "wav"
                
                return f"""
                <script>
                const audio = new Audio('data:audio/{audio_type};base64,{audio_data}');
                audio.volume = {tts_volume};
                audio.play().catch(e => console.log('Audio play failed:', e));
                </script>
                """
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return ""
    
    else:
        # Use text-to-speech
        default_text = "Your scheduled media {title} starts playing at {date_time}"
        text_template = custom_announcement or default_text
        
        # Replace variables in template
        announcement_text = text_template.format(
            title=target.title or "untitled",
            date_time=target.run_at.strftime('%B %d, %Y at %H:%M')
        )
        
        # Try gTTS for English text first (better quality) if selected
        # gTTS provides superior audio quality for English but requires internet connection
        if tts_engine == "gtts" and is_english_text(announcement_text):
            gtts_html = generate_gtts_audio_html(announcement_text, tts_volume)
            if gtts_html:
                return gtts_html
        
        # Fallback to browser TTS (for non-English or if gTTS fails)
        # Escape quotes for JavaScript
        announcement_text_escaped = announcement_text.replace('"', '\\"').replace("'", "\\'")
        
        return f"""
        <script>
        if ('speechSynthesis' in window) {{
            const utterance = new SpeechSynthesisUtterance("{announcement_text_escaped}");
            utterance.rate = {tts_rate};
            utterance.volume = {tts_volume};
            utterance.pitch = {tts_pitch};
            speechSynthesis.speak(utterance);
        }}
        </script>
        """

def generate_announcement_html_wo_tts_parameter(target, audio_announcement, announcement_type=None, custom_announcement=None, 
                             tts_parameter = None):
    """
    Generate HTML for audio announcement based on user settings
    
    Args:
        target: Schedule object with title and run_at
        audio_announcement: Whether to play announcement
        announcement_type: "텍스트 음성 변환" or "미리 녹음된 오디오"
        custom_announcement: Custom text template
        tts_rate, tts_volume, tts_pitch: TTS settings
        uploaded_audio: Uploaded audio file object
        tts_engine: "gtts" for Google TTS or "browser" for browser TTS
    
    Returns:
        HTML string for announcement or empty string
    """
    if not audio_announcement:
        return ""
    
    if announcement_type == "미리 녹음된 오디오" and uploaded_audio:
        # Use uploaded audio file
        audio_path = os.path.join("uploads/audio", uploaded_audio.name)
        # Convert to base64 for embedding
        try:
            with open(audio_path, "rb") as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode()
                audio_type = "mpeg" if uploaded_audio.name.endswith('.mp3') else "wav"
                
                return f"""
                <script>
                const audio = new Audio('data:audio/{audio_type};base64,{audio_data}');
                audio.volume = {tts_volume};
                audio.play().catch(e => console.log('Audio play failed:', e));
                </script>
                """
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return ""
    
    else:
        # Use text-to-speech
        default_text = "Your scheduled media {title} starts playing at {date_time}"
        text_template = custom_announcement or default_text
        
        # Replace variables in template
        announcement_text = text_template.format(
            title=target.title or "untitled",
            date_time=target.run_at.strftime('%B %d, %Y at %H:%M')
        )
        
        # Try gTTS for English text first (better quality) if selected
        # gTTS provides superior audio quality for English but requires internet connection
        if tts_engine == "gtts" and is_english_text(announcement_text):
            gtts_html = generate_gtts_audio_html(announcement_text, tts_volume)
            if gtts_html:
                return gtts_html
        
        # Fallback to browser TTS (for non-English or if gTTS fails)
        # Escape quotes for JavaScript
        announcement_text_escaped = announcement_text.replace('"', '\\"').replace("'", "\\'")
        
        return f"""
        <script>
        if ('speechSynthesis' in window) {{
            const utterance = new SpeechSynthesisUtterance("{announcement_text_escaped}");
            utterance.rate = {tts_rate};
            utterance.volume = {tts_volume};
            utterance.pitch = {tts_pitch};
            speechSynthesis.speak(utterance);
        }}
        </script>
        """
