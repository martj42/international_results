"""Interactive World-Cup match predictor.

Usage
-----
    python -m world_cup_predictor.predict

Type a national team's name (e.g. ``France``) and the app shows that team's
*next scheduled* fixture from the dataset together with the model's prediction:
win/draw/loss probabilities, expected goals and the most likely correct scores.

The fitted model is loaded from ``model.json`` (created by ``train.py``).  If it
is missing, the app offers to train it on the spot.
"""

from __future__ import annotations

import difflib
import os
import sys

import pandas as pd

from .data import get_data, all_team_names
from .dixon_coles import DixonColesModel
from .qualification import format_qualification_scenarios

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.json")


# ---------------------------------------------------------------------------
# Team-name resolution
# ---------------------------------------------------------------------------
# Common shorthand / colloquial names -> canonical dataset names.
ALIASES = {
    "usa": "United States",
    "us": "United States",
    "u.s.a.": "United States",
    "america": "United States",
    "holland": "Netherlands",
    "korea": "South Korea",
    "czechia": "Czech Republic",
    "bosnia": "Bosnia and Herzegovina",
    "ivory coast": "Ivory Coast",
    "cote d'ivoire": "Ivory Coast",
    "uae": "United Arab Emirates",
    "drc": "DR Congo",
    "dr congo": "DR Congo",
}


def resolve_team(query: str, teams: list[str]) -> str | None:
    """Map free-text user input to a canonical team name.

    Tries aliases, then exact (case-insensitive), then substring, then fuzzy
    matching.  Returns the canonical name or None if nothing is close enough.
    """
    q = query.strip()
    if not q:
        return None
    teamset = set(teams)
    if q.lower() in ALIASES and ALIASES[q.lower()] in teamset:
        return ALIASES[q.lower()]
    lower = {t.lower(): t for t in teams}
    if q.lower() in lower:
        return lower[q.lower()]

    subs = [t for t in teams if q.lower() in t.lower()]
    if len(subs) == 1:
        return subs[0]
    if len(subs) > 1:
        # Prefer an exact-word-start match if unambiguous.
        starts = [t for t in subs if t.lower().startswith(q.lower())]
        if len(starts) == 1:
            return starts[0]
        return None  # ambiguous - caller will show suggestions

    close = difflib.get_close_matches(q, teams, n=3, cutoff=0.6)
    return close[0] if len(close) == 1 else None


def suggestions(query: str, teams: list[str], n: int = 5) -> list[str]:
    q = query.strip().lower()
    subs = [t for t in teams if q in t.lower()]
    if subs:
        return subs[:n]
    return difflib.get_close_matches(query, teams, n=n, cutoff=0.4)


# ---------------------------------------------------------------------------
# Fixture lookup
# ---------------------------------------------------------------------------
def next_fixture(team: str, fixtures: pd.DataFrame):
    """Earliest upcoming fixture involving ``team`` (or None)."""
    mask = (fixtures["home_team"] == team) | (fixtures["away_team"] == team)
    rows = fixtures.loc[mask].sort_values("date")
    if rows.empty:
        return None
    return rows.iloc[0]


# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------
def _bar(p: float, width: int = 24) -> str:
    filled = int(round(p * width))
    return "#" * filled + "." * (width - filled)


def format_prediction(team: str, fixture: pd.Series, model: DixonColesModel) -> str:
    home = fixture["home_team"]
    away = fixture["away_team"]
    neutral = bool(fixture["neutral"])
    date = pd.Timestamp(fixture["date"]).date()
    venue = f"{fixture.get('city', '')}, {fixture.get('country', '')}".strip(", ")
    tournament = fixture.get("tournament", "")

    if not (model.has_team(home) and model.has_team(away)):
        missing = home if not model.has_team(home) else away
        return f"  Sorry - the model has no rating for '{missing}'."

    pred = model.predict(home, away, neutral=neutral, top_n=6)

    # Orient everything from the queried team's perspective.
    team_is_home = team == home
    opponent = away if team_is_home else home
    p_team = pred["p_home_win"] if team_is_home else pred["p_away_win"]
    p_opp = pred["p_away_win"] if team_is_home else pred["p_home_win"]
    p_draw = pred["p_draw"]
    xg_team = pred["exp_home_goals"] if team_is_home else pred["exp_away_goals"]
    xg_opp = pred["exp_away_goals"] if team_is_home else pred["exp_home_goals"]

    outcomes = {team: p_team, "Draw": p_draw, opponent: p_opp}
    verdict = max(outcomes, key=outcomes.get)
    if verdict == "Draw":
        verdict_txt = "Most likely: a draw"
    else:
        verdict_txt = f"Most likely winner: {verdict}  ({outcomes[verdict]*100:.0f}%)"

    # Most likely scoreline, oriented to team-opponent.
    (hg, ag), sp = pred["scorelines"][0]
    ts, os_ = (hg, ag) if team_is_home else (ag, hg)

    venue_note = "neutral venue" if neutral else f"home advantage to {home}"

    lines = []
    lines.append("")
    lines.append("=" * 58)
    lines.append(f"  {team}'s next match")
    lines.append("=" * 58)
    lines.append(f"  {home}  vs  {away}")
    lines.append(f"  {date}   {tournament}")
    lines.append(f"  {venue}   ({venue_note})")
    lines.append("-" * 58)

    # Add qualification scenarios if available
    qual_scenarios = format_qualification_scenarios(home, away)
    if qual_scenarios:
        lines.append(qual_scenarios)
        lines.append("-" * 58)

    lines.append("  Outcome probabilities:")
    lines.append(f"    {team:<22} {p_team*100:5.1f}%  {_bar(p_team)}")
    lines.append(f"    {'Draw':<22} {p_draw*100:5.1f}%  {_bar(p_draw)}")
    lines.append(f"    {opponent:<22} {p_opp*100:5.1f}%  {_bar(p_opp)}")
    lines.append("-" * 58)
    lines.append(f"  Expected goals:   {team} {xg_team:.2f}  -  {xg_opp:.2f} {opponent}")
    lines.append(f"  Predicted score:  {team} {ts} - {os_} {opponent}  "
                 f"(p={sp*100:.1f}%)")
    lines.append("-" * 58)
    lines.append("  Most likely scorelines:")
    for (h, a), p in pred["scorelines"][:5]:
        t_, o_ = (h, a) if team_is_home else (a, h)
        lines.append(f"    {team} {t_} - {o_} {opponent:<18} {p*100:5.1f}%")
    lines.append("-" * 58)
    lines.append(f"  >>> {verdict_txt}")
    lines.append("=" * 58)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
def load_or_train() -> DixonColesModel:
    if os.path.exists(MODEL_PATH):
        return DixonColesModel.from_json(MODEL_PATH)
    print("No trained model found. Training now (this takes a few minutes)...")
    from .train import main as train_main

    train_main()
    return DixonColesModel.from_json(MODEL_PATH)


def main():
    model = load_or_train()
    comp, fixtures = get_data()
    teams = all_team_names(comp)

    upcoming_teams = sorted(
        set(fixtures["home_team"]) | set(fixtures["away_team"])
    )

    print("\n" + "=" * 58)
    print("  WORLD CUP MATCH PREDICTOR  (Dixon-Coles, time-weighted)")
    print("=" * 58)
    print(f"  Model trained up to {model.trained_until}.")
    print(f"  {len(fixtures)} upcoming fixtures, {len(upcoming_teams)} teams with a next game.")
    print("  Type a team name (e.g. 'France'). 'teams' to list, 'quit' to exit.")
    print("=" * 58)

    while True:
        try:
            raw = input("\nTeam > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not raw:
            continue
        if raw.lower() in {"quit", "exit", "q"}:
            print("Bye!")
            break
        if raw.lower() in {"teams", "list"}:
            print("  Teams with an upcoming fixture:")
            print("   " + ", ".join(upcoming_teams))
            continue

        team = resolve_team(raw, teams)
        if team is None:
            sug = suggestions(raw, teams)
            if sug:
                print(f"  '{raw}' not recognised. Did you mean: {', '.join(sug)}?")
            else:
                print(f"  '{raw}' not recognised and no close match found.")
            continue

        fx = next_fixture(team, fixtures)
        if fx is None:
            print(f"  {team} has no upcoming fixture in the dataset "
                  f"(eliminated or not scheduled).")
            continue

        print(format_prediction(team, fx, model))


if __name__ == "__main__":
    main()
