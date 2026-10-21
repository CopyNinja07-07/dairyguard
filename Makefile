# Reproduce everything. Requires Python 3.10+, the packages in requirements.txt, and (for the PDFs) a LaTeX install.
PY=python3
.PHONY: test runs validate summary figures generated report whitepaper demo all
test:
	@for f in tests/test_*.py; do $(PY) $$f || exit 1; done
runs:   # about three hours on two CPU cores
	DG_PARAMS=ref $(PY) src/benchmark.py 4000 results/base
	DG_PARAMS=ref DG_SHIFT=0.25 $(PY) src/benchmark.py 4000 results/lag
	DG_PARAMS=ref DG_N0=low $(PY) src/benchmark.py 4000 results/low
	DG_PARAMS=comb DG_N0=low $(PY) src/benchmark.py 4000 results/comb
	DG_PARAMS=lis $(PY) src/benchmark.py 4000 results/lis
validate:
	$(PY) src/validate_lin.py
	$(PY) src/validate_combase.py
	$(PY) src/validate_combase_lis.py
	$(PY) src/compare_secondary.py
	DG_PARAMS=ref $(PY) src/example_setting.py
	DG_PARAMS=ref $(PY) src/calorimetry_info.py
summary:
	$(PY) src/summarize_runs.py
figures:
	cd report && $(PY) figures.py
generated: summary   # numbers, tables and figures shared by the report and the white paper
	$(PY) generated/make_numbers.py
	$(PY) generated/make_tables.py
	$(PY) generated/figures.py
report: figures generated
	cd report && $(PY) cover.py && latexmk -pdf -interaction=nonstopmode main.tex && cp main.pdf ../docs/DairyGuard-Technical-Report-TR01.pdf
whitepaper: generated
	cd whitepaper && latexmk -pdf -interaction=nonstopmode main.tex && cp main.pdf ../docs/DairyGuard-White-Paper-WP01.pdf
demo: summary
	cd demo && $(PY) build_web.py
all: test validate summary figures generated report whitepaper demo
