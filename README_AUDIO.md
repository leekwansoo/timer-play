# 🎵 Audio Implementation - Timer Play App

## Overview

This document describes the enhanced audio announcement system for the Timer Play application, featuring high-quality Text-to-Speech (TTS) capabilities using Google Text-to-Speech (gTTS) for English content.

## ✨ Features

### 🎯 Core Capabilities
- **Dual TTS Engine Support**: Choose between gTTS (high quality) and Browser TTS (universal)
- **Smart Language Detection**: Automatically detects English text for optimal TTS engine selection
- **High-Quality Audio**: Professional-grade voice synthesis for English announcements
- **Fallback System**: Seamless fallback to browser TTS for non-English content or connectivity issues
- **Custom Audio Upload**: Support for pre-recorded announcement audio files
- **Live Testing**: Real-time audio preview and quality testing

### 🎛️ Audio Controls
- **TTS Engine Selection**: gTTS vs Browser TTS
- **Voice Parameters**: Rate, volume, and pitch control (Browser TTS)
- **Custom Messages**: Personalized announcement templates
- **File Upload**: MP3, WAV, OGG audio file support

## 🚀 Quick Start

### Prerequisites
```bash
pip install gtts streamlit
```

### Basic Usage
1. Run the audio handler: `streamlit run pages/audio_handler.py`
2. Select your preferred TTS engine (gTTS recommended for English)
3. Customize your announcement message
4. Test audio quality using the built-in test feature

## 🛠️ Technical Implementation

### Architecture Overview
```
Audio Handler (pages/audio_handler.py)
    ↓
Audio Functions (functions/audio_function.py)
    ├── Language Detection (is_english_text)
    ├── gTTS Generation (generate_gtts_audio_html)
    └── Main Generator (generate_announcement_html)
```

### Key Components

#### 1. Language Detection
```python
def is_english_text(text):
    """Smart detection of English content for optimal TTS routing"""
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    total_chars = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
    if total_chars == 0:
        return True
    return ascii_chars / total_chars > 0.8
```

#### 2. High-Quality Audio Generation
```python
def generate_gtts_audio_html(text, volume=0.8):
    """Generate premium quality audio using Google TTS"""
    tts = gTTS(text=text, lang='en', slow=False)
    # Converts to base64-embedded HTML audio
```

#### 3. Smart Engine Selection
- **English Text + gTTS Selected** → High-quality gTTS audio
- **Non-English Text** → Browser TTS (supports multiple languages)
- **gTTS Failure** → Automatic fallback to Browser TTS
- **Offline Mode** → Browser TTS only

## 🎵 Audio Quality Comparison

### gTTS (Google Text-to-Speech)
- ✅ **Professional Quality**: Natural, human-like voice
- ✅ **Consistent Output**: Same quality across all devices
- ✅ **Clear Pronunciation**: Excellent articulation
- ✅ **Optimized for English**: Native language support
- ❌ **Internet Required**: Online connectivity needed
- ❌ **English Only**: Limited to English language

### Browser TTS (speechSynthesis API)
- ✅ **Offline Capable**: Works without internet
- ✅ **Multi-Language**: Supports various languages
- ✅ **Customizable**: Rate, pitch, volume control
- ✅ **Universal Support**: Available in all modern browsers
- ❌ **Variable Quality**: Depends on browser/OS
- ❌ **Robotic Sound**: Less natural than gTTS

## 📋 Configuration Options

### Session State Variables
```python
# Core Settings
'audio_announcement': True/False          # Enable/disable audio
'announcement_type': "텍스트 음성 변환"    # TTS or uploaded audio
'tts_engine': "gtts"                      # TTS engine selection

# TTS Parameters (Browser TTS only)
'tts_rate': 0.9                           # Speaking rate (0.5-2.0)
'tts_volume': 0.8                         # Volume level (0.0-1.0)
'tts_pitch': 1.0                          # Voice pitch (0.0-2.0)

# Message Customization
'custom_announcement': "Your message..."   # Custom announcement template

# Uploaded Audio
'uploaded_audio_name': "filename.mp3"     # Uploaded audio filename
'uploaded_audio_path': "/path/to/file"    # Full path to uploaded audio
```

### Message Templates
Use these variables in your custom announcements:
- `{title}` - Media title
- `{date_time}` - Scheduled date and time

Example:
```
"Hello! Your scheduled media '{title}' will start playing at {date_time}. Please get ready!"
```

## 🔧 Integration Guide

### Adding Audio to Your Content
```python
from functions.audio_function import generate_announcement_html

# Generate announcement HTML
announcement_html = generate_announcement_html(
    target=schedule_object,
    audio_announcement=True,
    announcement_type="텍스트 음성 변환",
    custom_announcement="Your custom message",
    tts_engine="gtts"  # Key addition for gTTS support
)

# Play audio
if announcement_html:
    st.components.v1.html(announcement_html, height=0)
```

### File Structure
```
timer-play-main/
├── functions/
│   └── audio_function.py          # Core audio processing
├── pages/
│   └── audio_handler.py           # Audio configuration UI  
├── uploads/
│   └── audio/                     # Uploaded audio files
├── requirements.txt               # Dependencies (includes gtts)
└── app.py                         # Main app with audio integration
```

## 🧪 Testing and Quality Assurance

### Manual Testing
1. **Language Detection Test**:
   ```python
   python test_gtts_quality.py
   ```

2. **Live Audio Test**:
   - Open audio handler page
   - Enter test text in "TTS 품질 테스트" section
   - Click "🎵 TTS 테스트" button
   - Compare gTTS vs Browser TTS quality

3. **Integration Test**:
   - Create scheduled media in main app
   - Verify audio plays at scheduled time
   - Test both English and non-English content

### Automated Quality Checks
- ✅ Language detection accuracy
- ✅ gTTS generation success rate
- ✅ Fallback mechanism reliability
- ✅ Audio format compatibility

## 🐛 Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'gtts'"
```bash
# Solution: Install gTTS
pip install gtts
# Or using conda
conda install gtts
```

#### "gTTS generation failed: Connection error"
- **Cause**: No internet connection
- **Solution**: System automatically falls back to Browser TTS
- **Prevention**: Check network connectivity

#### "Audio not playing"
- **Check**: Browser permissions for audio playback
- **Check**: Volume levels and mute settings
- **Check**: JavaScript console for errors

#### "Poor audio quality"
- **For English**: Use gTTS engine (requires internet)
- **For other languages**: Browser TTS is the best option
- **Check**: Browser and OS audio drivers

### Performance Optimization
- gTTS audio is cached as base64 data
- Temporary files are avoided using BytesIO
- Fallback is instantaneous on connection failure

## 📚 API Reference

### Core Functions

#### `generate_announcement_html()`
Main function for generating audio announcements.

**Parameters:**
- `target` (Schedule): Schedule object with title and run_at
- `audio_announcement` (bool): Enable/disable audio
- `announcement_type` (str): "텍스트 음성 변환" or "미리 녹음된 오디오"
- `custom_announcement` (str): Custom message template
- `tts_rate` (float): Speaking rate (0.5-2.0)
- `tts_volume` (float): Volume level (0.0-1.0)
- `tts_pitch` (float): Voice pitch (0.0-2.0)
- `uploaded_audio` (object): Uploaded audio file object
- `tts_engine` (str): "gtts" or "browser"

**Returns:** HTML string with embedded audio

#### `is_english_text(text)`
Detects if text is primarily English for optimal TTS engine selection.

**Parameters:**
- `text` (str): Text to analyze

**Returns:** Boolean (True if primarily English)

#### `generate_gtts_audio_html(text, volume)`
Generates high-quality audio using Google TTS.

**Parameters:**
- `text` (str): Text to synthesize
- `volume` (float): Audio volume (0.0-1.0)

**Returns:** HTML with base64 audio or None on failure

## 🔄 Version History

### v1.0.0 - Initial gTTS Integration
- ✅ Added gTTS support for English text
- ✅ Implemented smart language detection
- ✅ Created fallback system
- ✅ Added TTS engine selection UI
- ✅ Integrated live testing feature

### Planned Enhancements
- 🔄 Additional language support for gTTS
- 🔄 Voice selection options
- 🔄 Audio caching for repeated announcements
- 🔄 Batch audio generation
- 🔄 Custom voice training integration

## 🤝 Contributing

### Adding New TTS Engines
1. Create new generation function in `audio_function.py`
2. Add engine option to `audio_handler.py`
3. Update language detection if needed
4. Add fallback logic
5. Test integration

### Code Standards
- Follow existing naming conventions
- Add comprehensive error handling
- Include documentation strings
- Test edge cases thoroughly

## 📄 License

This audio implementation is part of the Timer Play application. Please refer to the main project license for usage terms.

---

## 📞 Support

For audio-related issues:
1. Check this README first
2. Run the test script: `python test_gtts_quality.py`
3. Verify network connectivity for gTTS
4. Check browser console for JavaScript errors

**Note**: This implementation provides significantly improved audio quality for English announcements while maintaining compatibility with all existing features.