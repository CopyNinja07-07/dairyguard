"""The DairyGuard Kinetic monitor: what runs on a logger or a server as temperature readings arrive.

For every reading the monitor adds the fraction of shelf life used, dt / SL(T), for the textbook batch and for
`n_draws` plausible batches drawn from the product's between-batch spread. From these it reports
  * shelf life used by a textbook batch (CSL; 1.0 means the limit is predicted to be reached),
  * the probability that this batch has crossed the limit (share of plausible batches with CSL >= 1),
  * the hours left if the product is now held at 4 deg C: a typical value and a cautious one that 9 batches in 10
    would reach, which is the number to plan sales against,
  * a plain-language state.

Example
    >>> from dairyguard import ColdChainMonitor
    >>> m = ColdChainMonitor("milk")
    >>> for T in [4.0] * 160 + [17.5] * 8 + [4.0] * 40:        # one reading every 15 minutes
    ...     s = m.update(T, 0.25)
    >>> round(s.shelf_life_used, 2), round(s.probability_crossed, 2)
"""
from dataclasses import dataclass, asdict
import numpy as np

from .kinetics import sl_gompertz
from .products import get as get_product

STATES = ((0.15, "fresh"), (0.40, "use soon"), (0.75, "check before use"), (1.01, "likely over the limit"))


@dataclass
class Status:
    hours: float
    temperature: float
    shelf_life_used: float
    probability_crossed: float
    hours_left_at_4C: float
    hours_left_at_4C_cautious: float
    state: str

    def as_dict(self):
        return asdict(self)


def plain_state(p):
    for edge, label in STATES:
        if p < edge:
            return label
    return STATES[-1][1]


class ColdChainMonitor:
    def __init__(self, product="milk", n_draws=200, seed=0):
        self.product = get_product(product) if isinstance(product, str) else product
        p, rng = self.product, np.random.default_rng(seed)
        k = n_draws
        self.draws = dict(
            b=p.b * np.exp(rng.normal(0, p.cv_b, k) - p.cv_b ** 2 / 2),
            Tmin=p.Tmin + rng.normal(0, p.Tmin_sd, k),
            h0=rng.uniform(*p.h0_range, k),
            log10N0=rng.uniform(*p.log10N0_range, k))
        self.reset()

    def _sl(self, T):
        p, d = self.product, self.draws
        nominal = float(sl_gompertz(np.array(T, float), p.b, p.Tmin, p.h0, p.log10N0, p.log10Nmax, p.limit))
        each = sl_gompertz(np.full(len(d["b"]), float(T)), d["b"], d["Tmin"], d["h0"], d["log10N0"], p.log10Nmax, p.limit)
        return nominal, each

    def reset(self):
        self.hours, self.csl, self.csl_each, self.last_T = 0.0, 0.0, np.zeros(len(self.draws["b"])), np.nan
        self._sl4 = self._sl(4.0)

    def update(self, temperature, dt_hours):
        """Add one reading held for dt_hours. Returns the new Status."""
        nominal, each = self._sl(temperature)
        self.csl += dt_hours / nominal
        self.csl_each += dt_hours / each
        self.hours += dt_hours
        self.last_T = float(temperature)
        return self.status()

    def status(self):
        p_cross = float((self.csl_each >= 1.0).mean())
        left = np.maximum(1.0 - self.csl_each, 0.0) * self._sl4[1]
        return Status(hours=round(self.hours, 4), temperature=self.last_T, shelf_life_used=float(self.csl),
                      probability_crossed=p_cross, hours_left_at_4C=float(np.median(left)),
                      hours_left_at_4C_cautious=float(np.percentile(left, 10)), state=plain_state(p_cross))

    def run(self, times_h, temps):
        """Feed a whole log. Each reading is held until the next one (as a logger does). Returns the statuses."""
        times_h, temps = np.asarray(times_h, float), np.asarray(temps, float)
        self.reset()
        dts = np.diff(times_h, append=times_h[-1] + (np.median(np.diff(times_h)) if len(times_h) > 1 else 0.25))
        return [self.update(T, dt) for T, dt in zip(temps, dts)]


def summarise_log(times_h, temps):
    """Simple facts about a log that a quality manager would also want to see."""
    times_h, temps = np.asarray(times_h, float), np.asarray(temps, float)
    dts = np.diff(times_h, append=times_h[-1] + (np.median(np.diff(times_h)) if len(times_h) > 1 else 0.25))
    above = temps > 8.0
    starts = int(np.sum(above[1:] & ~above[:-1]) + (1 if above[0] else 0))
    return dict(duration_h=float(dts.sum()), readings=int(len(temps)), max_temp_C=float(temps.max()),
                mean_temp_C=float(np.average(temps, weights=dts)), hours_above_5C=float(dts[temps > 5].sum()),
                hours_above_8C=float(dts[above].sum()), warm_events_above_8C=starts,
                degree_hours_above_4C=float(np.sum(np.maximum(temps - 4.0, 0) * dts)))
