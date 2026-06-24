"""Backtesting and hyper-parameter tuning.

We evaluate the model the way football forecasts are judged in the literature:

* **Ranked Probability Score (RPS)** - the standard proper scoring rule for
  ordered outcomes (home win / draw / away win).  Lower is better.
* **Multiclass log-loss** - secondary proper scoring rule.
* **Accuracy** - share of matches whose most-likely outcome was correct.

Tuning is done with a *walk-forward* (out-of-sample) split: for every match in a
recent evaluation window we fit the model on everything that happened strictly
before it and score the prediction.  To keep this affordable we refit on a
periodic cadence (every ``refit_days``) rather than for literally every match -
the parameters barely move day to day.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from .dixon_coles import fit_dixon_coles


def ranked_probability_score(probs: np.ndarray, outcome: int) -> float:
    """RPS for a single 3-way ordered prediction.

    probs = [p_home, p_draw, p_away]; outcome in {0,1,2}.
    """
    obs = np.zeros(3)
    obs[outcome] = 1.0
    cum_p = np.cumsum(probs)
    cum_o = np.cumsum(obs)
    return float(np.sum((cum_p - cum_o) ** 2) / (len(probs) - 1))


def _outcome(home_goals: int, away_goals: int) -> int:
    if home_goals > away_goals:
        return 0
    if home_goals == away_goals:
        return 1
    return 2


def evaluate(
    matches: pd.DataFrame,
    xi: float,
    reg: float,
    eval_start: str,
    refit_days: int = 30,
    min_train: int = 2000,
    train_window_years: int = 8,
) -> dict:
    """Walk-forward evaluation over matches on/after ``eval_start``.

    ``train_window_years`` caps each refit to recent matches; with exponential
    time-decay the older games carry ~0 weight anyway, so this only speeds
    things up without affecting the forecasts.
    """
    matches = matches.sort_values("date").reset_index(drop=True)
    eval_mask = matches["date"] >= pd.Timestamp(eval_start)
    eval_idx = np.where(eval_mask.to_numpy())[0]
    eval_idx = eval_idx[eval_idx >= min_train]
    if len(eval_idx) == 0:
        raise ValueError("No evaluation matches after warm-up period.")

    rps_list, ll_list, hits = [], [], 0
    n_used = 0
    model = None
    last_fit_date = None

    for k in eval_idx:
        row = matches.iloc[k]
        cur_date = row["date"]

        # Refit periodically on everything strictly before the current match.
        if last_fit_date is None or (cur_date - last_fit_date).days >= refit_days:
            train = matches.iloc[:k]
            window_start = cur_date - pd.DateOffset(years=train_window_years)
            train = train[train["date"] >= window_start]
            model = fit_dixon_coles(train, xi=xi, reg=reg, ref_date=cur_date)
            last_fit_date = cur_date

        h, a = row["home_team"], row["away_team"]
        if not (model.has_team(h) and model.has_team(a)):
            continue  # unseen team - skip rather than guess

        pred = model.predict(h, a, neutral=bool(row["neutral"]))
        probs = np.array([pred["p_home_win"], pred["p_draw"], pred["p_away_win"]])
        outcome = _outcome(int(row["home_score"]), int(row["away_score"]))

        rps_list.append(ranked_probability_score(probs, outcome))
        ll_list.append(-np.log(max(probs[outcome], 1e-12)))
        hits += int(np.argmax(probs) == outcome)
        n_used += 1

    return {
        "xi": xi,
        "reg": reg,
        "n_matches": n_used,
        "rps": float(np.mean(rps_list)),
        "log_loss": float(np.mean(ll_list)),
        "accuracy": float(hits / n_used) if n_used else float("nan"),
    }


def tune(
    matches: pd.DataFrame,
    eval_start: str = "2023-06-01",
    xi_grid=None,
    reg_grid=None,
    refit_days: int = 45,
    verbose: bool = True,
) -> tuple[dict, list[dict]]:
    """Grid-search xi and reg by walk-forward RPS. Returns (best, all_results)."""
    if xi_grid is None:
        # xi expressed as a half-life in days, converted to a rate.
        half_lives = [180, 365, 550, 730, 1095]
        xi_grid = [np.log(2) / hl for hl in half_lives]
    if reg_grid is None:
        reg_grid = [0.005, 0.02, 0.05]

    results = []
    for xi, reg in itertools.product(xi_grid, reg_grid):
        res = evaluate(matches, xi=xi, reg=reg, eval_start=eval_start, refit_days=refit_days)
        results.append(res)
        if verbose:
            hl = np.log(2) / xi
            print(
                f"  half-life={hl:6.0f}d reg={reg:5.3f} | "
                f"RPS={res['rps']:.4f} logloss={res['log_loss']:.4f} "
                f"acc={res['accuracy']:.3f} (n={res['n_matches']})"
            )

    best = min(results, key=lambda r: r["rps"])
    return best, results


if __name__ == "__main__":
    from .data import get_data

    comp, _ = get_data()
    print("Tuning Dixon-Coles (walk-forward, RPS)...")
    best, _ = tune(comp)
    print(
        f"\nBest: half-life={np.log(2)/best['xi']:.0f}d reg={best['reg']} "
        f"RPS={best['rps']:.4f} acc={best['accuracy']:.3f}"
    )
