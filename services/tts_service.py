"""TTS 서비스 - Typecast API"""

import logging
import os
import re

import streamlit as st
from typecast import Typecast
from typecast.models import TTSRequest
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

TYPECAST_VOICE_ID = "tc_66f4ecd1e386a91199bb0bf1"
TYPECAST_MODEL = "ssfm-v21"


def clean_story_for_tts(story: str) -> str:
    """마크다운 서식 제거 -> 자연스러운 읽기 텍스트"""
    text = story.replace("**[ 라운드 1 ]**", "라운드 1.")
    text = text.replace("**[ 라운드 2 ]**", "라운드 2.")
    text = text.replace("**[ 라운드 3 ]**", "라운드 3.")
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    return text.strip()


def generate_tts_audio(
    story: str,
    victory_line: str = "",
    winner_name: str = "",
) -> bytes | None:
    """배틀 스토리 -> WAV 오디오 바이트 반환"""
    try:
        api_key = st.secrets["TYPECAST_API_KEY"]
    except Exception:
        api_key = os.getenv("TYPECAST_API_KEY", "")
    if not api_key:
        logger.warning("TYPECAST_API_KEY가 설정되지 않았습니다.")
        return None

    tts_text = clean_story_for_tts(story)
    if victory_line and winner_name:
        tts_text += f"\n\n{winner_name}이 외친다. {victory_line}"

    client = Typecast(api_key=api_key)
    response = client.text_to_speech(TTSRequest(
        text=tts_text,
        model=TYPECAST_MODEL,
        voice_id=TYPECAST_VOICE_ID,
    ))
    return response.audio_data
