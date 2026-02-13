"""상대 생성 모듈 - 하이브리드 매칭 시스템"""

import json
import random
from pathlib import Path

from config.settings import (
    MATCHING_EARLY_PREDEFINED,
    MATCHING_EARLY_RANDOM,
    MATCHING_EARLY_USER,
    MATCHING_GROWTH_PREDEFINED,
    MATCHING_GROWTH_RANDOM,
    MATCHING_GROWTH_USER,
    MATCHING_MATURE_PREDEFINED,
    MATCHING_MATURE_RANDOM,
    MATCHING_MATURE_USER,
    MATCHING_GROWTH_THRESHOLD,
    MATCHING_MATURE_THRESHOLD,
)
from core.models import Fighter


# 랜덤 이름 생성 풀
PREFIXES = [
    "불꽃의", "그림자", "천둥", "얼음", "황금", "암흑", "폭풍",
    "강철", "비밀의", "고대", "심연의", "하늘", "대지의", "은빛",
    "성스러운", "저주받은", "잊혀진", "영원한",
]

CORES = [
    "검사", "마법사", "궁수", "기사", "암살자", "연금술사",
    "드루이드", "무도가", "현자", "사냥꾼", "해적", "닌자",
    "수호자", "파괴자", "방랑자", "예언자",
]

SUFFIXES = [
    "레이든", "아르카스", "셀레나", "모르간", "카이론", "에반",
    "리안", "타리스", "노바", "제로스", "루미아", "칸드라",
    "아이리스", "벨리온", "크로노스", "테라",
]


def load_predefined_pool() -> tuple[list[dict], dict]:
    """사전 정의 상대 풀 로드"""
    try:
        data_path = Path(__file__).parent.parent / "data" / "predefined_opponents.json"
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["characters"], data["rarities"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return [], {}


def generate_random_name() -> dict:
    """규칙 기반 랜덤 이름 생성"""
    templates = [
        "{prefix} {suffix}",
        "{core} {suffix}",
        "{prefix} {core}",
    ]
    prefix = random.choice(PREFIXES)
    core = random.choice(CORES)
    suffix = random.choice(SUFFIXES)

    name = random.choice(templates).format(prefix=prefix, core=core, suffix=suffix)
    title = random.choice([
        f"떠도는 {core}",
        f"{prefix} 수호자",
        f"전설의 {core}",
        f"미지의 도전자",
        f"{prefix} 전사",
    ])

    # 밸런스 스탯 생성
    stat_names = ["attack", "defense", "speed", "luck", "charisma"]
    raw = [random.randint(50, 95) for _ in stat_names]
    total = sum(raw)
    budget = 380
    stats = {name: int(v * budget / total) for name, v in zip(stat_names, raw)}

    return {
        "name": name,
        "title": title,
        "stats": stats,
        "appearance_prompt": "",
    }


def pick_opponent(
    player_name: str,
    user_characters: list[dict] | None = None,
) -> Fighter:
    """하이브리드 매칭으로 상대 선택"""

    user_chars = user_characters or []
    user_count = len(user_chars)

    # 동적 확률 계산
    if user_count < MATCHING_GROWTH_THRESHOLD:
        p_pre, p_rand, p_user = (
            MATCHING_EARLY_PREDEFINED,
            MATCHING_EARLY_RANDOM,
            MATCHING_EARLY_USER,
        )
    elif user_count < MATCHING_MATURE_THRESHOLD:
        p_pre, p_rand, p_user = (
            MATCHING_GROWTH_PREDEFINED,
            MATCHING_GROWTH_RANDOM,
            MATCHING_GROWTH_USER,
        )
    else:
        p_pre, p_rand, p_user = (
            MATCHING_MATURE_PREDEFINED,
            MATCHING_MATURE_RANDOM,
            MATCHING_MATURE_USER,
        )

    roll = random.random()

    # 사용자 캐릭터 재등장
    if roll < p_user and user_chars:
        candidates = [c for c in user_chars if c.get("name") != player_name]
        if candidates:
            chosen = random.choice(candidates)
            return Fighter(
                name=chosen["name"],
                title=chosen.get("title", ""),
                description=chosen.get("description", ""),
                image_base64=chosen.get("image_base64", ""),
                stats=chosen.get("stats", {}),
                source="user_character",
                creator_name=chosen.get("creator_name"),
            )

    # 사전 정의 상대
    if roll < p_user + p_pre:
        characters, rarities = load_predefined_pool()
        if characters:
            weights = [rarities.get(c.get("rarity", "common"), {}).get("weight", 0.4)
                       for c in characters]
            chosen = random.choices(characters, weights=weights, k=1)[0]
            return Fighter(
                name=chosen["name"],
                title=chosen["title"],
                description=chosen["description"],
                stats=chosen["stats"],
                source="predefined",
                appearance_prompt=chosen.get("appearance_prompt", ""),
                image_url=chosen.get("image_url", ""),
                image_file=chosen.get("image_file", ""),
            )

    # 랜덤 생성
    data = generate_random_name()
    return Fighter(
        name=data["name"],
        title=data["title"],
        stats=data["stats"],
        source="random",
    )
