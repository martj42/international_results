"""Data loading and cleaning for the international results dataset.

The repository ships a single canonical fixture/result source: `results.csv`.
Completed matches have integer scores; *upcoming* matches (the ones we want to
predict) are present as rows whose `home_score`/`away_score` are the literal
string ``NA``.  We therefore never need to scrape an external provider - the
fixtures we care about already live in the dataset.
"""

from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
RESULTS_CSV = os.path.join(REPO_ROOT, "results.csv")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_raw(path: str = RESULTS_CSV) -> pd.DataFrame:
    """Load results.csv with robust parsing.

    A handful of rows contain commas inside quoted city names
    (e.g. ``"Washington, D.C."``); pandas' default C parser handles the
    quoting correctly, so we simply rely on it rather than hand-rolling a
    splitter.
    """
    df = pd.read_csv(
        path,
        dtype={
            "home_team": "string",
            "away_team": "string",
            "tournament": "string",
            "city": "string",
            "country": "string",
        },
        keep_default_na=False,  # keep the literal "NA" so we can detect fixtures
        na_values=[],
    )
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).reset_index(drop=True)

    # Scores: "NA" (upcoming) -> NaN, everything else -> numeric.
    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")

    # neutral column is "TRUE"/"FALSE" text.
    df["neutral"] = (
        df["neutral"].astype("string").str.strip().str.upper() == "TRUE"
    )

    for col in ("home_team", "away_team", "tournament"):
        df[col] = df[col].astype("string").str.strip()

    return df


def completed_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Matches that have actually been played (both scores known)."""
    mask = df["home_score"].notna() & df["away_score"].notna()
    out = df.loc[mask].copy()
    out["home_score"] = out["home_score"].astype(int)
    out["away_score"] = out["away_score"].astype(int)
    return out.sort_values("date").reset_index(drop=True)


def upcoming_fixtures(df: pd.DataFrame) -> pd.DataFrame:
    """Scheduled-but-unplayed matches (scores are NA in the dataset)."""
    mask = df["home_score"].isna() | df["away_score"].isna()
    out = df.loc[mask].copy()
    return out.sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Convenience accessors used by the rest of the package
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_data():
    """Return (completed, upcoming) as a cached tuple of DataFrames."""
    df = load_raw()
    return completed_matches(df), upcoming_fixtures(df)


def all_team_names(completed: pd.DataFrame) -> list[str]:
    teams = pd.unique(
        pd.concat([completed["home_team"], completed["away_team"]], ignore_index=True)
    )
    return sorted(t for t in teams.tolist() if isinstance(t, str) and t)


if __name__ == "__main__":
    comp, up = get_data()
    print(f"Completed matches : {len(comp):,}")
    print(f"Upcoming fixtures : {len(up):,}")
    print(f"Distinct teams    : {len(all_team_names(comp)):,}")
    print(f"Date range        : {comp['date'].min().date()} -> {comp['date'].max().date()}")
    print("\nNext 10 fixtures:")
    cols = ["date", "home_team", "away_team", "tournament", "neutral"]
    print(up[cols].head(10).to_string(index=False))
