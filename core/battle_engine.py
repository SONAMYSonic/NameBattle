"""배틀 엔진 - 전체 배틀 흐름 오케스트레이션"""

import base64
import hashlib
import io
import logging
import os
import random

import requests as req
from PIL import Image

from config.settings import PLAYER_WIN_RATE
from core.models import Fighter, BattleResult, BattleRound
from services.ai_service import generate_battle_story, generate_character_image
from services.tts_service import generate_tts_audio

_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
IMAGE_CACHE_DIR = os.path.join(_PROJECT_ROOT, "assets", "images", "generated")
CHARACTER_IMG_DIR = os.path.join(_PROJECT_ROOT, "assets", "images", "characters")

logger = logging.getLogger(__name__)


def _cache_key(name: str) -> str:
    """캐릭터 이름으로 캐시 파일 경로 반환"""
    h = hashlib.md5(name.strip().lower().encode()).hexdigest()[:12]
    safe = "".join(c if c.isalnum() else "_" for c in name.strip())
    return os.path.join(IMAGE_CACHE_DIR, f"{safe}_{h}.b64")


def load_cached_image(name: str) -> str | None:
    """캐시된 이미지 base64 로드. 없으면 None"""
    path = _cache_key(name)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read().strip()
            if data:
                logger.info("캐시 이미지 사용: %s", name)
                return data
        except Exception:
            pass
    return None


def save_cached_image(name: str, b64: str) -> None:
    """이미지 base64를 캐시에 저장"""
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
    path = _cache_key(name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(b64)
        logger.info("이미지 캐시 저장: %s", name)
    except Exception as e:
        logger.warning("이미지 캐시 저장 실패: %s", e)


def load_local_image_as_base64(filename: str) -> str:
    """로컬 캐릭터 이미지 파일을 512x512 base64로 반환"""
    path = os.path.join(CHARACTER_IMG_DIR, filename)
    if not os.path.exists(path):
        return ""
    img = Image.open(path)
    img = img.resize((512, 512), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def download_image_as_base64(url: str) -> str:
    """URL에서 이미지를 다운로드하여 512x512 base64 문자열로 반환"""
    resp = req.get(url, timeout=30)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content))
    img = img.resize((512, 512), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def determine_winner(player_name: str, opponent_name: str) -> str:
    """승패 사전 결정 (플레이어 승률 55%)"""
    if random.random() < PLAYER_WIN_RATE:
        return player_name
    return opponent_name


def execute_battle(
    player_name: str,
    opponent: Fighter,
    progress_callback=None,
    tts_enabled: bool = True,
    gemini_client=None,
) -> BattleResult:
    """
    배틀 전체 실행.

    Args:
        player_name: 플레이어 이름
        opponent: 매칭된 상대 Fighter
        progress_callback: 진행 상태 콜백 (단계, 메시지)
        tts_enabled: TTS 활성화 여부
        gemini_client: Gemini 클라이언트 (None이면 GPT-4o-mini 사용)

    Returns:
        BattleResult
    """

    def _progress(step: int, msg: str):
        if progress_callback:
            progress_callback(step, msg)

    # 1단계: 승패 사전 결정
    _progress(1, "승패의 운명을 결정하고 있습니다...")
    winner_name = determine_winner(player_name, opponent.name)

    # 2단계: 배틀 스토리 생성
    _progress(2, "배틀 스토리를 생성하고 있습니다...")
    story_data = generate_battle_story(
        player_name=player_name,
        opponent_name=opponent.name,
        opponent_title=opponent.title,
        winner_name=winner_name,
        gemini_client=gemini_client,
    )

    # 플레이어 Fighter 생성
    player = Fighter(
        name=player_name,
        title=story_data.get("player_title", "도전자"),
        source="player",
    )

    # 상대 제목 업데이트 (비어있는 경우)
    if not opponent.title:
        opponent.title = story_data.get("opponent_title", "미지의 전사")

    # 3단계: 플레이어 이미지 생성 (캐시 확인)
    cached = load_cached_image(player_name)
    if cached:
        _progress(3, f"{player_name}의 캐릭터 이미지를 불러오고 있습니다...")
        player.image_base64 = cached
    else:
        _progress(3, f"{player_name}의 캐릭터 이미지를 생성하고 있습니다...")
        try:
            player.image_base64 = generate_character_image(
                character_name=player_name,
                appearance_prompt=story_data.get("player_appearance", "fantasy warrior"),
            )
            if player.image_base64:
                save_cached_image(player_name, player.image_base64)
        except Exception as e:
            logger.warning("플레이어 이미지 생성 실패: %s", e)
            player.image_base64 = ""

    # 4단계: 상대 이미지 (로컬파일 > image_url > user_character > 캐시 > DALL-E)
    _loaded_local = False
    if opponent.image_file:
        _progress(4, f"{opponent.name}의 캐릭터 이미지를 불러오고 있습니다...")
        try:
            img_data = load_local_image_as_base64(opponent.image_file)
            if img_data:
                opponent.image_base64 = img_data
                _loaded_local = True
            else:
                logger.warning("로컬 이미지 파일 없음: %s", opponent.image_file)
        except Exception as e:
            logger.warning("로컬 이미지 로드 실패: %s", e)

    if not _loaded_local and opponent.image_url:
        _progress(4, f"{opponent.name}의 캐릭터 이미지를 불러오고 있습니다...")
        opp_cached = load_cached_image(opponent.name)
        if opp_cached:
            opponent.image_base64 = opp_cached
        else:
            try:
                opponent.image_base64 = download_image_as_base64(opponent.image_url)
                if opponent.image_base64:
                    save_cached_image(opponent.name, opponent.image_base64)
            except Exception as e:
                logger.warning("상대 이미지 URL 다운로드 실패: %s", e)
                opponent.image_base64 = ""
    elif opponent.source == "user_character" and opponent.image_base64:
        _progress(4, "상대 캐릭터 이미지를 불러오고 있습니다...")
    else:
        opp_cached = load_cached_image(opponent.name)
        if opp_cached:
            _progress(4, f"{opponent.name}의 캐릭터 이미지를 불러오고 있습니다...")
            opponent.image_base64 = opp_cached
        else:
            _progress(4, f"{opponent.name}의 캐릭터 이미지를 생성하고 있습니다...")
            opp_appearance = (
                opponent.appearance_prompt
                or story_data.get("opponent_appearance", "fantasy warrior")
            )
            try:
                opponent.image_base64 = generate_character_image(
                    character_name=opponent.name,
                    appearance_prompt=opp_appearance,
                )
                if opponent.image_base64:
                    save_cached_image(opponent.name, opponent.image_base64)
            except Exception as e:
                logger.warning("상대 이미지 생성 실패: %s", e)
                opponent.image_base64 = ""

    # 5단계: 스토리 조립 + TTS 생성
    rounds = [
        BattleRound(1, story_data.get("round1", ""), ""),
        BattleRound(2, story_data.get("round2", ""), ""),
        BattleRound(3, story_data.get("round3", ""), ""),
    ]

    full_story = (
        f"**[ 라운드 1 ]**\n{story_data.get('round1', '')}\n\n"
        f"**[ 라운드 2 ]**\n{story_data.get('round2', '')}\n\n"
        f"**[ 라운드 3 ]**\n{story_data.get('round3', '')}"
    )

    victory_line = story_data.get("victory_line", "")
    winner = "player" if winner_name == player_name else "opponent"
    winner_display = player_name if winner == "player" else opponent.name

    audio_data = b""
    if tts_enabled:
        _progress(5, "배틀 나레이션을 생성하고 있습니다...")
        try:
            audio_data = generate_tts_audio(full_story, victory_line, winner_display) or b""
        except Exception as e:
            logger.warning("TTS 생성 실패: %s", e)

    # 6단계: 결과 조립
    _progress(6, "배틀 결과를 정리하고 있습니다...")

    return BattleResult(
        player=player,
        opponent=opponent,
        winner=winner,
        rounds=rounds,
        victory_line=victory_line,
        battle_summary=story_data.get("battle_summary", ""),
        story=full_story,
        audio_data=audio_data,
    )
