import json
import streamlit as st
import os
import hashlib
from gtts import gTTS
import tempfile

import json
import streamlit as st
import os
import hashlib
from gtts import gTTS
import tempfile
import base64
from io import BytesIO

def generate_audio_base64(text, lang='en'):
    """Generate audio data as base64 string from text using gTTS"""
    try:
        # Create gTTS object
        tts = gTTS(text=text, lang=lang, slow=False)
        
        # Save to BytesIO buffer
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Convert to base64
        audio_base64 = base64.b64encode(audio_buffer.getvalue()).decode()
        return f"data:audio/mpeg;base64,{audio_base64}"
        
    except Exception as e:
        print(f"Error generating audio for '{text}': {e}")
        return None