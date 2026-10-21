# DairyGuard roadmap

Each stop ends in something finished and public. A journal paper comes last, once laboratory results stand.

| When | Stop | Output | Status |
|---|---|---|---|
| October 2026 | DairyGuard Kinetic | Python package and command line, ESP32 firmware, browser app, 240,000 simulated deliveries, the book, the architecture white paper (WP-01) and the blueprint of the next model (WP-02) | Done |
| October 2026 | Real-data checks | Five growth laws on 20 unseen *Listeria* studies, between-study spread from 11 studies, monitor against a trained model | Done |
| November to December 2026 | Curves and protocol | A pipeline for complete ComBase growth curves (counts against time), and a written lab protocol for milk at steady and changing temperatures | In progress |
| January to February 2027 | First lab measurements | Plate counts of milk at steady and shifting temperatures, with simple batch tests on the first day | Planned |
| After that | DairyGuard Batch | Built to the WP-02 blueprint and evaluated on locked test batches | Planned |
| After that | Peer review | A journal paper built on the laboratory results | Planned |

## Why the next model is needed

DairyGuard Kinetic's own results set the direction:

- Real growth rates differ between studies by about 25%. That is biology a temperature log cannot see.
- A flexible neural growth law fitted to growth rates alone predicts unseen studies no better than the square-root law. More data of the same kind will not close the gap.
- In simulation, one measurement of the batch itself closes most of the gap.

So the next step is better data, not a bigger formula: complete growth curves of real milk under changing temperatures, and cheap tests of each batch at loading. The model that will use them, DairyGuard Batch, is designed in [White Paper WP-02](docs/DairyGuard-White-Paper-WP02.pdf), with its pass-or-fail tests fixed in advance.

## Rules fixed in advance

- Data are split by study and by batch before any result is looked at.
- Every new model is compared with DairyGuard Kinetic on the same unseen data.
- Results on simulated data are labelled as simulation.
- "Crossing the limit" means the bacterial count passed a stated limit. It is not a safety verdict.
- Every number in a report is written from result files by script.

## Open tasks

- [x] Unit audit: ComBase rates converted from log10 to natural-log units before fitting
- [x] Headline numbers pinned by tests
- [x] Growth laws compared on held-out studies
- [x] Monitor compared with a trained logistic model; Monte Carlo size and correlated biology checked
- [x] Firmware tested against the Python monitor
- [ ] ComBase growth-curve pipeline
- [ ] Lab protocol for steady and shifting temperatures, agreed with a lab
- [ ] First plate counts

## Data and laboratories needed

| Need | Why |
|---|---|
| Growth curves of milk or chilled food under changing temperatures | train and test the next model on real dynamics |
| Microbiology lab: incubators, laminar flow, plate count agar | about 300 to 400 plate counts (ISO 4833-1) |
| Isothermal microcalorimeter | test the heat-flow result on real milk |

Have growth data or a lab? Open an issue with the "Offer data or lab access" form.
