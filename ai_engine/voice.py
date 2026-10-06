"""
Voice Copilot — Multilingual Text-to-Speech (TTS) for Patient Literacy.
Generates spoken audio explanations in Tamil and English from clinical summaries.
"""
from __future__ import annotations

import io
import os
from typing import Optional


def generate_audio(text: str, lang: str = "en", output_path: Optional[str] = None) -> Optional[bytes]:
    """
    Generate speech audio (MP3) from text in English or Tamil.
    
    Parameters
    ----------
    text : str
        The summary text to speak.
    lang : str
        Language code ('en' or 'ta').
    output_path : str, optional
        If provided, writes the MP3 file to this path.
        
    Returns
    -------
    bytes or None
        Audio MP3 bytes if successful, None otherwise.
    """
    if not text or not text.strip():
        return None

    clean_text = text.strip()
    # Normalize language code (en, ta, hi)
    lang_lower = (lang or "en").lower().strip()
    if lang_lower in ("ta", "tamil"):
        tts_lang = "ta"
    elif lang_lower in ("hi", "hindi"):
        tts_lang = "hi"
    else:
        tts_lang = "en"

    try:
        from gtts import gTTS
        tts = gTTS(text=clean_text, lang=tts_lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        audio_bytes = buf.read()

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

        return audio_bytes
    except Exception:
        # Graceful fallback: return None if offline / rate limited
        return None


def get_browser_speech_html(text_en: str, text_ta: str, text_hi: str = "") -> str:
    """
    Generate interactive HTML with Web Speech API audio buttons
    for zero-latency browser-native text-to-speech in English, Tamil, and Hindi.
    """
    safe_en = (text_en or "").replace("'", "\\'").replace("\n", " ")
    safe_ta = (text_ta or "").replace("'", "\\'").replace("\n", " ")
    safe_hi = (text_hi or "").replace("'", "\\'").replace("\n", " ")
    return f"""
    <div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 16px; border-radius: 12px; border: 1px solid #334155; margin-top: 12px;">
      <h4 style="color: #38bdf8; margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">
        🎙️ Multilingual Voice Copilot — Audio Explanation (குரல் / आवाज़)
      </h4>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <button onclick="speakText('{safe_en}', 'en-US')" style="background: #2563eb; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;">
          🔊 Listen in English
        </button>
        <button onclick="speakText('{safe_ta}', 'ta-IN')" style="background: #059669; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;">
          🗣️ தமிழில் கேட்க (Tamil)
        </button>
        <button onclick="speakText('{safe_hi}', 'hi-IN')" style="background: #ea580c; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;">
          🎙️ हिंदी में सुनें (Hindi)
        </button>
        <button onclick="window.speechSynthesis.cancel()" style="background: #dc2626; color: white; border: none; padding: 10px 14px; border-radius: 8px; font-weight: 600; cursor: pointer;">
          ⏹️ Stop
        </button>
      </div>
      <script>
        function speakText(text, lang) {{
          window.speechSynthesis.cancel();
          if (!text) return;
          const u = new SpeechSynthesisUtterance(text);
          u.lang = lang;
          u.rate = 0.95;
          window.speechSynthesis.speak(u);
        }}
      </script>
    </div>
    """
