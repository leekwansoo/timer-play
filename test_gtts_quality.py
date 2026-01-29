#!/usr/bin/env python3
"""
Test script to demonstrate gTTS vs Browser TTS quality
Run this to see the difference in audio generation approaches
"""

import os
import sys
import tempfile
from functions.audio_function import is_english_text, generate_gtts_audio_html

def test_language_detection():
    print("🔍 Testing Language Detection:")
    print("─" * 40)
    
    test_cases = [
        "Hello, your scheduled media will start playing soon.",
        "안녕하세요, 예약된 미디어가 곧 재생됩니다.",
        "混合された text with multiple languages",
        "123 Numbers and symbols @#$%",
        "This is 100% English text for testing purposes."
    ]
    
    for i, text in enumerate(test_cases, 1):
        is_english = is_english_text(text)
        print(f"{i}. {'✅ English' if is_english else '❌ Non-English'}: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    print()

def test_gtts_generation():
    print("🎵 Testing gTTS Generation:")
    print("─" * 40)
    
    test_text = "Hello! This is a test of Google Text to Speech quality."
    
    try:
        # Test if gTTS can generate audio
        html_output = generate_gtts_audio_html(test_text, 0.8)
        
        if html_output:
            print("✅ gTTS audio generation: SUCCESS")
            print(f"📝 Generated HTML length: {len(html_output)} characters")
            print("🔊 Audio quality: High (MP3 format)")
            print("🌐 Requires: Internet connection")
        else:
            print("❌ gTTS audio generation: FAILED")
            
    except Exception as e:
        print(f"❌ gTTS error: {e}")
    
    print()

def compare_methods():
    print("⚖️  Comparison Summary:")
    print("─" * 40)
    print("🌐 gTTS (Google Text-to-Speech):")
    print("   ✅ High-quality, natural voice")
    print("   ✅ Consistent pronunciation") 
    print("   ✅ Professional audio quality")
    print("   ❌ Requires internet connection")
    print("   ❌ Best for English only")
    print()
    print("🌍 Browser TTS (speechSynthesis):")
    print("   ✅ Works offline")
    print("   ✅ Supports multiple languages")
    print("   ✅ Customizable rate/pitch/volume")
    print("   ❌ Quality varies by browser/OS")
    print("   ❌ Robotic sound in some browsers")

if __name__ == "__main__":
    print("🎤 Audio Quality Test - gTTS vs Browser TTS")
    print("=" * 50)
    print()
    
    test_language_detection()
    test_gtts_generation()
    compare_methods()
    
    print("\n🚀 Ready to use improved audio in your timer-play app!")
    print("   Run: streamlit run pages/audio_handler.py")
    print("   Open the audio handler page to test both engines.")