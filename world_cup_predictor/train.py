"""Train the Dixon-Coles model and persist it.

Run once (``python -m world_cup_predictor.train``).  It:

1. tunes the time-decay (xi) and ridge (reg) hyper-parameters by walk-forward
   Ranked Probability Score,
2. compares the tuned model against a naive base-rate baseline so the value
   added is explicit,
3. refits on the most recent data with the chosen settings,
4. saves the fitted parameters to ``model.json`` next to this file.

The interactive app (`predict.py`) just loads that file, so prediction is
instant.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

from .backtest import evaluate, tune, ranked_probability_score, _outcome
from .data import get_data
from .dixon_coles import fit_dixon_coles

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.json")
TRAIN_WINDOW_YEARS = 8
EVAL_START = "2023-06-01"


def baseline_rps(matches: pd.DataFrame, eval_start: str) -> dict:
    """Base-rate baseline: predict the historical home/draw/away frequencies
    (computed on the training portion) for every match."""
    matches = matches.sort_values("date").reset_index(drop=True)
    cut = pd.Timestamp(eval_start)
    train = matches[matches["date"] < cut]
    test = matches[matches["date"] >= cut]

    outcomes = np.array(
        [_outcome(int(h), int(a)) for h, a in zip(train["home_score"], train["away_score"])]
    )
    base = np.array([(outcomes == c).mean() for c in (0, 1, 2)])

    rps, hits = [], 0
    for h, a in zip(test["home_score"], test["away_score"]):
        o = _outcome(int(h), int(a))
        rps.append(ranked_probability_score(base, o))
        hits += int(np.argmax(base) == o)
    return {
        "probs": base.tolist(),
        "rps": float(np.mean(rps)),
        "accuracy": float(hits / len(test)),
        "n": int(len(test)),
    }


def main():
    comp, up = get_data()
    print(f"Loaded {len(comp):,} completed matches, {len(up)} upcoming fixtures.\n")

    print("Step 1/3  Baseline (home/draw/away base rates)")
    base = baseline_rps(comp, EVAL_START)
    print(
        f"  base rates P(home/draw/away) = "
        f"{base['probs'][0]:.2f}/{base['probs'][1]:.2f}/{base['probs'][2]:.2f}"
    )
    print(f"  baseline RPS={base['rps']:.4f} acc={base['accuracy']:.3f} (n={base['n']})\n")

    print("Step 2/3  Tuning Dixon-Coles (walk-forward RPS)")
    best, results = tune(comp, eval_start=EVAL_START, verbose=True)
    hl = np.log(2) / best["xi"]
    print(
        f"\n  -> best: half-life={hl:.0f}d reg={best['reg']} "
        f"RPS={best['rps']:.4f} acc={best['accuracy']:.3f}"
    )
    improve = 100 * (base["rps"] - best["rps"]) / base["rps"]
    print(f"  -> {improve:.1f}% better RPS than the base-rate baseline\n")

    print("Step 3/3  Final fit on recent data and save")
    ref = comp["date"].max()
    window_start = ref - pd.DateOffset(years=TRAIN_WINDOW_YEARS)
    train = comp[comp["date"] >= window_start].reset_index(drop=True)
    model = fit_dixon_coles(train, xi=best["xi"], reg=best["reg"], ref_date=ref, verbose=True)
    model.to_json(MODEL_PATH)
    print(f"  saved {len(model.teams)} teams to {MODEL_PATH}")
    print(f"  home advantage={model.home_adv:.3f}  rho={model.rho:.3f}  "
          f"trained_until={model.trained_until}")

    # A quick peek at the strongest sides by net rating (attack - defence).
    rating = model.attack - model.defence
    order = np.argsort(rating)[::-1][:10]
    print("\nTop 10 teams by net rating (attack - defence allowed):")
    for r, i in enumerate(order, 1):
        print(f"  {r:2d}. {model.teams[i]:<22} {rating[i]:+.2f}")


if __name__ == "__main__":
    main()
