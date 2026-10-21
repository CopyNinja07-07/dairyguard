"""Command-line interface.

    dairyguard assess trip.csv [--product milk] [--json]     read a temperature log and judge the batch
    dairyguard shelf-life [--product milk] [--temps 2 4 8]   time to the limit at steady temperatures
    dairyguard products                                      list the product presets
"""
import argparse
import json
import sys

import numpy as np

from . import __version__
from .io import read_log
from .kinetics import sl_gompertz
from .monitor import ColdChainMonitor, summarise_log
from .products import PRODUCTS, get


def _bar(x, width=24):
    n = int(round(min(max(x, 0), 1) * width))
    return "#" * n + "." * (width - n)


def cmd_assess(a):
    t, T = read_log(a.log)
    m = ColdChainMonitor(a.product, n_draws=a.draws, seed=a.seed)
    s = m.run(t, T)[-1]
    facts = summarise_log(t, T)
    out = dict(product=m.product.name, limit=m.product.limit_label, **s.as_dict(), log=facts)
    if a.json:
        print(json.dumps(out, indent=2))
        return 0
    p = m.product
    print(f"DairyGuard Kinetic {__version__}  |  {p.description}")
    print(f"Log: {facts['readings']} readings over {facts['duration_h']:.1f} h, max {facts['max_temp_C']:.1f} C, "
          f"{facts['hours_above_8C']:.1f} h above 8 C in {facts['warm_events_above_8C']} warm event(s)")
    print()
    print(f"  Shelf life used (textbook batch)  {s.shelf_life_used * 100:6.0f} %   [{_bar(s.shelf_life_used)}]")
    print(f"  Chance it crossed the limit       {s.probability_crossed * 100:6.0f} %   [{_bar(s.probability_crossed)}]")
    print(f"  Hours left if held at 4 C         {s.hours_left_at_4C:6.0f} h   (typical batch)")
    print(f"  Hours left, cautious              {s.hours_left_at_4C_cautious:6.0f} h   (9 batches in 10 reach this)")
    print()
    print(f"  Verdict: {s.state.upper()}")
    print(f"  Limit: {p.limit_label}")
    return 0


def cmd_shelf_life(a):
    p = get(a.product)
    print(f"Time to the limit at steady temperature  |  {p.description}")
    for T in a.temps:
        h = float(sl_gompertz(np.array(T), p.b, p.Tmin, p.h0, p.log10N0, p.log10Nmax, p.limit))
        print(f"  {T:5.1f} C   {h:7.1f} h   ({h / 24:4.1f} days)")
    return 0


def cmd_products(a):
    for k, p in PRODUCTS.items():
        print(f"{k:14s} {p.description}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="dairyguard", description="Judge chilled products from their temperature log.")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("assess", help="read a temperature log and judge the batch")
    s.add_argument("log", help="CSV file with a time column and a temperature column")
    s.add_argument("--product", default="milk", choices=list(PRODUCTS))
    s.add_argument("--draws", type=int, default=200, help="plausible batches used for the probability")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--json", action="store_true", help="print machine-readable output")
    s.set_defaults(fn=cmd_assess)
    s = sub.add_parser("shelf-life", help="time to the limit at steady temperatures")
    s.add_argument("--product", default="milk", choices=list(PRODUCTS))
    s.add_argument("--temps", type=float, nargs="+", default=[2, 4, 6, 8, 10, 12, 15])
    s.set_defaults(fn=cmd_shelf_life)
    s = sub.add_parser("products", help="list the product presets")
    s.set_defaults(fn=cmd_products)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
