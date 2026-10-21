"""Secondary models: how the maximum growth rate depends on temperature.

Every law here predicts the natural-log growth rate mu (1/h) from temperature T (deg C) and is fitted by least
squares on ln(mu), the usual choice because the error of a growth rate is roughly proportional to its size.

    SquareRoot   sqrt(mu) = b (T - Tmin)                         Ratkowsky et al. 1982
    Arrhenius    ln mu = ln A - Ea / (R T_K)
    Exponential  ln mu = a + c T            (constant Q10 = exp(10 c))
    Davey        ln mu = C0 + C1 / T_K + C2 / T_K^2               Davey 1989
    MonotoneNet  sqrt(mu) = sum_k exp(u_k) softplus(exp(v_k) (T - c_k))   a small neural network that can only rise
                 with temperature; trained as an ensemble of independent fits.

All laws share one interface: law.fit(T, mu) returns the fitted law; law.predict(T) returns mu.
Rates reported in log10 units (ComBase) must be multiplied by ln(10) before fitting; see to_ln_rate().
"""
import numpy as np
from scipy.optimize import least_squares

R_GAS = 8.314
LN10 = np.log(10.0)


def to_ln_rate(mu_log10):
    """Convert a growth rate in log10 units per hour (as ComBase reports it) to the natural-log rate mu."""
    return np.asarray(mu_log10, float) * LN10


def softplus(x):
    return np.logaddexp(0.0, x)


class GrowthLaw:
    name = "law"
    n_params = 0

    def fit(self, T, mu):
        raise NotImplementedError

    def predict(self, T):
        raise NotImplementedError

    def residuals(self, T, mu):
        """ln(predicted) - ln(observed)."""
        return np.log(np.maximum(self.predict(T), 1e-12)) - np.log(mu)


class SquareRoot(GrowthLaw):
    name, n_params = "square-root", 2

    def fit(self, T, mu):
        T, mu = np.asarray(T, float), np.asarray(mu, float)
        b0, c0 = np.polyfit(T, np.sqrt(mu), 1)
        x0 = [max(b0, 1e-3), min(-c0 / b0 if b0 > 0 else -5.0, T.min() - 0.5)]

        def res(p):
            b, tmin = p
            return np.log(np.maximum((b * np.maximum(T - tmin, 1e-6)) ** 2, 1e-12)) - np.log(mu)
        r = least_squares(res, x0, bounds=([1e-5, -40.0], [1.0, T.min() - 1e-3]))
        self.b, self.Tmin = r.x
        return self

    def predict(self, T):
        T = np.asarray(T, float)
        return np.where(T > self.Tmin, (self.b * (T - self.Tmin)) ** 2, 0.0)


class Arrhenius(GrowthLaw):
    name, n_params = "Arrhenius", 2

    def fit(self, T, mu):
        x = 1.0 / (np.asarray(T, float) + 273.15)
        slope, icpt = np.polyfit(x, np.log(mu), 1)
        self.lnA, self.Ea = icpt, -slope * R_GAS
        return self

    def predict(self, T):
        return np.exp(self.lnA - self.Ea / (R_GAS * (np.asarray(T, float) + 273.15)))


class Exponential(GrowthLaw):
    name, n_params = "Q10 (exponential)", 2

    def fit(self, T, mu):
        self.c, self.a = np.polyfit(np.asarray(T, float), np.log(mu), 1)
        self.Q10 = float(np.exp(10 * self.c))
        return self

    def predict(self, T):
        return np.exp(self.a + self.c * np.asarray(T, float))


class Davey(GrowthLaw):
    name, n_params = "Davey", 3

    def fit(self, T, mu):
        x = 1.0 / (np.asarray(T, float) + 273.15)
        self.coef = np.polyfit(x, np.log(mu), 2)
        return self

    def predict(self, T):
        x = 1.0 / (np.asarray(T, float) + 273.15)
        return np.exp(np.polyval(self.coef, x))


class MonotoneNet(GrowthLaw):
    """A small neural network for sqrt(mu) that is increasing in T by construction.

    sqrt(mu)(T) = sum_k exp(u_k) * softplus(exp(v_k) * (T - c_k) / s)
    Positive output weights (exp) and positive input weights (exp) make every unit, and so the sum, increasing.
    Temperatures are scaled by s = 10 K. An L2 penalty on (u, v) keeps the fit smooth. An ensemble of independently
    initialised fits gives both the prediction (geometric mean) and its spread."""
    name = "monotone neural net"

    def __init__(self, units=4, ensemble=5, penalty=1e-3, seed=0):
        self.units, self.ensemble, self.penalty, self.seed = units, ensemble, penalty, seed
        self.n_params = 3 * units

    @staticmethod
    def _sqrt_mu(p, T, units):
        u, v, c = p[:units], p[units:2 * units], p[2 * units:]
        z = np.exp(v)[None, :] * (np.asarray(T, float)[:, None] - c[None, :]) / 10.0
        return (np.exp(u)[None, :] * softplus(z)).sum(1)

    def fit(self, T, mu):
        T, mu = np.asarray(T, float), np.asarray(mu, float)
        rng = np.random.default_rng(self.seed)
        k = self.units
        scale = np.sqrt(mu).mean() / k
        self.members = []
        for _ in range(self.ensemble):
            x0 = np.concatenate([np.log(scale) + rng.normal(0, .3, k), rng.normal(0, .3, k),
                                 rng.uniform(T.min() - 15, T.max(), k)])

            def res(p):
                pred = np.maximum(self._sqrt_mu(p, T, k), 1e-9)
                fit = 2 * np.log(pred) - np.log(mu)
                return np.concatenate([fit, np.sqrt(self.penalty) * np.concatenate([p[:k] - np.log(scale), p[k:2 * k]])])
            r = least_squares(res, x0, max_nfev=4000)
            self.members.append(r.x)
        return self

    def predict_members(self, T):
        return np.array([self._sqrt_mu(p, T, self.units) ** 2 for p in self.members])

    def predict(self, T):
        m = np.maximum(self.predict_members(T), 1e-12)
        return np.exp(np.log(m).mean(0))

    def spread(self, T):
        """Standard deviation of ln(mu) across ensemble members: the network's own uncertainty."""
        return np.log(np.maximum(self.predict_members(T), 1e-12)).std(0)


LAWS = {"square-root": SquareRoot, "Arrhenius": Arrhenius, "Q10": Exponential, "Davey": Davey,
        "neural": MonotoneNet}


def performance(pred, obs):
    """Bias factor, accuracy factor (Ross 1996) and RMSE of ln(mu)."""
    r = np.log10(np.asarray(pred) / np.asarray(obs))
    return dict(Bf=float(10 ** r.mean()), Af=float(10 ** np.abs(r).mean()),
                rmse_ln=float(np.sqrt(np.mean((np.log(pred) - np.log(obs)) ** 2))))


def aicc(law, T, mu):
    n, k = len(T), law.n_params + 1
    rss = float(np.sum(law.residuals(T, mu) ** 2))
    return n * np.log(rss / n) + 2 * k + 2 * k * (k + 1) / max(n - k - 1, 1)


def leave_one_group_out(make_law, T, mu, groups):
    """Fit on all groups but one, predict the held-out group. Returns out-of-group predictions."""
    T, mu, groups = np.asarray(T, float), np.asarray(mu, float), np.asarray(groups)
    pred = np.full(len(T), np.nan)
    for g in np.unique(groups):
        test = groups == g
        law = make_law().fit(T[~test], mu[~test])
        pred[test] = law.predict(T[test])
    return pred


def between_study_variation(T, mu, groups, min_records=3):
    """How much growth rates differ between studies at the same temperature.

    Fits the square-root law with one shared Tmin and a separate slope b_s for every study with at least
    `min_records` records, then reports the spread of ln(b_s) as a coefficient of variation of b. This is the real-data
    counterpart of the strain variability that the benchmark has to assume."""
    T, mu, groups = np.asarray(T, float), np.asarray(mu, float), np.asarray(groups)
    keep = np.isin(groups, [g for g in np.unique(groups) if (groups == g).sum() >= min_records])
    T, mu, groups = T[keep], mu[keep], groups[keep]
    ids = {g: i for i, g in enumerate(np.unique(groups))}
    gi = np.array([ids[g] for g in groups])
    base = SquareRoot().fit(T, mu)
    x0 = np.concatenate([[base.Tmin], np.full(len(ids), np.log(base.b))])

    def res(p):
        tmin, lb = p[0], p[1:]
        return np.log(np.maximum((np.exp(lb[gi]) * np.maximum(T - tmin, 1e-6)) ** 2, 1e-12)) - np.log(mu)
    r = least_squares(res, x0)
    lb = r.x[1:]
    within = float(np.sqrt(np.mean(r.fun ** 2)))
    return dict(n_studies=len(ids), n_records=int(len(T)), Tmin=float(r.x[0]), b_median=float(np.exp(np.median(lb))),
                cv_b=float(np.std(lb, ddof=1)), within_study_rmse_ln=within,
                study_b={g: float(np.exp(lb[i])) for g, i in ids.items()})
