# DairyGuard roadmap

DairyGuard grows in stages. Each stage ends in something finished and public. The journal paper comes last, once real milk has been measured.

| Stage | What it delivers | Target | Status |
|---|---|---|---|
| 0. Models v1 and v2 | Loss budget, kinetic theory, 240,000 simulated trips, website and demo | October 2026 | Done |
| 1. Report 1: Framework | The idea and the mathematics as a technical report | December 2026 | In progress |
| 2. Report 2: Model v3 | Hybrid model and its code release, corrected benchmark, new baselines | February 2027 | Next |
| 3. Report 3: Validation | Model v3 tested on real published growth data it was not fitted to | March 2027 | Planned |
| 4. Experiment and paper | Milk counted at steady and changing temperatures, then a peer-reviewed paper | 2027 | Planned |

Technical reports are not peer reviewed. Each one will say so on its first page.

## Model v3 in one paragraph

Model v2 shows that the biggest limit on predicting spoilage from a temperature log is the biology the log cannot see: how many bacteria were in the milk, which ones, and how long they wait before growing. Model v3 keeps the proven physics core (generalized time) and adds two learned parts: a growth law fitted to real growth records, and an estimator that turns a cheap test of the milk at loading into a range for the hidden biology. Its output is a probability of crossing the limit and a remaining shelf life with an uncertainty band.

The research question: **which cheap test at loading buys the most accuracy?** Candidates are a dye-reduction test, an initial plate count and a calorimetric detection time.

## Rules the project keeps

- Every result is reported on real data the model was not fitted to. Results from the simulator alone are labelled as simulation.
- Fitting data and held-out data are chosen before results are looked at.
- "Spoiled" means the bacterial count crossed a stated limit. It is not a safety verdict.
- Every number in a report is generated from the result files by script.

## Open tasks

- [ ] Unit audit: growth rates in log10 and natural-log units used consistently (test added)
- [ ] Probability baseline: a logistic model on temperature features, to compare with the Monte Carlo probability
- [ ] Sensitivity run with correlated biological parameters
- [ ] Collect open real growth data at changing temperatures
- [ ] Learned growth law (model v3, part 1)
- [ ] Biology estimator (model v3, part 2)

## Help

Have growth data or a lab? Open an issue with the "Offer data or lab access" form.
