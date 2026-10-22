"""DairyGuard Batch prototype (White Paper WP-02, stages 0, 1 and 2), NumPy and SciPy only. Simulated data only.

What it does
  1. Simulates batches of milk with known hidden biology and the lab data I will collect:
     growth curves at 4, 7, 10 and 15 C, and three day-one tests (initial count, dye time, pH).
  2. Stage 0: fits each batch's hidden state from its curves and checks the fit recovers the truth.
  3. Stage 1: learns the population of batches (mean m, spread Sigma) and shrinks each batch towards it.
  4. Stage 2: learns the encoder: how day-one tests predict a batch's hidden state.
  5. Uses the encoder to judge NEW batches from a temperature log plus day-one tests, and compares
     with a monitor that knows only the population (what DairyGuard Kinetic does).

The link between day-one tests and biology in simulate_tests() is INVENTED so the code can be tested.
Finding the real link is the job of the lab experiments.

Run, from the repository root:  python experiments/batch_prototype.py   (about 7 seconds)
"""
import numpy as np
from scipy.optimize import least_squares, brentq, minimize

LN10 = np.log(10.0)
B0, TMIN = 0.030, -7.7          # population square-root law (Neumeyer 1995)
LIMIT = 3e4                     # FSSAI limit, CFU/mL
NAMES = ["delta", "h0", "log10N0", "log10Nmax"]


# ---------------------------------------------------------------- the kinetic core
def mu_sqrt(T):
    """Population growth rate (1/h, natural-log basis) from the square-root law."""
    T = np.asarray(T, float)
    return np.where(T > TMIN, (B0 * (T - TMIN)) ** 2, 0.0)


def clock(times_h, temps):
    """Generalized time tau(t) = integral of mu(T) dt at each time in times_h.
    The log is a list of readings; each reading is held until the next one."""
    times_h, temps = np.asarray(times_h, float), np.asarray(temps, float)
    dt = np.diff(times_h, prepend=times_h[0])
    rate = np.concatenate([[0.0], mu_sqrt(temps[:-1])])
    return np.cumsum(rate * dt)


def log10_count(tau_pop, z):
    """Baranyi-Roberts count, closed form in generalized time, for a batch with state z.
    tau_pop: population clock; the batch clock runs e^(2 delta) times faster."""
    delta, h0, l0, lmax = z
    tau = np.exp(2 * delta) * np.asarray(tau_pop, float)
    y0, ymax = l0 * LN10, lmax * LN10
    A = tau + np.log(np.exp(-tau) + np.exp(-h0) - np.exp(-tau - h0))
    D = ymax - y0
    # ln(1 + (e^A - 1) / e^D), written so that large A cannot overflow
    y = y0 + A - np.logaddexp(A - D, np.log1p(-np.exp(-D)))
    return y / LN10


# ---------------------------------------------------------------- simulated batches and lab data
M_TRUE = np.array([0.0, 3.8, 1.7, 9.0])
SD_TRUE = np.array([0.25, 0.6, 0.25, 0.2])
CORR = np.eye(4); CORR[0, 1] = CORR[1, 0] = -0.3       # faster batches tend to have shorter lag
SIGMA_TRUE = np.outer(SD_TRUE, SD_TRUE) * CORR
TEMPS = (4.0, 7.0, 10.0, 15.0)
PLATE_SD = 0.2                                        # duplicate plates differ by about 0.2 log10


def sample_times(T):
    """Nine sampling times from 0 to past the plateau at temperature T."""
    end = 1.6 * (3.8 + 17) / mu_sqrt(T)               # past the plateau of a typical batch
    return np.linspace(0, end, 9)                    # 9 samples, the first at time 0


def simulate_batch(rng):
    z = rng.multivariate_normal(M_TRUE, SIGMA_TRUE)
    curves = []
    for T in TEMPS:
        t = sample_times(T)
        tau = mu_sqrt(T) * t
        obs = log10_count(tau, z) + rng.normal(0, PLATE_SD, len(t))
        curves.append((t, np.full(len(t), T), obs))
    return z, curves


def simulate_tests(z, rng):
    """Day-one tests. INVENTED relationship, for testing the code only."""
    delta, h0, l0, lmax = z
    count = l0 + rng.normal(0, 0.15)                          # initial plate count, log10 CFU/mL
    dye = 8.0 - 1.5 * (l0 - 1.7) - 3.0 * delta + rng.normal(0, 0.5)   # dye-reduction time, h
    ph = 6.7 + rng.normal(0, 0.05)                            # pH, unrelated to growth here
    return np.array([count, dye, ph])


# ---------------------------------------------------------------- stage 0: fit one batch
def fit_batch(curves):
    """Least-squares estimate of z from all curves of one batch, with its covariance."""
    tau_all = np.concatenate([clock(t, T) if len(np.unique(T)) > 1 else mu_sqrt(T) * t for t, T, _ in curves])
    obs = np.concatenate([o for _, _, o in curves])

    def res(z):
        return log10_count(tau_all, z) - obs
    start = np.clip([0.0, 3.0, obs.min(), obs.max()], [-1.9, 0.1, -2.9, 5.1], [1.9, 14.9, 5.9, 10.9])
    r = least_squares(res, start,
                      bounds=([-2, 0.05, -3, 5], [2, 15, 6, 11]))
    n, k = len(obs), 4
    s2 = np.sum(r.fun ** 2) / (n - k)                 # plate noise estimated from the residuals
    J = r.jac
    cov = s2 * np.linalg.pinv(J.T @ J)                # covariance of the estimate
    return r.x, cov


# ---------------------------------------------------------------- stages 1 and 2: the population and the encoder
def fit_gaussian(ZH, C, X=None):
    """Fit  z_b ~ N(m + W (x_b - xbar), Sigma)  to the batch estimates ZH, whose own errors have covariance C[b].

    Each estimate is then  zhat_b ~ N(m + W (x_b - xbar), Sigma + C[b]); we choose m, W and Sigma that make the
    estimates most probable (maximum marginal likelihood). Without X this is stage 1 (the population);
    with X it is stage 2 (the encoder). Sigma = L L^T keeps it a valid covariance."""
    nb, k = ZH.shape
    p = 0 if X is None else X.shape[1]
    xbar = np.zeros(p) if X is None else X.mean(0)
    Xc = np.zeros((nb, 0)) if X is None else (X - xbar) / X.std(0)
    il = np.tril_indices(k)

    def unpack(th):
        m = th[:k]
        W = th[k:k + k * p].reshape(k, p)
        L = np.zeros((k, k)); L[il] = th[k + k * p:]
        L[np.diag_indices(k)] = np.exp(L[np.diag_indices(k)])
        return m, W, L @ L.T

    def nll(th):
        m, W, S = unpack(th)
        tot = 0.0
        for b in range(nb):
            V = S + C[b]
            r = ZH[b] - m - W @ Xc[b]
            sign, logdet = np.linalg.slogdet(V)
            tot += 0.5 * (logdet + r @ np.linalg.solve(V, r))
        return tot

    L0 = np.diag(np.log(ZH.std(0) + 1e-3))
    th0 = np.concatenate([ZH.mean(0), np.zeros(k * p), L0[il]])
    res = minimize(nll, th0, method="L-BFGS-B")
    m, W, S = unpack(res.x)
    sd = np.ones(p) if X is None else X.std(0)
    return dict(m=m, W=W / sd, S=S, xbar=xbar)        # W rescaled to the tests' own units


def shrink(zhat, cov, mean, S):
    """Combine a batch's own estimate with the population (partial pooling)."""
    Si, Ci = np.linalg.inv(S), np.linalg.inv(cov)
    post_cov = np.linalg.inv(Si + Ci)
    return post_cov @ (Si @ mean + Ci @ zhat), post_cov


def predict_state(enc, x):
    return enc["m"] + enc["W"] @ (x - enc["xbar"]), enc["S"]


# ---------------------------------------------------------------- judging a trip
def hours_left_at_4C(tau_now, z):
    """Hours the batch can still spend at 4 C before reaching the limit."""
    target = np.log10(LIMIT)
    if log10_count(tau_now, z) >= target:
        return 0.0
    f = lambda h: log10_count(tau_now + mu_sqrt(4.0) * h, z) - target
    if f(5000.0) < 0:                                 # this batch never reaches the limit (counted as 5000 h)
        return 5000.0
    return brentq(f, 0.0, 5000.0)


def judge(times_h, temps, mean, cov, rng, K=200):
    """Probability the limit was crossed and hours left, from K plausible batches drawn from N(mean, cov)."""
    tau_now = clock(times_h, temps)[-1]
    draws = rng.multivariate_normal(mean, cov, K)
    over = np.array([log10_count(tau_now, z) >= np.log10(LIMIT) for z in draws])
    left = np.array([hours_left_at_4C(tau_now, z) for z in draws])
    return over.mean(), np.median(left), np.percentile(left, 10)


def a_trip():
    """40 h at 4 C, 3 h at 15 C, 10 h at 4 C, one reading every 15 minutes."""
    T = np.r_[np.full(160, 4.0), np.full(12, 15.0), np.full(40, 4.0)]
    return np.arange(len(T)) * 0.25, T


# ---------------------------------------------------------------- run everything
def main(n_train=30, n_test=200, seed=1):
    rng = np.random.default_rng(seed)

    # stage 0 on training batches
    Z, ZH, C, X = [], [], [], []
    for _ in range(n_train):
        z, curves = simulate_batch(rng)
        zh, cov = fit_batch(curves)
        Z.append(z); ZH.append(zh); C.append(cov); X.append(simulate_tests(z, rng))
    Z, ZH, C, X = map(np.array, (Z, ZH, C, X))
    inside = np.abs(ZH - Z) <= 1.645 * np.sqrt(np.einsum("bii->bi", C))
    print("Stage 0: share of true values inside the 90% interval, per parameter")
    for nm, v in zip(NAMES, inside.mean(0)):
        print(f"   {nm:10s} {v:.2f}")

    # stage 1
    pop = fit_gaussian(ZH, C)
    m, S = pop["m"], pop["S"]
    print("\nStage 1: population mean (true in brackets)")
    for nm, a, b in zip(NAMES, m, M_TRUE):
        print(f"   {nm:10s} {a:6.2f}  ({b:.2f})")
    print("   spread (SD):", np.round(np.sqrt(np.diag(S)), 2), " true:", SD_TRUE)

    # stage 2
    enc = fit_gaussian(ZH, C, X)
    print("\nStage 2: encoder weights W (rows: delta, h0, log10N0, log10Nmax; columns: count, dye, pH)")
    print(np.round(enc["W"], 2))
    explained = 1 - np.diag(enc["S"]) / np.diag(S)
    print("   share of each parameter's spread explained by the tests:", np.round(np.clip(explained, 0, 1), 2))

    # judge new batches: population only (like Kinetic) vs with day-one tests
    t, T = a_trip()
    tau_now = clock(t, T)[-1]
    err_pop, err_enc, cov_pop, cov_enc = [], [], [], []
    for _ in range(n_test):
        z, _ = simulate_batch(rng)
        x = simulate_tests(z, rng)
        truth = hours_left_at_4C(tau_now, z)
        _, med_p, lo_p = judge(t, T, m, S, rng, K=100)
        mean_e, cov_e = predict_state(enc, x)
        _, med_e, lo_e = judge(t, T, mean_e, cov_e, rng, K=100)
        err_pop.append(abs(med_p - truth)); err_enc.append(abs(med_e - truth))
        cov_pop.append(truth >= lo_p); cov_enc.append(truth >= lo_e)
    print(f"\nNew batches, one trip ({n_test} batches):")
    print(f"   median error of hours left, population only : {np.median(err_pop):6.1f} h")
    print(f"   median error of hours left, with day-one tests: {np.median(err_enc):6.1f} h")
    print(f"   cautious value safe (truth >= cautious): population {np.mean(cov_pop):.2f}, with tests {np.mean(cov_enc):.2f}")


if __name__ == "__main__":
    main()
