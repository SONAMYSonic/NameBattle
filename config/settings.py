"""NameBattle 전역 설정"""


# Gemini API 설정 (텍스트 생성)
GEMINI_MODEL_TEXT = "gemini-2.5-flash"

# 이미지 생성 스타일 프리픽스
IMAGE_STYLE_PREFIX = (
    "Anime-style character portrait, vibrant colors, "
    "dynamic action pose, fantasy RPG aesthetic, "
    "clean line art, detailed shading, "
    "solid dark background, upper body shot, "
    "high quality digital illustration. "
)

# 매칭 확률 설정
MATCHING_EARLY_PREDEFINED = 0.60
MATCHING_EARLY_RANDOM = 0.40
MATCHING_EARLY_USER = 0.00

MATCHING_GROWTH_PREDEFINED = 0.45
MATCHING_GROWTH_RANDOM = 0.40
MATCHING_GROWTH_USER = 0.15

MATCHING_MATURE_PREDEFINED = 0.30
MATCHING_MATURE_RANDOM = 0.35
MATCHING_MATURE_USER = 0.35

MATCHING_GROWTH_THRESHOLD = 10
MATCHING_MATURE_THRESHOLD = 50

# 플레이어 승률 (약간 유리하게)
PLAYER_WIN_RATE = 0.55

# 애니메이션 타이밍 (초)
ANIMATION_BATTLE_DURATION = 5.5
ANIMATION_MATCHING_STEPS = 20
