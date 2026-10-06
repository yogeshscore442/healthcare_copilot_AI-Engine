"""
Unit tests for Voice Copilot text-to-speech engine.
"""
from ai_engine.voice import get_browser_speech_html


def test_browser_speech_html():
    html = get_browser_speech_html("Patient should take medicines.", "மருந்துகளை தவறாமல் உட்கொள்ளவும்.")
    assert "Voice Copilot" in html
    assert "SpeechSynthesisUtterance" in html
    assert "ta-IN" in html
    assert "en-US" in html
