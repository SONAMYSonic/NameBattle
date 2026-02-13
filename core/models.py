"""NameBattle 데이터 모델"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Fighter:
    name: str
    title: str = ""
    description: str = ""
    image_base64: str = ""
    image_url: str = ""  # 외부 이미지 URL (있으면 DALL-E 생성 건너뜀)
    image_file: str = ""  # 로컬 이미지 파일명 (assets/images/characters/ 내)
    stats: dict = field(default_factory=dict)
    source: str = "random"  # "predefined", "random", "user_character"
    creator_name: Optional[str] = None
    appearance_prompt: str = ""


@dataclass
class BattleRound:
    round_number: int
    description: str
    round_winner: str


@dataclass
class BattleResult:
    player: Fighter
    opponent: Fighter
    winner: str  # "player" or "opponent"
    rounds: list = field(default_factory=list)
    victory_line: str = ""
    battle_summary: str = ""
    story: str = ""
    audio_data: bytes = b""
