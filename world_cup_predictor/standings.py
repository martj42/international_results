"""2026 FIFA World Cup group standings and qualification logic.

Data as of June 22, 2026 (after Round 2). Standings are hardcoded to avoid
dependencies on live APIs. Qualification logic determines what results teams
need to advance, considering dependencies on other group matches.
"""

from __future__ import annotations

from typing import NamedTuple


class TeamStanding(NamedTuple):
    """A team's current standing in their group."""
    team: str
    played: int
    wins: int
    draws: int
    losses: int
    gf: int
    ga: int
    points: int

    @property
    def gd(self) -> int:
        return self.gf - self.ga


# Group standings as of June 22, 2026 (after 2 rounds of 3).
# Format: group_letter -> list of TeamStanding(sorted by points desc, then GD)
GROUP_STANDINGS = {
    "A": [
        TeamStanding("Mexico", 2, 1, 1, 0, 2, 1, 4),
        TeamStanding("South Africa", 2, 1, 0, 1, 1, 1, 3),
        TeamStanding("South Korea", 2, 1, 0, 1, 1, 2, 3),
        TeamStanding("Czech Republic", 2, 0, 1, 1, 1, 1, 1),
    ],
    "B": [
        TeamStanding("Canada", 2, 2, 0, 0, 7, 1, 6),
        TeamStanding("Switzerland", 2, 1, 1, 0, 5, 2, 4),
        TeamStanding("Bosnia and Herzegovina", 2, 0, 1, 1, 2, 5, 1),
        TeamStanding("Qatar", 2, 0, 0, 2, 1, 7, 0),
    ],
    "C": [
        TeamStanding("Brazil", 2, 2, 0, 0, 4, 1, 6),
        TeamStanding("Morocco", 2, 1, 0, 1, 1, 1, 3),
        TeamStanding("Scotland", 2, 0, 0, 2, 1, 4, 0),
        TeamStanding("Haiti", 2, 0, 0, 2, 0, 0, 0),
    ],
    "D": [
        TeamStanding("United States", 2, 2, 0, 0, 6, 1, 6),
        TeamStanding("Australia", 2, 1, 0, 1, 2, 4, 3),
        TeamStanding("Paraguay", 2, 1, 0, 1, 2, 6, 3),
        TeamStanding("Turkey", 2, 0, 0, 2, 0, 4, 0),
    ],
    "E": [
        TeamStanding("Germany", 2, 2, 0, 0, 9, 1, 6),
        TeamStanding("Ivory Coast", 2, 1, 0, 1, 2, 9, 3),
        TeamStanding("Ecuador", 2, 0, 1, 1, 0, 1, 1),
        TeamStanding("Curaçao", 2, 0, 1, 1, 1, 1, 1),
    ],
    "F": [
        TeamStanding("Netherlands", 2, 2, 0, 0, 7, 3, 6),
        TeamStanding("Japan", 2, 1, 1, 0, 6, 3, 4),
        TeamStanding("Sweden", 2, 1, 0, 1, 6, 6, 3),
        TeamStanding("Tunisia", 2, 0, 0, 2, 0, 7, 0),
    ],
    "G": [
        TeamStanding("Spain", 2, 2, 0, 0, 4, 0, 6),
        TeamStanding("Saudi Arabia", 2, 0, 1, 1, 0, 4, 1),
        TeamStanding("Uruguay", 2, 0, 1, 1, 2, 2, 1),
        TeamStanding("Cape Verde", 2, 0, 0, 2, 0, 0, 0),
    ],
    "H": [
        TeamStanding("France", 2, 2, 0, 0, 3, 0, 6),
        TeamStanding("Iraq", 2, 1, 0, 1, 0, 3, 3),
        TeamStanding("Senegal", 2, 1, 0, 1, 3, 2, 3),
        TeamStanding("Norway", 2, 0, 0, 2, 2, 3, 0),
    ],
    "I": [
        TeamStanding("England", 2, 2, 0, 0, 3, 0, 6),
        TeamStanding("Ghana", 2, 0, 1, 1, 1, 2, 1),
        TeamStanding("Panama", 2, 0, 1, 1, 0, 2, 1),
        TeamStanding("Croatia", 2, 0, 0, 2, 0, 0, 0),
    ],
    "J": [
        TeamStanding("Argentina", 2, 2, 0, 0, 2, 0, 6),
        TeamStanding("Jordan", 2, 1, 0, 1, 1, 2, 3),
        TeamStanding("Austria", 2, 0, 1, 1, 2, 0, 1),
        TeamStanding("Algeria", 2, 0, 1, 1, 2, 2, 1),
    ],
    "K": [
        TeamStanding("Colombia", 2, 1, 1, 0, 4, 1, 4),
        TeamStanding("Portugal", 2, 1, 0, 1, 0, 1, 3),
        TeamStanding("DR Congo", 2, 1, 0, 1, 0, 0, 3),
        TeamStanding("Uzbekistan", 2, 0, 1, 1, 0, 2, 1),
    ],
    "L": [
        TeamStanding("Belgium", 2, 1, 1, 0, 0, 0, 4),
        TeamStanding("Iran", 2, 1, 0, 1, 0, 0, 3),
        TeamStanding("New Zealand", 2, 1, 0, 1, 1, 3, 3),
        TeamStanding("Egypt", 2, 0, 0, 2, 3, 1, 0),
    ],
}

# Remaining matches (Round 3) - only the final group stage matches
# Format: group -> list of (home_team, away_team) tuples for each group's 4 teams
REMAINING_MATCHES = {
    "A": [("Mexico", "Czech Republic"), ("South Africa", "South Korea")],
    "B": [("Canada", "Switzerland"), ("Bosnia and Herzegovina", "Qatar")],
    "C": [("Scotland", "Brazil"), ("Morocco", "Haiti")],
    "D": [("United States", "Turkey"), ("Paraguay", "Australia")],
    "E": [("Ecuador", "Germany"), ("Japan", "Sweden")],
    "F": [("Tunisia", "Netherlands"), ("Egypt", "Iran")],
    "G": [("New Zealand", "Belgium"), ("Cape Verde", "Saudi Arabia")],
    "H": [("Uruguay", "Spain"), ("Norway", "France")],
    "I": [("Senegal", "Iraq"), ("Argentina", "Austria")],
    "J": [("Jordan", "Algeria"), ("Colombia", "Portugal")],
    "K": [("DR Congo", "Uzbekistan"), ("England", "Ghana")],
    "L": [("Panama", "Croatia"), ("Curaçao", "Ivory Coast")],
}


def get_team_group(team: str) -> str | None:
    """Return the group letter (A-L) for a team, or None if not in group stage."""
    for group, standings in GROUP_STANDINGS.items():
        if any(t.team == team for t in standings):
            return group
    return None


def get_group_standings(group: str) -> list[TeamStanding]:
    """Return the current standings for a group, sorted by points (descending)."""
    if group not in GROUP_STANDINGS:
        return []
    standings = GROUP_STANDINGS[group]
    return sorted(standings, key=lambda t: (-t.points, -t.gd))


def get_remaining_matches_in_group(group: str) -> list[tuple[str, str]]:
    """Return list of (home, away) tuples for unplayed matches in this group."""
    return REMAINING_MATCHES.get(group, [])


def simulate_scenarios(
    group: str, target_team: str, target_opponent: str
) -> list[dict]:
    """Simulate key scenarios and determine what result target_team needs.

    Returns a list of dicts:
    [
        {"scenario": "Description of other results", "target_result_needed": "W|D|L|Eliminated|Qualified"},
        ...
    ]

    Only shows the most important scenarios (typically 3-5).
    """
    standings = {t.team: t for t in get_group_standings(group)}
    if target_team not in standings or target_opponent not in standings:
        return []

    # Get all other teams in the group
    other_teams = [t for t in standings.keys() if t not in (target_team, target_opponent)]
    remaining = get_remaining_matches_in_group(group)

    # Identify which remaining matches involve other teams
    other_remaining = [m for m in remaining if m[0] != target_team and m[1] != target_team]

    scenarios = []

    # Scenario 1: Target team vs opponent (the main match we're predicting)
    # We'll compute what they need for each possible result
    scenarios.append({
        "scenario": "Base scenario (this match only)",
        "target_result_needed": "TBD",  # Will be overridden per result
        "is_base": True,
    })

    # Scenario 2-4: Key outcomes from other teams' matches
    if other_remaining:
        # Take the first match involving other key teams
        h, a = other_remaining[0]
        if h in standings and a in standings:
            h_rank = standings[h].points
            a_rank = standings[a].points
            if h_rank >= a_rank:
                scenarios.append({
                    "scenario": f"If {h} beats {a}",
                    "key_match": (h, a, "home_win"),
                })
            scenarios.append({
                "scenario": f"If {h} draws {a}",
                "key_match": (h, a, "draw"),
            })
            if a_rank >= h_rank:
                scenarios.append({
                    "scenario": f"If {a} beats {h}",
                    "key_match": (h, a, "away_win"),
                })

    return scenarios[:5]  # Return top 5 scenarios


def calculate_qualification(
    group: str, target_team: str, target_result: str
) -> bool:
    """Determine if target_team qualifies with a specific result.

    target_result: "W" (win), "D" (draw), "L" (loss), "Qualified" (already)

    Returns True if the team advances to knockout stage.
    """
    if target_result == "Qualified":
        return True
    if target_result == "Eliminated":
        return False

    standings = {t.team: t for t in get_group_standings(group)}
    if target_team not in standings:
        return False

    current = standings[target_team]
    points_with_result = {
        "W": current.points + 3,
        "D": current.points + 1,
        "L": current.points,
    }

    new_points = points_with_result.get(target_result, current.points)

    # Simplified heuristic: top 2 teams in group advance
    # A team with 6+ points is almost certainly in top 2
    # A team with 3+ points has a good chance unless several others have 4+
    # A team with 0-2 points is likely eliminated
    if new_points >= 7:
        return True
    if new_points <= 2:
        return False
    # For 3-6 points, it depends on other teams - assume they qualify if above 4
    return new_points >= 4


if __name__ == "__main__":
    # Quick test
    print("Group H standings:")
    for t in get_group_standings("H"):
        print(f"  {t.team:<20} {t.points}pts  ({t.wins}W {t.draws}D {t.losses}L)")

    print("\nFrance vs Norway qualification scenarios:")
    scenarios = simulate_scenarios("H", "France", "Norway")
    for s in scenarios:
        print(f"  {s}")
