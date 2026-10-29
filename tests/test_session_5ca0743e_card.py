"""The 2026-10-29 read-only review must not be mistaken for a submission."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / 'docs/evidence/session-5ca0743e-run-card.json'


def test_unrun_card_preserves_negative_state_and_exact_evidence_bytes():
    card = json.loads(CARD.read_text())
    assert card['verdict'] == 'negative' and card['decision'] == 'DO NOT SUBMIT'
    assert card['session_branch'] == 'arena/5ca0743e-gemsdoe86'
    assert card['lane_assignment'] is None
    assert card['new_candidate_generated'] is card['unique_tiff_requirement_satisfied'] is False
    assert card['safe_to_submit'] is card['approved_for_weekly_slot'] is False
    assert card['experiments_run'] == card['submission_slots_used'] == 0
    assert card['raster_sha256'] is card['submission_name'] is card['organizer_score_estimate'] is None
    assert 0 < len(card['note']) <= 140
    h = card['holdout_dti']
    assert h['status'].startswith('NOT_RUN')
    assert h['evaluator_version'] is h['value'] is h['ci95'] is h['withheld_positives'] is None
    assert card['validator_output']['status'] == 'NOT_RUN_NO_NEW_RASTER'
    reg = card['correlation_overlap_vs_registry']
    assert reg['candidate_surface_spearman'] is reg['candidate_final_dot_overlap_3px'] is None
    assert reg['witness_direct_uncovered_allowed_pixels'] == 0
    assert reg['witness_implied_forward_overlap_for_any_nonempty_allowed_candidate'] == 1.0
    assert reg['overlap_limit'] == 0.70 and reg['registry_complete'] is False
    assert card['upstream_metric_prose_issue']['shared_tool_modified'] is False
    for path, digest in card['evidence_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path


def test_dated_workspace_receipt_is_not_claimed_as_a_shared_cache():
    card = json.loads(CARD.read_text())
    inputs = json.loads((ROOT / 'docs/evidence/session-5ca0743e-inputs-20261029.json').read_text())
    status = card['input_status_at_measurement']
    assert status['measured_utc'] == inputs['measured_utc']
    assert status['native_inputs_available'] is inputs['native_inputs_available'] is True
    assert status['native_bands_prepared'] is inputs['preparation']['native_bands_available'] is True
    assert status['shared_template_cache_established'] is inputs['shared_cache']['ready'] is False
    assert inputs['safe_to_submit'] is False
    assert 'ephemeral' in status['persistence']


def test_focus9_public_table_never_treats_a_score_estimate_as_a_result():
    html = (ROOT / 'docs/executive-summary.html').read_text()
    table = html.split('id="focus9-summary"', 1)[1].split('</section>', 1)[0]
    assert 'Estimated organizer score' in table
    assert table.count('no calibrated organizer-score estimate') == 9
    assert table.count('SUBMIT: NO') >= 9
    assert 'GitHub availability is not guaranteed' in table
    assert 'not a fresh score or new byte audit' in table
