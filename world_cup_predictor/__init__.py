"""World Cup match predictor built on the international results dataset.

A time-weighted Dixon-Coles Poisson model that forecasts match outcomes and the
most likely correct score.  See ``README.md`` in this directory.
"""

__all__ = ["data", "dixon_coles", "backtest", "train", "predict"]
