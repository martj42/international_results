"""Time-weighted Dixon-Coles model for international football.

The Dixon & Coles (1997) model is the standard, well-validated approach for
forecasting *both* the match outcome and the exact scoreline.  Goals are
modelled as (almost) independent Poisson variables whose rates depend on a
per-team attack strength, a per-team defence strength and a global home
advantage.  A low-score dependency parameter ``rho`` corrects the known excess
of 0-0 / 1-0 / 0-1 / 1-1 results, and an exponential time-decay weights recent
matches more heavily than ancient ones.

For a match between home team *i* and away team *j*::

    log(lambda) = home_adv * is_home + attack[i] + defence[j]   # home goals
    log(mu)     =                       attack[j] + defence[i]   # away goals

(``is_home`` is 0 at a neutral venue, so World-Cup neutral-site games get no
home edge while genuine host-nation games do.)

The full joint distribution of a scoreline (x, y) is::

    P(x, y) = tau(x, y; lambda, mu, rho) * Poisson(x; lambda) * Poisson(y; mu)

from which win/draw/loss probabilities and the most likely correct score are
obtained by summing the score matrix.

We fit the parameters by maximising the time-weighted log-likelihood with a
small ridge penalty on the team parameters.  The penalty both resolves the
attack/defence identifiability (their overall level is otherwise unidentified)
and shrinks teams with few matches toward the global mean - which improves
out-of-sample accuracy.  An analytic gradient is supplied so the ~700-parameter
optimisation converges in seconds rather than minutes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson


# ---------------------------------------------------------------------------
# Dixon-Coles low-score correction tau and its derivatives
# ---------------------------------------------------------------------------
def _tau(x, y, lam, mu, rho):
    """Vectorised tau(x, y; lambda, mu, rho)."""
    out = np.ones_like(lam, dtype=float)
    m00 = (x == 0) & (y == 0)
    m01 = (x == 0) & (y == 1)
    m10 = (x == 1) & (y == 0)
    m11 = (x == 1) & (y == 1)
    out[m00] = 1.0 - lam[m00] * mu[m00] * rho
    out[m01] = 1.0 + lam[m01] * rho
    out[m10] = 1.0 + mu[m10] * rho
    out[m11] = 1.0 - rho
    return out


@dataclass
class DixonColesModel:
    """Fitted Dixon-Coles parameters plus the metadata needed to predict."""

    teams: list[str]
    attack: np.ndarray
    defence: np.ndarray
    home_adv: float
    rho: float
    xi: float                      # time-decay rate (per day)
    reg: float                     # ridge strength used at fit time
    trained_until: str = ""        # ISO date of the last match used
    max_goals: int = 12
    _index: dict = field(default_factory=dict, repr=False)

    # -- construction -------------------------------------------------------
    def __post_init__(self):
        if not self._index:
            self._index = {t: i for i, t in enumerate(self.teams)}

    def has_team(self, name: str) -> bool:
        return name in self._index

    # -- core scoreline distribution ---------------------------------------
    def score_matrix(self, home: str, away: str, neutral: bool = True) -> np.ndarray:
        """Return the (max_goals+1) x (max_goals+1) joint score probability
        matrix, rows = home goals, cols = away goals."""
        i, j = self._index[home], self._index[away]
        is_home = 0.0 if neutral else 1.0
        lam = np.exp(self.home_adv * is_home + self.attack[i] + self.defence[j])
        mu = np.exp(self.attack[j] + self.defence[i])

        n = self.max_goals + 1
        home_p = poisson.pmf(np.arange(n), lam)
        away_p = poisson.pmf(np.arange(n), mu)
        mat = np.outer(home_p, away_p)

        # Apply the low-score correction to the 2x2 corner.
        mat[0, 0] *= 1.0 - lam * mu * self.rho
        mat[0, 1] *= 1.0 + lam * self.rho
        mat[1, 0] *= 1.0 + mu * self.rho
        mat[1, 1] *= 1.0 - self.rho

        mat = np.clip(mat, 0.0, None)
        mat /= mat.sum()
        return mat

    def expected_goals(self, home: str, away: str, neutral: bool = True):
        i, j = self._index[home], self._index[away]
        is_home = 0.0 if neutral else 1.0
        lam = float(np.exp(self.home_adv * is_home + self.attack[i] + self.defence[j]))
        mu = float(np.exp(self.attack[j] + self.defence[i]))
        return lam, mu

    def predict(self, home: str, away: str, neutral: bool = True, top_n: int = 5):
        """Full prediction: outcome probabilities, expected goals and the most
        likely scorelines."""
        mat = self.score_matrix(home, away, neutral)
        n = mat.shape[0]
        idx = np.arange(n)
        home_win = np.tril(mat, -1).sum()      # home goals > away goals
        away_win = np.triu(mat, 1).sum()       # away goals > home goals
        draw = np.trace(mat)
        lam, mu = self.expected_goals(home, away, neutral)

        # Top-N correct scores.
        flat = np.dstack(np.meshgrid(idx, idx, indexing="ij")).reshape(-1, 2)
        probs = mat.reshape(-1)
        order = np.argsort(probs)[::-1][:top_n]
        scorelines = [
            ((int(flat[k, 0]), int(flat[k, 1])), float(probs[k])) for k in order
        ]

        return {
            "home": home,
            "away": away,
            "neutral": neutral,
            "p_home_win": float(home_win),
            "p_draw": float(draw),
            "p_away_win": float(away_win),
            "exp_home_goals": lam,
            "exp_away_goals": mu,
            "scorelines": scorelines,
            "most_likely_score": scorelines[0][0],
        }

    # -- (de)serialisation --------------------------------------------------
    def to_json(self, path: str):
        payload = asdict(self)
        payload.pop("_index", None)
        payload["attack"] = self.attack.tolist()
        payload["defence"] = self.defence.tolist()
        with open(path, "w") as fh:
            json.dump(payload, fh)

    @classmethod
    def from_json(cls, path: str) -> "DixonColesModel":
        with open(path) as fh:
            payload = json.load(fh)
        payload["attack"] = np.asarray(payload["attack"], dtype=float)
        payload["defence"] = np.asarray(payload["defence"], dtype=float)
        return cls(**payload)


# ---------------------------------------------------------------------------
# Fitting
# ---------------------------------------------------------------------------
def _prepare(matches: pd.DataFrame, ref_date: pd.Timestamp, xi: float):
    """Encode matches into integer team indices, goals, home flags and weights."""
    teams = sorted(
        set(matches["home_team"].tolist()) | set(matches["away_team"].tolist())
    )
    index = {t: i for i, t in enumerate(teams)}
    hi = matches["home_team"].map(index).to_numpy()
    ai = matches["away_team"].map(index).to_numpy()
    x = matches["home_score"].to_numpy(dtype=int)
    y = matches["away_score"].to_numpy(dtype=int)
    is_home = np.where(matches["neutral"].to_numpy(), 0.0, 1.0)

    age_days = (ref_date - matches["date"]).dt.days.to_numpy(dtype=float)
    age_days = np.clip(age_days, 0.0, None)
    weights = np.exp(-xi * age_days)

    return teams, index, hi, ai, x, y, is_home, weights


def fit_dixon_coles(
    matches: pd.DataFrame,
    xi: float = 0.0018,
    reg: float = 0.02,
    ref_date: pd.Timestamp | None = None,
    max_goals: int = 12,
    verbose: bool = False,
) -> DixonColesModel:
    """Fit the time-weighted Dixon-Coles model.

    Parameters
    ----------
    matches : completed matches with columns
        date, home_team, away_team, home_score, away_score, neutral.
    xi : exponential time-decay rate per day (larger = forget faster).
    reg : ridge penalty on attack/defence parameters.
    """
    if ref_date is None:
        ref_date = matches["date"].max()

    teams, index, hi, ai, x, y, is_home, w = _prepare(matches, ref_date, xi)
    nt = len(teams)

    # Parameter vector: [attack(nt), defence(nt), home_adv, rho].
    def unpack(p):
        att = p[:nt]
        dfc = p[nt : 2 * nt]
        home_adv = p[2 * nt]
        rho = p[2 * nt + 1]
        return att, dfc, home_adv, rho

    x0 = np.zeros(2 * nt + 2)
    x0[2 * nt] = 0.25          # sensible home-advantage start
    x0[2 * nt + 1] = -0.05     # typical small negative rho

    # Precompute corner masks for the gradient of log(tau).
    m00 = (x == 0) & (y == 0)
    m01 = (x == 0) & (y == 1)
    m10 = (x == 1) & (y == 0)
    m11 = (x == 1) & (y == 1)

    def neg_ll_and_grad(p):
        att, dfc, home_adv, rho = unpack(p)
        log_lam = home_adv * is_home + att[hi] + dfc[ai]
        log_mu = att[ai] + dfc[hi]
        lam = np.exp(log_lam)
        mu = np.exp(log_mu)

        # Poisson part of the log-likelihood (factorials are constant, dropped).
        ll = w * (x * log_lam - lam + y * log_mu - mu)

        # tau correction.
        tau = _tau(x, y, lam, mu, rho)
        tau = np.clip(tau, 1e-10, None)
        ll = ll + w * np.log(tau)

        total = ll.sum() - reg * (np.sum(att**2) + np.sum(dfc**2))

        # ----- gradient -----
        # d ll / d log_lam  and  d ll / d log_mu  (Poisson part).
        g_loglam = w * (x - lam)
        g_logmu = w * (y - mu)

        # tau contribution to those derivatives (only the 2x2 corner).
        dtau_dloglam = np.zeros_like(lam)
        dtau_dlogmu = np.zeros_like(mu)
        dtau_drho = np.zeros_like(lam)

        # (0,0): tau = 1 - lam*mu*rho
        t = tau[m00]
        dtau_dloglam[m00] = (-lam[m00] * mu[m00] * rho) / t
        dtau_dlogmu[m00] = (-lam[m00] * mu[m00] * rho) / t
        dtau_drho[m00] = (-lam[m00] * mu[m00]) / t
        # (0,1): tau = 1 + lam*rho
        t = tau[m01]
        dtau_dloglam[m01] = (lam[m01] * rho) / t
        dtau_drho[m01] = (lam[m01]) / t
        # (1,0): tau = 1 + mu*rho
        t = tau[m10]
        dtau_dlogmu[m10] = (mu[m10] * rho) / t
        dtau_drho[m10] = (mu[m10]) / t
        # (1,1): tau = 1 - rho
        t = tau[m11]
        dtau_drho[m11] = (-1.0) / t

        g_loglam = g_loglam + w * dtau_dloglam
        g_logmu = g_logmu + w * dtau_dlogmu

        grad = np.zeros_like(p)
        # log_lam = home_adv*is_home + att[hi] + dfc[ai]
        np.add.at(grad, hi, g_loglam)                 # d/d att[home]
        np.add.at(grad, nt + ai, g_loglam)            # d/d dfc[away]
        # log_mu = att[ai] + dfc[hi]
        np.add.at(grad, ai, g_logmu)                  # d/d att[away]
        np.add.at(grad, nt + hi, g_logmu)             # d/d dfc[home]
        # home advantage
        grad[2 * nt] = np.sum(g_loglam * is_home)
        # rho
        grad[2 * nt + 1] = np.sum(w * dtau_drho)

        # ridge
        grad[:nt] -= 2 * reg * att
        grad[nt : 2 * nt] -= 2 * reg * dfc

        # We minimise the negative.
        return -total, -grad

    bounds = [(None, None)] * (2 * nt) + [(-1.0, 1.0), (-0.18, 0.18)]
    res = minimize(
        neg_ll_and_grad,
        x0,
        method="L-BFGS-B",
        jac=True,
        bounds=bounds,
        options={"maxiter": 2000, "maxfun": 50000, "ftol": 1e-10, "gtol": 1e-6},
    )
    if verbose:
        print(f"  fit: success={res.success} nll={res.fun:.1f} iters={res.nit}")

    att, dfc, home_adv, rho = unpack(res.x)
    # Re-centre so mean attack == 0 for interpretability.  The model is
    # invariant ONLY to the joint shift (attack += c, defence -= c) because
    # both lambda and mu depend on attack[team] + defence[opponent]; shifting
    # both means independently would rescale every expected-goal value.  So we
    # apply exactly that invariant shift and leave the goal level untouched.
    c = att.mean()
    att = att - c
    dfc = dfc + c

    return DixonColesModel(
        teams=teams,
        attack=att,
        defence=dfc,
        home_adv=float(home_adv),
        rho=float(rho),
        xi=float(xi),
        reg=float(reg),
        trained_until=str(ref_date.date()),
        max_goals=max_goals,
    )
