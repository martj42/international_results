import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from statistics import mean, median, mode
from src.statistics_processor import TeamStats

def test_initial_state():
    stats = TeamStats()
    assert stats.matches == 0
    assert stats.wins == 0
    assert stats.losses == 0
    assert stats.draws == 0
    assert stats.goals_for == 0
    assert stats.goals_against == 0
    assert stats.goals_list == []

def test_update_win():
    stats = TeamStats()
    stats.update(3, 1, "win")
    assert stats.matches == 1
    assert stats.wins == 1
    assert stats.losses == 0
    assert stats.draws == 0
    assert stats.goals_for == 3
    assert stats.goals_against == 1
    assert stats.goals_list == [3]

def test_update_loss():
    stats = TeamStats()
    stats.update(0, 2, "loss")
    assert stats.matches == 1
    assert stats.wins == 0
    assert stats.losses == 1
    assert stats.draws == 0
    assert stats.goals_for == 0
    assert stats.goals_against == 2
    assert stats.goals_list == [0]

def test_update_draw():
    stats = TeamStats()
    stats.update(2, 2, "draw")
    assert stats.matches == 1
    assert stats.wins == 0
    assert stats.losses == 0
    assert stats.draws == 1
    assert stats.goals_for == 2
    assert stats.goals_against == 2
    assert stats.goals_list == [2]

def test_multiple_updates_and_summary():
    stats = TeamStats()
    stats.update(1, 0, "win")
    stats.update(2, 2, "draw")
    stats.update(0, 3, "loss")
    summary = stats.stats_summary()
    assert summary["matches"] == 3
    assert summary["wins"] == 1
    assert summary["losses"] == 1
    assert summary["draws"] == 1
    assert summary["goals_for"] == 3
    assert summary["goals_against"] == 5
    assert summary["mean_goals"] == int(mean([1,2,0]))
    assert summary["median_goals"] == int(median([1,2,0]))
    assert summary["mode_goals"] == int(mode([1,2,0]))

def test_stats_summary_empty():
    stats = TeamStats()
    summary = stats.stats_summary()
    assert "mean_goals" not in summary
    assert "median_goals" not in summary
    assert "mode_goals" not in summary
