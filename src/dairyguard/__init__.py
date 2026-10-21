"""DairyGuard: what a temperature log can and cannot tell about spoiling milk.

Main entry points
    ColdChainMonitor   judge a batch from its temperature log (shelf life used, probability, hours left)
    sl_gompertz        time to the limit at a steady temperature
    mu_sqrt            growth rate from the square-root law
    growthlaws         secondary models, including a monotone neural network, and their validation tools
"""
__version__ = "2026.10"

from .kinetics import mu_sqrt, sl_gompertz, make_sl_lookup, LN10
from .monitor import ColdChainMonitor, Status, summarise_log
from .products import PRODUCTS, Product
from . import growthlaws

__all__ = ["ColdChainMonitor", "Status", "summarise_log", "PRODUCTS", "Product", "mu_sqrt", "sl_gompertz",
           "make_sl_lookup", "LN10", "growthlaws", "__version__"]
