"""NameBattle - 이름으로 결투하라!"""

import time
import random
import streamlit as st

from ui.styles import inject_global_styles
from ui.components import (
    render_title,
    render_fighter_card,
    render_vs_badge,
    render_user_character_badge,
    render_story_streaming,
    render_opponent_reveal,
    render_battle_history,
)
from ui.animation import render_battle_animation, render_loading_animation
from ui.sounds import play_match_found, play_victory, play_defeat, play_battle_start
from core.battle_engine import execute_battle
from core.opponent_generator import load_predefined_pool, pick_opponent
from config.settings import ANIMATION_MATCHING_STEPS

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NameBattle - 이름 배틀",
    page_icon="\u2694\uFE0F",
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_global_styles()

# ─────────────────────────────────────────────
# 세션 초기화
# ─────────────────────────────────────────────
if "phase" not in st.session_state:
    st.session_state.phase = "home"
if "history" not in st.session_state:
    st.session_state.history = []
if "saved_characters" not in st.session_state:
    st.session_state.saved_characters = []
if "tts_enabled" not in st.session_state:
    st.session_state.tts_enabled = True
if "_nav_counter" not in st.session_state:
    st.session_state._nav_counter = 0


def scroll_to_top():
    """페이지 상단으로 스크롤 (타이밍 보장)"""
    st.html(
        "<script>setTimeout(function(){"
        "try{var m=window.parent.document.querySelector('section.main');"
        "if(m)m.scrollTo({top:0,behavior:'instant'});}catch(e)"
        "{window.parent.scrollTo(0,0);}},50);</script>"
    )


# ─────────────────────────────────────────────
# API 키 확인
# ─────────────────────────────────────────────
def get_gemini_client():
    """Gemini 클라이언트 가져오기 (선택 사항)"""
    api_key = st.session_state.get("gemini_api_key", "")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None


# ─────────────────────────────────────────────
# 사이드바: API 키 입력 + 전적
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Settings")

    st.session_state.tts_enabled = st.toggle(
        "TTS 나레이션",
        value=st.session_state.tts_enabled,
        help="배틀 스토리를 음성으로 읽어줍니다. (Typecast API 토큰 소모)",
    )

    st.markdown("---")
    st.markdown("### 텍스트 모델")
    st.caption("기본: GPT-4o-mini (API 키 내장)")

    api_key = st.text_input(
        "Gemini API Key (선택)",
        type="password",
        key="gemini_api_key",
        help="입력하면 Gemini로 스토리 생성. 비워두면 GPT-4o-mini 사용.",
    )
    if api_key:
        st.success("Gemini 모드로 전환됩니다.")
    else:
        st.info("GPT-4o-mini 모드 (기본)")

    if st.session_state.history:
        st.markdown("---")
        st.markdown("### 최근 전적")
        wins = sum(1 for h in st.session_state.history if h["result"] == "player")
        total = len(st.session_state.history)
        st.markdown(f"**{wins}승 {total - wins}패**")
        for record in reversed(st.session_state.history[-5:]):
            result_emoji = "\U0001F3C6" if record["result"] == "player" else "\U0001F4A2"
            st.markdown(
                f"{result_emoji} **{record['player']}** vs {record['opponent']}"
            )

    if st.session_state.saved_characters:
        st.markdown("---")
        st.markdown(f"### 등록된 캐릭터: {len(st.session_state.saved_characters)}명")


# ═════════════════════════════════════════════
# 페이지 라우팅
# ═════════════════════════════════════════════

# ─────────────────────────────────────────────
# HOME: 이름 입력
# ─────────────────────────────────────────────
if st.session_state.phase == "home":
    scroll_to_top()
    render_title()

    st.markdown("")
    user_name = st.text_input(
        "당신의 이름을 입력하세요",
        max_chars=20,
        placeholder="이름을 입력하면 배틀이 시작됩니다",
        key="user_name_input",
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        start_btn = st.button(
            "\u2694\uFE0F 결투 시작!",
            type="primary",
            use_container_width=True,
            disabled=not user_name,
        )

    if start_btn:
        if not user_name.strip():
            st.warning("이름을 입력해주세요!")
        else:
            st.session_state.user_name = user_name.strip()
            st.session_state.phase = "matching"
            st.rerun()

    # 전적 표시 (홈에서도)
    if st.session_state.history:
        with st.expander("\U0001F4CA 전적 보기"):
            render_battle_history(st.session_state.history)

# ─────────────────────────────────────────────
# MATCHING: 상대 매칭 슬롯머신 + 실제 상대 표시
# ─────────────────────────────────────────────
elif st.session_state.phase == "matching":
    # 이미 매칭된 상대가 있으면 스킵 (이중 클릭 방지)
    if st.session_state.get("matched_opponent"):
        st.session_state.phase = "confirm"
        st.rerun()

    scroll_to_top()
    st.markdown("## \u2694\uFE0F VS 매칭 중...")

    characters, _ = load_predefined_pool()
    name_pool = [c["name"] for c in characters] if characters else ["???"]

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.html(
            f"<div style='text-align:center;'>"
            f"<div class='fighter-name'>{st.session_state.user_name}</div>"
            f"</div>"
        )
    with col2:
        render_vs_badge()
    with col3:
        name_slot = st.empty()

    # 슬롯머신 효과
    for i in range(ANIMATION_MATCHING_STEPS):
        name_slot.markdown(
            f"<div style='text-align:center;'>"
            f"<div class='fighter-name'>{random.choice(name_pool)}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        time.sleep(0.08 + i * 0.015)

    # 실제 상대 매칭
    opponent = pick_opponent(
        st.session_state.user_name,
        st.session_state.saved_characters,
    )
    st.session_state.matched_opponent = opponent

    # 최종 상대 이름 표시 (빨간색으로 강조)
    play_match_found()
    name_slot.markdown(
        f"<div style='text-align:center;'>"
        f"<div class='fighter-name' style='color:#FF4B4B;'>{opponent.name}</div>"
        f"<div class='fighter-title'>{opponent.title}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    time.sleep(1.5)

    st.session_state.phase = "confirm"
    st.rerun()

# ─────────────────────────────────────────────
# CONFIRM: 상대 확인 + 대결 시작
# ─────────────────────────────────────────────
elif st.session_state.phase == "confirm":
    scroll_to_top()
    opponent = st.session_state.get("matched_opponent")
    if not opponent:
        st.session_state.phase = "home"
        st.rerun()

    render_title()

    # 사용자 캐릭터 재등장 알림
    if opponent.source == "user_character" and opponent.creator_name:
        render_user_character_badge(opponent.creator_name)

    # 매칭 결과 표시
    render_opponent_reveal(
        player_name=st.session_state.user_name,
        opponent_name=opponent.name,
        opponent_title=opponent.title,
        source=opponent.source,
    )

    if opponent.description:
        st.markdown(f"> *{opponent.description}*")

    st.markdown("")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("\u2694\uFE0F 대결하기!", type="primary", use_container_width=True):
            play_battle_start()
            st.session_state.phase = "prepare"
            st.rerun()

    with col2:
        nav = st.session_state._nav_counter
        if st.button("다른 상대 찾기", key=f"confirm_rematch_{nav}", use_container_width=True):
            st.session_state._nav_counter = nav + 1
            st.session_state.pop("matched_opponent", None)
            st.session_state.phase = "matching"
            st.rerun()

# ─────────────────────────────────────────────
# PREPARE: AI 생성 (로딩)
# ─────────────────────────────────────────────
elif st.session_state.phase == "prepare":
    opponent = st.session_state.get("matched_opponent")
    if not opponent:
        st.session_state.phase = "home"
        st.rerun()

    gemini_client = get_gemini_client()

    # 탑블레이드 스타일 로딩 애니메이션
    render_loading_animation(st.session_state.user_name, opponent.name)

    progress = st.progress(0, text="준비 중...")

    def on_progress(step: int, msg: str):
        pct = int(step / 6 * 100)
        progress.progress(pct, text=msg)

    try:
        result = execute_battle(
            player_name=st.session_state.user_name,
            opponent=opponent,
            progress_callback=on_progress,
            tts_enabled=st.session_state.tts_enabled,
            gemini_client=gemini_client,
        )
        st.session_state.battle_result = result
        progress.progress(100, text="모든 준비 완료!")

    except Exception as e:
        st.error(f"배틀 준비 중 오류가 발생했습니다: {e}")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("다시 시도"):
                st.rerun()
        with col_b:
            if st.button("홈으로"):
                st.session_state.phase = "home"
                st.rerun()
        st.stop()

    time.sleep(1)
    st.session_state.phase = "battle"
    st.rerun()

# ─────────────────────────────────────────────
# BATTLE: 애니메이션
# ─────────────────────────────────────────────
elif st.session_state.phase == "battle":
    result = st.session_state.get("battle_result")
    if not result:
        st.session_state.phase = "home"
        st.rerun()

    # 사용자 캐릭터 재등장 알림
    if result.opponent.source == "user_character" and result.opponent.creator_name:
        render_user_character_badge(result.opponent.creator_name)

    # 배틀 애니메이션
    render_battle_animation(
        player_name=result.player.name,
        opponent_name=result.opponent.name,
        player_img_b64=result.player.image_base64,
        opponent_img_b64=result.opponent.image_base64,
    )

    # 애니메이션 시간 대기 후 결과로 전환
    time.sleep(5.5)
    st.session_state.phase = "result"
    st.rerun()

# ─────────────────────────────────────────────
# RESULT: 결과 표시
# ─────────────────────────────────────────────
elif st.session_state.phase == "result":
    result = st.session_state.get("battle_result")
    if not result:
        st.session_state.phase = "home"
        st.rerun()

    is_player_win = result.winner == "player"

    # 승패 헤더 (효과음/연출은 최초 1회만)
    if is_player_win:
        st.html('<div class="winner-text">\u2728 VICTORY! \u2728</div>')
        if not st.session_state.get("result_effect_played"):
            play_victory()
            st.balloons()
    else:
        st.html('<div class="loser-text">DEFEAT...</div>')
        if not st.session_state.get("result_effect_played"):
            play_defeat()
            st.snow()

    if not st.session_state.get("result_effect_played"):
        st.session_state.result_effect_played = True

    st.markdown("---")

    # 캐릭터 비교
    col1, col_mid, col2 = st.columns([3, 1, 3])
    with col1:
        render_fighter_card(
            result.player.name,
            result.player.title,
            result.player.image_base64,
            is_winner=is_player_win,
        )
    with col_mid:
        render_vs_badge()
    with col2:
        render_fighter_card(
            result.opponent.name,
            result.opponent.title,
            result.opponent.image_base64,
            is_winner=not is_player_win,
        )

    st.markdown("---")

    # 승리 선언
    if result.victory_line:
        winner_name = result.player.name if is_player_win else result.opponent.name
        st.markdown(f'> **{winner_name}**: *"{result.victory_line}"*')
        st.markdown("")

    # TTS 오디오 재생
    if result.audio_data:
        st.audio(result.audio_data, format="audio/wav", autoplay=True)

    # 배틀 스토리 (최초 1회만 스트리밍, 이후 즉시 표시)
    st.markdown("### \U0001F4DC 배틀 스토리")
    if not st.session_state.get("story_streamed"):
        render_story_streaming(result.story)
        st.session_state.story_streamed = True
    else:
        st.markdown(result.story)

    if result.battle_summary:
        st.markdown("")
        st.info(f"\U0001F4DD **요약**: {result.battle_summary}")

    st.markdown("---")

    # 전적 저장 (중복 방지)
    if "result_saved" not in st.session_state:
        st.session_state.history.append({
            "player": result.player.name,
            "opponent": result.opponent.name,
            "result": result.winner,
            "opponent_source": result.opponent.source,
            "player_title": result.player.title,
            "opponent_title": result.opponent.title,
        })

        # 승리 캐릭터를 saved_characters에 저장 (재등장용)
        if is_player_win and result.player.image_base64:
            st.session_state.saved_characters.append({
                "name": result.player.name,
                "title": result.player.title,
                "description": f"{result.player.title} - {result.battle_summary}",
                "image_base64": result.player.image_base64,
                "creator_name": result.player.name,
                "stats": result.player.stats,
            })
            st.success(
                f"\U0001F4BE **{result.player.name}** 캐릭터가 등록되었습니다! "
                "다른 플레이어의 상대로 등장할 수 있습니다."
            )

        st.session_state.result_saved = True

    # 버튼 (nav_counter로 이중 클릭 방지)
    nav = st.session_state._nav_counter
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("\u2694\uFE0F 다른 상대 찾기", key=f"result_rematch_{nav}", type="primary", use_container_width=True):
            st.session_state._nav_counter = nav + 1
            for key in ["battle_result", "result_saved", "matched_opponent", "show_history", "story_streamed", "result_effect_played"]:
                st.session_state.pop(key, None)
            st.session_state.phase = "matching"
            st.rerun()
    with col_b:
        if st.button("\U0001F464 다른 캐릭터로 배틀하기!", key=f"result_newchar_{nav}", use_container_width=True):
            st.session_state._nav_counter = nav + 1
            for key in ["battle_result", "result_saved", "matched_opponent", "show_history", "story_streamed", "result_effect_played"]:
                st.session_state.pop(key, None)
            st.session_state.phase = "home"
            st.rerun()
    with col_c:
        if st.button("\U0001F4CA 전적 보기", use_container_width=True):
            st.session_state.show_history = not st.session_state.get("show_history", False)
            st.rerun()

    # 전적 상세
    if st.session_state.get("show_history"):
        st.markdown("---")
        st.markdown("### \U0001F4CA 전체 전적")
        render_battle_history(st.session_state.history)
