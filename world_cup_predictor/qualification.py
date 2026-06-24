"""Qualification scenario display and analysis.

Determines what each team needs to qualify based on current group standings
and simulates key dependency scenarios.
"""

from __future__ import annotations

from .standings import (
    get_team_group,
    get_group_standings,
    get_remaining_matches_in_group,
    calculate_qualification,
)


def get_qualification_summary(team: str) -> tuple[str, str]:
    """Get a one-line summary of a team's qualification status.

    Returns (status_text, symbol) where:
    - status_text: "Already qualified", "Must...", "Can...", "Eliminated"
    - symbol: "✓", "!", "?", "✗"
    """
    group = get_team_group(team)
    if not group:
        return "Not in group stage", "—"

    standings = {t.team: t for t in get_group_standings(group)}
    if team not in standings:
        return "Unknown team", "—"

    current_points = standings[team].points
    remaining = get_remaining_matches_in_group(group)
    other_matches = [m for m in remaining if team not in m]

    # Check if already qualified or eliminated
    if current_points >= 7:
        return "Already qualified ✓", "✓"
    if current_points <= 0 and len(other_matches) == len(remaining):
        return "Eliminated", "✗"

    # Determine what's needed
    scenarios = []
    for result in ["W", "D", "L"]:
        qualifies = calculate_qualification(group, team, result)
        if result == "W":
            scenarios.append(("win", qualifies))
        elif result == "D":
            scenarios.append(("draw", qualifies))
        else:
            scenarios.append(("loss", qualifies))

    wins_if_win, wins_if_draw, wins_if_loss = [q for _, q in scenarios]

    if wins_if_win and wins_if_draw and wins_if_loss:
        return "Can qualify with any result", "✓"
    elif wins_if_win and wins_if_draw:
        return "Can qualify (needs W or D)", "?"
    elif wins_if_win:
        return "MUST WIN to advance", "!"
    elif wins_if_draw:
        return "Can qualify (needs W or D)", "?"
    else:
        return "Likely eliminated", "✗"


def format_qualification_scenarios(home: str, away: str) -> str:
    """Format detailed qualification scenarios for both teams.

    Returns a multi-line string showing:
    - Team name and qualification status
    - Dependency scenarios from other group matches
    - What result is needed in each scenario
    """
    group_h = get_team_group(home)
    group_a = get_team_group(away)

    if group_h != group_a or not group_h:
        return ""

    group = group_h
    standings = {t.team: t for t in get_group_standings(group)}
    remaining = get_remaining_matches_in_group(group)

    # Get other matches in this group (excluding the one we're predicting)
    other_matches = [
        (h, a) for h, a in remaining if not ((h == home and a == away) or (h == away and a == home))
    ]

    lines = []
    lines.append("")
    lines.append("Qualification scenarios:")

    # Format for home team
    home_status, home_sym = get_qualification_summary(home)
    lines.append(f"  {home:<22} {home_status}")

    # Show specific scenarios for home team if not already qualified
    if "Eliminated" not in home_status and "Already qualified" not in home_status:
        lines.append(f"    This match: {home} needs to {'WIN' if 'Must' in home_status else 'get at least a DRAW' if 'needs W or D' in home_status else 'just play'} to have a strong chance")

    # Format for away team
    away_status, away_sym = get_qualification_summary(away)
    lines.append(f"  {away:<22} {away_status}")

    # Show specific scenarios for away team if not already qualified
    if "Eliminated" not in away_status and "Already qualified" not in away_status:
        lines.append(f"    This match: {away} needs to {'WIN' if 'Must' in away_status else 'get at least a DRAW' if 'needs W or D' in away_status else 'just play'} to have a strong chance")

    # Show key other matches that might affect these teams
    if other_matches:
        lines.append("")
        lines.append("  Other matches in this group:")
        for h, a in other_matches[:2]:  # Show top 2 other matches
            lines.append(f"    • {h} vs {a}")

    return "\n".join(lines)


if __name__ == "__main__":
    # Test
    print(format_qualification_scenarios("France", "Norway"))
    print("\n---\n")
    print(format_qualification_scenarios("Brazil", "Scotland"))
