"""The independent identity checker must not imply registry or slot clearance."""
import json
import zipfile

import pytest

from scripts import verify_submission_tif as verifier


def test_real_file_format_pass_is_not_upload_authorization(capsys):
    assert verifier.main() == 0
    output = capsys.readouterr().out
    assert 'FORMAT/IDENTITY CHECK PASSED' in output
    assert 'DO NOT SUBMIT' in output
    assert 'unique by pinned digest' not in output
    assert 'NOT established' in output


@pytest.mark.parametrize('payload', ['{', '[]', 'null', '{"note":null}', '{"note":12}', '{"note":""}'])
def test_malformed_receipt_fails_cleanly(tmp_path, monkeypatch, capsys, payload):
    receipt = tmp_path / 'receipt.json'
    receipt.write_text(payload)
    monkeypatch.setattr(verifier, 'RECEIPT', receipt)
    assert verifier.main() == 1
    assert 'VERIFY FAILED' in capsys.readouterr().out


def test_missing_tiff_fails_cleanly(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(verifier, 'TIFF', tmp_path / 'missing.tif')
    assert verifier.main() == 1
    assert 'VERIFY FAILED' in capsys.readouterr().out


@pytest.mark.parametrize('kind', ['invalid', 'empty', 'wrong-member', 'duplicate'])
def test_bad_zip_fails_without_member_lookup_crash(tmp_path, monkeypatch, capsys, kind):
    archive = tmp_path / 'candidate.zip'
    if kind == 'invalid':
        archive.write_bytes(b'not a zip')
    else:
        with zipfile.ZipFile(archive, 'w') as z:
            if kind == 'wrong-member':
                z.writestr('unrelated.tif', b'wrong')
            elif kind == 'duplicate':
                z.writestr(verifier.TIFF.name, b'wrong')
                with pytest.warns(UserWarning, match='Duplicate name'):
                    z.writestr(verifier.TIFF.name, b'wrong')
    monkeypatch.setattr(verifier, 'ZIP', archive)
    assert verifier.main() == 1
    assert 'VERIFY FAILED' in capsys.readouterr().out


def test_wrong_validator_schema_fails_cleanly(tmp_path, monkeypatch, capsys):
    receipt = json.loads(verifier.RECEIPT.read_text())
    receipt['validator'] = None
    path = tmp_path / 'receipt.json'
    path.write_text(json.dumps(receipt))
    monkeypatch.setattr(verifier, 'RECEIPT', path)
    assert verifier.main() == 1
    assert 'VERIFY FAILED' in capsys.readouterr().out
