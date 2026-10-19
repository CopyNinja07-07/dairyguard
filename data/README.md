# Data

All files here were transcribed **by optical character recognition from screen recordings** of ComBase (combase.cc) search results, because the records could not be exported in bulk. They have **not** been checked against the database. Use them as a convenience, not as a reference dataset, and verify any record you rely on at the source.

| File | Content |
|---|---|
| `combase_tasmania_pasteurised_milk.csv` | 51 records of the maximum growth rate of *aerobic total spoilage bacteria* in pasteurised milk, 2.7–14.9 °C (Tasmanian Institute of Agriculture). Result-list position is recorded, not the ComBase record ID. One record with a misread temperature was removed; one outlier is kept in the "all" fit and dropped in the "robust" fit. |
| `combase_milk_full_ocr.csv` | 373 records from the full milk search (result positions 51 onward, about 480 in the list), nearly all for pathogens. Columns: organism, food, temperature, aw, pH, conditions, source, maximum rate, `rate_status` (`value`, `no_growth`, `fit_data_required` = ComBase shows no rate until the user fits the curve, or `unreadable`), and the video frame each record was read from. Rate stated for 179 records. About 40 records near the end of the list and a few elsewhere were not captured. |

Known issues: record IDs are unknown; OCR can misread digits (checked by plausibility only); heterogeneous studies and methods; maximum rates, not curves.


**Not included in this repository.** The raw ComBase transcriptions are kept out of the public repo until ComBase's terms of use for redistribution are confirmed. The fitted outputs (`results_v4_s0/validation*.json`) are included. To rerun the validation scripts, place the two CSV files described above in this folder.
