import json
from zipfile import ZipFile, ZipInfo
import pytest
from training.import_results import read_evidence, report, render


def archive(tmp_path, entries):
    target = tmp_path/'results.zip'
    with ZipFile(target, 'w') as z:
        for name, value in entries.items():
            info = ZipInfo('entry')
            info.filename = name
            z.writestr(info, value)
    return target


def test_import_reads_only_evidence_without_extraction(tmp_path):
    path = archive(tmp_path, {'metrics.json': json.dumps({'base': {'base_test_loss': 4}, 'candidate': {'candidate_test_loss': 3}}), 'adapter/adapter_model.safetensors': b'not loaded'})
    evidence = read_evidence(path)
    result = report(evidence)
    assert result['reference_loss_reduction_pct'] == 25
    assert result['deploy'] is False
    assert not (tmp_path/'adapter').exists()
    assert result['review']['status'] == 'blocked'

@pytest.mark.parametrize('name', ['../metrics.json', '/metrics.json', 'C:/metrics.json', 'folder\\metrics.json'])
def test_rejects_unsafe_archive_paths(tmp_path, name):
    with pytest.raises(ValueError, match='Unsafe'):
        read_evidence(archive(tmp_path, {name: '{}'}))


def test_ambiguous_metrics_rejected(tmp_path):
    with pytest.raises(ValueError, match='Ambiguous'):
        read_evidence(archive(tmp_path, {'a/metrics.json': '{}', 'b/metrics.json': '{}'}))


def test_html_escapes_model_output():
    page = render({'deploy': False}, {'comparison.json': [{'prompt': '<script>alert(1)</script>', 'adapter': '<img src=x onerror=alert(1)>'}]})
    assert '<script>' not in page and '<img' not in page
    assert '&lt;script&gt;' in page


def test_missing_metrics_does_not_invent_improvement():
    result = report({'answers.json': []})
    assert result['reference_loss_reduction_pct'] is None and not result['deploy']
