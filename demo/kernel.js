// DairyGuard kinetic kernel (JS port of src/dg_kinetics.py). Growth slope, Tmin and lag from Neumeyer 1995 and Lin 2016; starting load assumed. See params.csv.
const LN10 = Math.log(10);
const P = { b: 0.030, Tmin: -7.7, h0: 3.8, logN0: 1.7, logNmax: 9.0 };
function muSqrt(T, b = P.b, Tmin = P.Tmin) { return T > Tmin ? Math.pow(b * (T - Tmin), 2) : 0; }
function slGompertz(T, Nlim, p = P) {
  const mu = Math.max(muSqrt(T, p.b, p.Tmin), 1e-9), mu10 = mu / LN10;
  const A = p.logNmax - p.logN0, L = Math.log10(Nlim) - p.logN0, lam = p.h0 / mu;
  return lam + A / (mu10 * Math.E) * (1 - Math.log(-Math.log(L / A)));
}
// Baranyi-Roberts reference (truth model): returns log10 N trajectory for a temperature series (1-min steps)
function baranyiTrajectory(Tseries, p = P, dtH = 1 / 60) {
  let y = p.logN0 * LN10; const ymax = p.logNmax * LN10; let q = 1 / (Math.exp(p.h0) - 1);
  const out = new Float64Array(Tseries.length);
  for (let i = 0; i < Tseries.length; i++) {
    const mu = muSqrt(Tseries[i], p.b, p.Tmin), a = q / (1 + q);
    y += dtH * mu * a * (1 - Math.exp(y - ymax)); q += dtH * mu * q; out[i] = y / LN10;
  }
  return out;
}
function cslSeries(Tseries, Nlim, dtH = 1 / 60) {
  const out = new Float64Array(Tseries.length); let c = 0;
  for (let i = 0; i < Tseries.length; i++) { c += dtH / slGompertz(Tseries[i], Nlim); out[i] = c; }
  return out;
}
if (typeof module !== 'undefined') module.exports = { P, muSqrt, slGompertz, baranyiTrajectory, cslSeries };
