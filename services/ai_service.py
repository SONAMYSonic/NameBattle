"""AI 서비스 - GPT-4o-mini(텍스트, 기본) / Gemini(텍스트, 옵션) + DALL-E 3(이미지)"""

import json
import base64
import io
import os
import time
import logging
import requests as req

import streamlit as st
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

from config.settings import IMAGE_STYLE_PREFIX

load_dotenv()
logger = logging.getLogger(__name__)

BATTLE_STORY_PROMPT = """당신은 이름 배틀 게임의 나레이터입니다.
두 전사의 이름을 기반으로 배틀 스토리를 만들어주세요.

플레이어: {player_name}
상대: {opponent_name} ({opponent_title})

규칙:
1. 각 이름의 의미, 느낌, 어감에서 캐릭터 능력과 무기를 창의적으로 추론하세요.
2. 배틀은 3라운드로 구성하세요. 각 라운드는 2-3문장입니다.
3. 최종 승자는 반드시 "{winner_name}"이어야 합니다.
4. 한국어로 작성하되, 기술명은 한자/영어 혼용 가능합니다.
5. 재미있고 과장된 표현을 사용하세요.

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "player_title": "플레이어의 칭호 (예: 불꽃의 검사)",
    "opponent_title": "상대의 칭호",
    "player_appearance": "플레이어 캐릭터 외형 묘사 (영어, 이미지 생성용)",
    "opponent_appearance": "상대 캐릭터 외형 묘사 (영어, 이미지 생성용)",
    "round1": "1라운드 전투 묘사",
    "round2": "2라운드 전투 묘사",
    "round3": "3라운드 전투 묘사",
    "winner": "승자 이름",
    "victory_line": "승리 선언 대사 (한국어)",
    "battle_summary": "전체 배틀 한 줄 요약"
}}"""


def _get_openai_key() -> str:
    """OpenAI API 키를 secrets 또는 .env에서 가져오기"""
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return os.getenv("OPENAI_API_KEY", "")


def generate_battle_story_gpt(
    player_name: str,
    opponent_name: str,
    opponent_title: str,
    winner_name: str,
) -> dict:
    """GPT-4o-mini로 배틀 스토리 생성 (기본)"""
    openai_key = _get_openai_key()
    if not openai_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

    client = OpenAI(api_key=openai_key)
    prompt = BATTLE_STORY_PROMPT.format(
        player_name=player_name,
        opponent_name=opponent_name,
        opponent_title=opponent_title,
        winner_name=winner_name,
    )

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=1.0,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise


def generate_battle_story_gemini(
    gemini_client,
    player_name: str,
    opponent_name: str,
    opponent_title: str,
    winner_name: str,
) -> dict:
    """Gemini로 배틀 스토리 생성 (옵션)"""
    from google.genai import types
    from config.settings import GEMINI_MODEL_TEXT

    prompt = BATTLE_STORY_PROMPT.format(
        player_name=player_name,
        opponent_name=opponent_name,
        opponent_title=opponent_title,
        winner_name=winner_name,
    )

    for attempt in range(3):
        try:
            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL_TEXT,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=1.0,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise


def generate_battle_story(
    player_name: str,
    opponent_name: str,
    opponent_title: str,
    winner_name: str,
    gemini_client=None,
) -> dict:
    """배틀 스토리 생성 - Gemini client가 있으면 Gemini, 없으면 GPT-4o-mini"""
    if gemini_client:
        return generate_battle_story_gemini(
            gemini_client, player_name, opponent_name, opponent_title, winner_name
        )
    return generate_battle_story_gpt(
        player_name, opponent_name, opponent_title, winner_name
    )


def generate_character_image(
    character_name: str,
    appearance_prompt: str,
) -> str:
    """DALL-E 3로 캐릭터 이미지 생성, base64 문자열 반환"""
    openai_key = _get_openai_key()
    if not openai_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

    openai_client = OpenAI(api_key=openai_key)

    full_prompt = (
        f"{IMAGE_STYLE_PREFIX}"
        f"Character: {character_name}. "
        f"{appearance_prompt}"
    )

    response = openai_client.images.generate(
        model="dall-e-3",
        prompt=full_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url

    img_response = req.get(image_url, timeout=30)
    img_response.raise_for_status()

    img = Image.open(io.BytesIO(img_response.content))
    img = img.resize((512, 512), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
