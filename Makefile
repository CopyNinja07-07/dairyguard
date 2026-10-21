# Reproduce everything. Requires Python 3.10+, the packages in requirements.txt, and (for the paper) a LaTeX install.
PY=python3
.PHONY: test runs validate summary figures paper book demo all
test:
	@for f in tests/test_*.py; do $(PY) $$f || exit 1; done
runs:   # about three hours on two CPU cores
	DG_PARAMS=ref $(PY) src/benchmark_v2.py 4000 results/base
	DG_PARAMS=ref DG_SHIFT=0.25 $(PY) src/benchmark_v2.py 4000 results/lag
	DG_PARAMS=ref DG_N0=low $(PY) src/benchmark_v2.py 4000 results/low
	DG_PARAMS=comb DG_N0=low $(PY) src/benchmark_v2.py 4000 results/comb
	DG_PARAMS=lis $(PY) src/benchmark_v2.py 4000 results/lis
validate:
	$(PY) src/validate_lin.py
	$(PY) src/validate_combase.py
	$(PY) src/validate_combase_lis.py
summary:
	$(PY) src/summarize_runs.py
figures:
	cd book && $(PY) figures.py
paper: summary
	$(PY) paper/figures_paper.py
	$(PY) paper/make_numbers.py
	$(PY) paper/make_tables.py
	cd paper && latexmk -pdf -interaction=nonstopmode main.tex && cp main.pdf ../docs/DairyGuard_Research_Paper.pdf
book: figures
	cd book && $(PY) cover.py && latexmk -pdf -interaction=nonstopmode monograph.tex && cp monograph.pdf ../docs/DairyGuard_Monograph.pdf
demo: summary
	cd demo && $(PY) build_web.py
all: test validate summary figures paper book demo
