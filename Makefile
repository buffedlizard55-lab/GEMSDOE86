PY ?= .venv/bin/python
.DEFAULT_GOAL := all
# data → audit → site → verify must stay ordered even with make -j.
.NOTPARALLEL:

.PHONY: setup data holdout submission audit refresh site test verify all verify-downloads refresh-downloads
setup:
	python3 -m venv .venv && .venv/bin/pip install -r requirements-lock.txt

# Small proof inputs only. A raw core TIFF is not the required shared feature cache.
data:
	$(PY) scripts/restore_protocol_data.py --include-registry

# Scientific entrypoints deliberately STOP under the current literal rule.
holdout:
	$(PY) scripts/run_lane.py --arms lane,no_gmc --ratios 4,6,8,10,12

submission:
	$(PY) scripts/build_submission.py --suppress-px 10

# Audit all files; do not silently choose the newest candidate with ls/head.
audit:
	$(PY) scripts/audit_release.py --measure-registry
	$(PY) scripts/audit_legacy_spt.py --write

# Retain the independently merged all-download integrity audit and its commands.
verify-downloads:
	$(PY) scripts/check_site.py
	$(PY) scripts/audit_downloads.py

refresh-downloads:
	$(PY) scripts/audit_downloads.py --write

refresh:
	$(PY) scripts/refresh_fleet.py

site:
	$(PY) scripts/build_site.py

test:
	$(PY) -m pytest -q

verify:
	$(PY) scripts/build_site.py --check
	$(PY) scripts/check_site.py
	$(PY) scripts/audit_legacy_spt.py
	$(PY) scripts/audit_downloads.py
	$(PY) -m pytest -q

# The safe default pipeline performs no model experiment, placement or slot selection.
all: data audit site verify
