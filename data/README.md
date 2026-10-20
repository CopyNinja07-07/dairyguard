# Data

| File | Content |
|---|---|
| `params.csv` | Every model parameter, its value, its source, and whether it is sourced from the literature or assumed. |
| `combase_tasmania_pasteurised_milk.csv` | 51 ComBase records of the maximum growth rate of aerobic spoilage bacteria in pasteurised milk, 2.7–14.9 °C (Tasmanian Institute of Agriculture). |
| `combase_milk_full.csv` | 373 ComBase milk records (organism, temperature, aw, pH, conditions, source, maximum rate). A growth rate is stated for 179; the rest need curve fitting and are not used. |

The two ComBase files are not redistributed here; ComBase data are available free at [combase.cc](https://combase.cc). The fitted results are in `results/validation_*.json`. To rerun the validation scripts, place the two CSV files in this folder.
