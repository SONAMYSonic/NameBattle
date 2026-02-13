"""재사용 가능한 UI 컴포넌트"""

import base64
import time
import streamlit as st
import streamlit.components.v1 as components


# 내장 SVG 플레이스홀더 (외부 서버 의존 없음)
_PLACEHOLDER_SVG = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='512' height='512'%3E"
    "%3Crect width='512' height='512' fill='%23262730'/%3E"
    "%3Ctext x='50%25' y='45%25' font-size='120' text-anchor='middle' "
    "dy='.3em' fill='%23555'%3E%3F%3C/text%3E"
    "%3Ctext x='50%25' y='70%25' font-size='24' text-anchor='middle' "
    "fill='%23666'%3EGenerating...%3C/text%3E"
    "%3C/svg%3E"
)


def render_title():
    """메인 타이틀 렌더링"""
    st.html("""
    <div class="title-container">
        <div class="title-text">NAME BATTLE</div>
        <div class="subtitle-text">이름으로 결투하라!</div>
    </div>
    """)


def render_fighter_card(name: str, title: str, image_b64: str, is_winner: bool | None = None):
    """전투사 카드 렌더링"""
    if image_b64:
        st.image(
            base64.b64decode(image_b64),
            use_container_width=True,
        )
    else:
        # 내장 SVG 플레이스홀더
        components.html(
            f'<div style="text-align:center;">'
            f'<img src="{_PLACEHOLDER_SVG}" '
            f'style="width:100%;border-radius:12px;"/>'
            f'</div>',
            height=300,
        )

    st.html(f"""
    <div style="text-align:center;">
        <div class="fighter-name">{name}</div>
        <div class="fighter-title">{title}</div>
    </div>
    """)

    if is_winner is True:
        st.success("WINNER!", icon="\U0001F3C6")
    elif is_winner is False:
        st.error("DEFEAT", icon="\U0001F4A2")


def render_vs_badge():
    """VS 배지"""
    st.html('<div style="text-align:center;padding:20px 0;"><span class="vs-badge">VS</span></div>')


def render_user_character_badge(creator_name: str):
    """사용자 캐릭터 재등장 배지"""
    st.html(f"""
    <div class="user-char-badge">
        <div style="font-size:14px;">&#x26A1; 다른 플레이어의 캐릭터가 도전장을 내밀었습니다!</div>
        <div style="font-size:12px;opacity:0.8;margin-top:4px;">
            이 캐릭터는 <b>{creator_name}</b> 님이 만든 캐릭터입니다.
        </div>
    </div>
    """)


def render_story_streaming(story: str):
    """배틀 스토리를 스트리밍 효과로 표시"""
    if not story:
        st.markdown("*스토리를 불러올 수 없습니다.*")
        return

    placeholder = st.empty()
    displayed = ""
    for char in story:
        displayed += char
        placeholder.markdown(displayed)
        time.sleep(0.015)


def render_opponent_reveal(player_name: str, opponent_name: str, opponent_title: str, source: str):
    """매칭 결과 표시 화면"""
    st.html(f"""
    <div style="text-align:center; padding:20px 0;">
        <div style="font-size:1.2rem; color:#888; margin-bottom:16px;">상대가 결정되었습니다!</div>
        <div style="display:flex; align-items:center; justify-content:center; gap:24px;">
            <div>
                <div class="fighter-name">{player_name}</div>
            </div>
            <div class="vs-badge" style="font-size:2rem;">VS</div>
            <div>
                <div class="fighter-name" style="color:#FF4B4B;">{opponent_name}</div>
                <div class="fighter-title">{opponent_title}</div>
            </div>
        </div>
    </div>
    """)

    # 상대 소스에 따른 태그
    if source == "predefined":
        st.html('<div style="text-align:center;"><span style="background:#ff9800;color:#000;padding:2px 10px;border-radius:8px;font-size:0.8rem;">BOSS</span></div>')
    elif source == "user_character":
        st.html('<div style="text-align:center;"><span style="background:#667eea;color:#fff;padding:2px 10px;border-radius:8px;font-size:0.8rem;">PLAYER</span></div>')
    elif source == "random":
        st.html('<div style="text-align:center;"><span style="background:#444;color:#fff;padding:2px 10px;border-radius:8px;font-size:0.8rem;">RANDOM</span></div>')


def render_battle_history(history: list):
    """전적 기록 상세 표시"""
    if not history:
        st.info("아직 전적이 없습니다. 첫 배틀을 시작해보세요!")
        return

    wins = sum(1 for h in history if h["result"] == "player")
    losses = len(history) - wins
    win_rate = wins / len(history) * 100

    # 전체 통계
    col1, col2, col3 = st.columns(3)
    col1.metric("승리", f"{wins}회")
    col2.metric("패배", f"{losses}회")
    col3.metric("승률", f"{win_rate:.0f}%")

    st.markdown("---")

    # 전적 목록
    for i, record in enumerate(reversed(history), 1):
        is_win = record["result"] == "player"
        emoji = "\U0001F3C6" if is_win else "\U0001F4A2"
        result_text = "승리" if is_win else "패배"
        source_tag = ""
        if record.get("opponent_source") == "predefined":
            source_tag = " `BOSS`"
        elif record.get("opponent_source") == "user_character":
            source_tag = " `PLAYER`"

        st.markdown(
            f"{i}. {emoji} **{record['player']}** vs **{record['opponent']}**{source_tag} "
            f"- {result_text}"
        )
