# Audio-related functions for TTS and audio playback
import os
import base64


def generate_announcement_html(target, audio_announcement, announcement_type=None, custom_announcement=None, 
                             tts_rate=0.9, tts_volume=0.8, tts_pitch=1.0, uploaded_audio=None):
    """
    Generate HTML for audio announcement based on user settings
    
    Args:
        target: Schedule object with title and run_at
        audio_announcement: Whether to play announcement
        announcement_type: "텍스트 음성 변환" or "미리 녹음된 오디오"
        custom_announcement: Custom text template
        tts_rate, tts_volume, tts_pitch: TTS settings
        uploaded_audio: Uploaded audio file object
    
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
        
        # Escape quotes for JavaScript
        announcement_text = announcement_text.replace('"', '\\"').replace("'", "\\'")
        
        return f"""
        <script>
        if ('speechSynthesis' in window) {{
            const utterance = new SpeechSynthesisUtterance("{announcement_text}");
            utterance.rate = {tts_rate};
            utterance.volume = {tts_volume};
            utterance.pitch = {tts_pitch};
            speechSynthesis.speak(utterance);
        }}
        </script>
        """
