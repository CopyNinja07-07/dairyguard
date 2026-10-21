"""Product presets: the growth parameters and limit for each kind of chilled product the monitor knows.

Each preset gives the nominal biology (square-root slope b, minimum temperature Tmin, lag parameter h0, starting count
and maximum count, all on the natural-log basis) and the spread of that biology between batches, used to turn a
temperature log into a probability. Sources are listed in data/params.csv.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Product:
    name: str
    description: str
    b: float                    # square-root slope, h^-1/2 K^-1
    Tmin: float                 # notional minimum growth temperature, deg C
    h0: float                   # lag parameter (lag x rate), dimensionless
    log10N0: float              # nominal starting count, log10 CFU/mL
    log10Nmax: float            # maximum population density, log10 CFU/mL
    limit: float                # the limit judged against, CFU/mL
    limit_label: str
    cv_b: float = 0.10          # between-batch coefficient of variation of b
    Tmin_sd: float = 1.5        # between-batch SD of Tmin, K
    h0_range: tuple = (2.5, 5.0)
    log10N0_range: tuple = (1.5, 2.0)
    sources: tuple = field(default_factory=tuple)


PRODUCTS = {
    "milk": Product(
        "milk", "Pasteurised milk, psychrotrophic spoilage flora (literature parameters)",
        b=0.030, Tmin=-7.7, h0=3.8, log10N0=1.7, log10Nmax=9.0, limit=3e4,
        limit_label="FSSAI aerobic plate count limit for pasteurised milk, 3 x 10^4 CFU/mL",
        sources=("Neumeyer 1995", "Lin et al. 2016", "FSSAI 2024")),
    "milk-combase": Product(
        "milk-combase", "Pasteurised milk, natural spoilage flora fitted to ComBase records",
        b=0.0256, Tmin=-6.6, h0=3.8, log10N0=1.7, log10Nmax=9.0, limit=3e4,
        limit_label="FSSAI aerobic plate count limit for pasteurised milk, 3 x 10^4 CFU/mL",
        sources=("ComBase, Tasmanian Institute of Agriculture records",)),
    "listeria": Product(
        "listeria", "Listeria monocytogenes in milk, growth only (no illness modelled)",
        b=0.0235, Tmin=-2.3, h0=3.0, log10N0=-1.0, log10Nmax=9.0, limit=10 ** 0.0,
        limit_label="tenfold growth over the starting count (+1 log10); a modelling target, not a legal limit",
        Tmin_sd=1.0, h0_range=(2.0, 4.5), log10N0_range=(-1.25, -0.75),
        sources=("ComBase Listeria records in milk",)),
}


def get(name):
    try:
        return PRODUCTS[name]
    except KeyError:
        raise KeyError(f"unknown product {name!r}; choose from {', '.join(PRODUCTS)}") from None
