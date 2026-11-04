from training.measure import audit


def test_training_audit_is_honest_about_coverage():
    result = audit()
    assert result['split_rows'] == {'train': 680, 'validation': 160, 'test': 160}
    assert result['family_overlap'] == []
    assert result['unique_reference_answers'] == 25
    assert result['languages'] == {'en': 1000}
    assert result['clinically_reviewed_rows'] == 0
    assert result['release'].startswith('rejected')
    assert 29 < result['reference_loss_reduction_pct'] < 30
