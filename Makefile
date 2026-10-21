# Reproduce everything. Requires Python 3.10+, the packages in requirements.txt, and (for the PDFs) a LaTeX install.
PY=python3
.PHONY: test runs validate extensions summary figures generated report whitepaper demo all
test:
	@for f in tests/test_*.py; do $(PY) $$f || exit 1; done
runs:   # about three hours on two CPU cores
	DG_PARAMS=ref $(PY) experiments/run_benchmark.py 4000 results/base
	DG_PARAMS=ref DG_SHIFT=0.25 $(PY) experiments/run_benchmark.py 4000 results/lag
	DG_PARAMS=ref DG_N0=low $(PY) experiments/run_benchmark.py 4000 results/low
	DG_PARAMS=comb DG_N0=low $(PY) experiments/run_benchmark.py 4000 results/comb
	DG_PARAMS=lis $(PY) experiments/run_benchmark.py 4000 results/lis
validate:
	$(PY) experiments/validate_lin.py
	$(PY) experiments/validate_combase.py
	$(PY) experiments/validate_combase_lis.py
	$(PY) experiments/compare_secondary.py
	DG_PARAMS=ref $(PY) experiments/example_setting.py
	DG_PARAMS=ref $(PY) experiments/calorimetry_info.py
extensions:   # growth-law study on real ComBase data and further tests of the monitor (a few minutes)
	$(PY) experiments/growth_law_study.py
	DG_PARAMS=ref $(PY) experiments/monitor_studies.py
	$(PY) experiments/extension_figures.py
	$(PY) experiments/readme_animations.py
summary:
	$(PY) experiments/summarize_runs.py
figures:
	cd report && $(PY) figures.py
generated: summary   # numbers, tables and figures shared by the report and the white paper
	$(PY) generated/make_numbers.py
	$(PY) generated/make_tables.py
	$(PY) generated/figures.py
report: figures generated
	cd report && $(PY) cover.py && latexmk -pdf -interaction=nonstopmode main.tex && cp main.pdf ../docs/Beyond-the-4C-Alarm-DairyGuard.pdf
whitepaper: generated
	cd whitepaper && latexmk -pdf -interaction=nonstopmode main.tex && cp main.pdf ../docs/DairyGuard-White-Paper-WP01.pdf
	cd whitepaper && latexmk -pdf -interaction=nonstopmode wp02.tex && cp wp02.pdf ../docs/DairyGuard-White-Paper-WP02.pdf
demo: summary
	cd demo && $(PY) build_web.py
all: test validate extensions summary figures generated report whitepaper demo
