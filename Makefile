PY ?= .venv/bin/python

.PHONY: setup data holdout submission audit site test all verify-downloads refresh-downloads
setup:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

data:
	$(PY) scripts/restore_data.py --with-external

holdout:
	$(PY) scripts/run_lane.py --arms lane,no_gmc --ratios 4,6,8,10,12

submission:
	$(PY) scripts/build_submission.py --suppress-px 10

audit:
	$(PY) scripts/build_registry.py
	$(PY) scripts/audit_uniqueness.py --candidate $$(ls -t docs/downloads/*.tif | head -1)

verify-downloads:
	$(PY) scripts/check_site.py
	$(PY) scripts/audit_downloads.py

refresh-downloads:
	$(PY) scripts/audit_downloads.py --write

site: verify-downloads
	$(PY) scripts/build_site.py

test:
	$(PY) -m pytest -q

all: data holdout submission audit site test
