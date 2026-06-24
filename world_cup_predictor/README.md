# World Cup Match Predictor

A machine-learning predictor for international football matches built on this
repository's `results.csv`. It forecasts the **match outcome** (win / draw /
loss probabilities) **and the most likely correct score** for upcoming games,
and ships as a small interactive command-line app: type a national team's name
(e.g. `France`) and it shows that team's next scheduled fixture plus the
prediction.

## Quick start

```bash
# from the repository root
pip install -r world_cup_predictor/requirements.txt

# 1) train once (tunes hyper-parameters, fits, and saves model.json)
python -m world_cup_predictor.train

# 2) run the interactive predictor
python -m world_cup_predictor.predict
#   ... or:  python world_cup_predictor/run.py
```

You only train once. After that the predictor loads the saved `model.json`
instantly. (If you launch the predictor before training, it offers to train on
the spot.)

Example session:

```
Team > France
==========================================================
  France's next match
==========================================================
  Norway  vs  France
  2026-06-26   FIFA World Cup
  Foxborough, United States   (neutral venue)
----------------------------------------------------------
  Outcome probabilities:
    France                  48.0%  ############............
    Draw                    25.8%  ######..................
    Norway                  26.3%  ######..................
----------------------------------------------------------
  Expected goals:   France 1.66  -  1.17 Norway
  Predicted score:  France 1 - 1 Norway  (p=12.2%)
----------------------------------------------------------
  Most likely scorelines:
    France 1 - 1 Norway              12.2%
    France 2 - 1 Norway               9.5%
    France 1 - 0 Norway               9.1%
    ...
  >>> Most likely winner: France  (48%)
==========================================================
```

Type `teams` to list the teams that have an upcoming fixture, or `quit` to exit.
Common shorthands work too (`USA`, `Holland`, `Korea`, ...).

## Where do fixtures come from?

The upcoming games are read directly from `results.csv`: scheduled-but-unplayed
matches are stored there with `NA` scores (the 2026 World Cup fixtures are
already present). This is the curated, offline source for "what game is next",
so no live scraping of Sofascore / FlashScore is required — and indeed those
providers are network-blocked in many sandboxed environments.

## The model: time-weighted Dixon-Coles

The predictor uses the **Dixon & Coles (1997)** model, the well-validated
standard for forecasting football outcomes *and* exact scorelines. It models the
two teams' goals as (almost) independent Poisson variables:

```
log(λ_home) = home_advantage · is_home + attack[home] + defence[away]
log(μ_away) =                            attack[away] + defence[home]
```

* **Per-team attack / defence strengths** are learned for every nation.
* **Home advantage** applies only when the match is *not* at a neutral venue —
  so neutral World Cup sites get no edge, while genuine host-nation games
  (Mexico / USA / Canada in 2026) do.
* A **low-score dependency parameter `ρ`** applies the Dixon-Coles correction to
  the 0-0 / 1-0 / 0-1 / 1-1 cells, fixing the known Poisson mis-fit on
  low-scoring results.
* **Exponential time-decay** (`exp(-ξ · age_in_days)`) weights recent matches
  more than old ones, so current form dominates.
* A small **ridge penalty** on the team parameters resolves the
  attack/defence identifiability and shrinks teams with few matches toward the
  mean, improving out-of-sample accuracy.

From the fitted parameters we build the full joint score-probability matrix

```
P(x, y) = τ(x, y; λ, μ, ρ) · Poisson(x; λ) · Poisson(y; μ)
```

and read off win/draw/loss probabilities (by summing the matrix), the expected
goals, and the most likely scorelines.

### Fitting

Parameters are estimated by maximising the time-weighted log-likelihood with
**L-BFGS-B and an analytic gradient** (so the ~700-parameter fit converges in
under a second). See `dixon_coles.py`.

### Hyper-parameter tuning and accuracy

`train.py` tunes the time-decay half-life and ridge strength by **walk-forward
(out-of-sample) backtesting**, scored with the **Ranked Probability Score
(RPS)** — the standard proper scoring rule for ordered football outcomes — plus
log-loss and accuracy (`backtest.py`).

On the most recent ~3 years of internationals the tuned model scores roughly:

| Model                         | RPS ↓     | Accuracy ↑ |
| ----------------------------- | --------- | ---------- |
| Base-rate baseline            | ~0.229    | ~47%       |
| **Tuned Dixon-Coles**         | **~0.163**| **~61%**   |

i.e. about a **29% RPS improvement** over predicting historical base rates,
with ~61% of match outcomes called correctly — in line with published
state-of-the-art international-football forecasts.

## Files

| File             | Purpose                                                        |
| ---------------- | ------------------------------------------------------------- |
| `data.py`        | Load/clean `results.csv`; split completed vs upcoming fixtures |
| `dixon_coles.py` | The model: fit (analytic gradient) + score-matrix prediction   |
| `backtest.py`    | Walk-forward evaluation (RPS / log-loss / accuracy) + tuning   |
| `train.py`       | Tune → compare to baseline → fit → save `model.json`           |
| `predict.py`     | Interactive CLI (team name → next fixture + prediction)        |
| `run.py`         | Convenience launcher (`--train` to retrain first)             |

## Notes & limitations

* The model rates *team strength and form*; it does not know about injuries,
  suspensions, or in-tournament squad rotation.
* Knockout-stage opponents that are not yet decided won't appear as fixtures
  until the dataset is updated. To predict a hypothetical matchup directly you
  can call `DixonColesModel.predict("Spain", "Brazil", neutral=True)` in Python.
* Re-run `python -m world_cup_predictor.train` whenever `results.csv` is updated
  with new results to refresh the ratings.
