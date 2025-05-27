from dataclasses import dataclass, field
from typing import List

@dataclass
class ScorerRecord:
    team: str
    scorer: str
    minute: str
    own_goal: bool
    penalty: bool

@dataclass
class MatchRecord:
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    date: str = ""
    tournament: str = ""
    city: str = ""
    country: str = ""
    neutral: bool = False
    scorers: List[ScorerRecord] = field(default_factory=list)
