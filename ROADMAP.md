# DairyGuard roadmap

DairyGuard grows in stops. Each one ends in something finished and public. A journal paper comes last, once real laboratory results stand.

| When | Stop | Output | Status |
|---|---|---|---|
| October 2026 | The case is opened | DairyGuard Kinetic, 240,000 simulated deliveries, Technical Report TR-01, website and demo | Done |
| November 2026 | The plan is written | White Paper WP-01; PyTorch prototype checked on curves simulated by DairyGuard Kinetic | In progress |
| December 2026 | Learning from real curves | Neural growth law trained on ComBase growth curves on a Colab GPU, compared with the square-root law | Next |
| January 2027 | Into the lab | Experiments E1 and E2: milk at steady and changing temperatures, counted on plates | Planned |
| February 2027 | DairyGuard Neural | First trained model, held-out evaluation, live in the demo; Technical Report TR-02 | Planned |
| Spring 2027 | The three questions | Experiments E3 (batches with cheap tests) and E4 (calorimetry with a partner lab) | Planned |
| After that | A paper | Peer-reviewed paper built on the laboratory results | Planned |

Technical reports and white papers are not peer reviewed. Each says so on its first page.

## DairyGuard Neural in one paragraph

DairyGuard Kinetic shows, in simulation, that the biggest limit on predicting spoilage from a temperature log is the biology the log cannot see. DairyGuard Neural keeps the proven generalized-time core and adds three learned parts: a monotone neural growth law fitted to real growth curves, small residual networks that show where real bacteria depart from the Baranyi–Roberts equations after a temperature shift, and an encoder that turns cheap tests at loading into a probability range for each batch's hidden biology. It is trained by maximising an evidence lower bound through an adaptive ODE solver in PyTorch. The full design is in [White Paper WP-01](docs/DairyGuard-White-Paper-WP01.pdf).

## The three research questions

1. **Does real milk run on one biological clock?** If real growth curves collapse on generalized time, one isothermal or calorimetric test can stand in for a whole temperature study. If not, the residual networks show exactly which temperature shifts break it.
2. **Which cheap test buys the most accuracy?** Dye reduction, an initial plate count, pH and a calorimetric detection time, ranked by AUC and calibration gained per rupee.
3. **Do chilled foods share a common hidden biology?** Whether the latent space learned on milk transfers to meat, fish and ready-to-eat foods in ComBase.

## Data and laboratories needed

| Need | Why | Where |
|---|---|---|
| ComBase growth curves (counts against time) | Train the growth law and the residuals on real data | Public, [combase.cc](https://www.combase.cc) |
| Published fluctuating-temperature studies | Test against real temperature shifts | Literature; authors contacted for raw counts |
| Microbiology lab: incubators, autoclave, laminar flow, plate count agar | Experiments E1 to E3, about 300 to 400 plate counts (ISO 4833-1, ISO 17410) | University laboratory |
| Microplate reader (optional) | Dye-reduction kinetics in many wells at once | University laboratory |
| Isothermal microcalorimeter | Experiment E4: test the calorimetric master curve on real milk | Partner laboratory |

## Rules fixed in advance

- Training, validation and test data are split by study and by batch before results are looked at.
- Baselines: DairyGuard Kinetic, a classical Baranyi–Roberts fit, and a black-box recurrent network of similar size.
- Every result is reported on real data the model has not seen. Results on simulated data are labelled as simulation.
- "Crossing the limit" means the bacterial count passed a stated limit. It is not a safety verdict.
- Every number in a report is generated from result files by script.

## Open tasks

- [x] Unit audit: ComBase rates converted from log10 to natural-log units before fitting (test added)
- [x] Headline numbers pinned by regression tests
- [ ] ComBase growth-curve pipeline
- [ ] PyTorch prototype recovers known parameters from simulated curves
- [ ] Monotone neural growth law trained on ComBase
- [ ] Logistic-regression probability baseline and correlated-parameter sensitivity run for TR-02
- [ ] Laboratory protocol for E1 and E2 written and agreed with a lab

## Help

Have growth data, a microbiology lab or a calorimeter? Open an issue with the "Offer data or lab access" form.
