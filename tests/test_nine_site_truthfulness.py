"""Regression tests for distinctions between history, estimates and submission clearance."""
import copy
import json
from pathlib import Path

from scripts.build_site import nine_sites_page

ROOT = Path(__file__).resolve().parents[1]


def inputs():
    def load(name):
        return json.loads((ROOT / 'docs/evidence' / name).read_text())
    return (load('nine-site-audit-20261027.json'),
            load('h87-fcb-candidate-receipt-20261027.json'),
            load('h87-fcb-experiment1-20261027.json'),
            load('h87-fcb-experiment2-20261027.json'))


def test_nine_site_page_distinguishes_history_from_estimates_and_approval():
    page = nine_sites_page(*inputs())
    assert 'Historical owner-reported result (not an estimate)' in page
    assert 'not guaranteed present in a fresh checkout' in page
    assert 'cell-bootstrap interval, not the requested spatial-block interval' in page
    assert 'holdout does not validate that exact final raster' in page
    assert 'No upload is authorized' in page
    assert 'an organizer receipt can only exist after an upload' in page
    assert 'not a guarantee of portal acceptance' not in page  # different section


def test_nine_site_threshold_is_strictly_greater_not_greater_or_equal():
    audit, cand, exp1, exp2 = copy.deepcopy(inputs())
    site = audit['files'][0]['site']
    audit['max_overlap_by_site'][site]['value'] = audit['threshold_overlap']
    page = nine_sites_page(audit, cand, exp1, exp2)
    row = next(row for row in page.split('</tr>') if f'<td>{site}</td>' in row)
    assert 'yes: max 0.7000' in row


def test_nine_sites_page_marks_its_own_navigation_item_active():
    page = nine_sites_page(*inputs())
    assert '<a href="nine-sites.html" aria-current="page">Nine sites</a>' in page
    assert '<a href="executive-summary.html" aria-current="page">How to submit</a>' not in page
