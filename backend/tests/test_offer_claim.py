from backend.offer_draft import build


def test_claim_contract_requires_explicit_consent_and_verified_offer():
    sample = build({'display_name': 'A'}, {'id': 's', 'source': 'sample', 'status': 'sample'}, consent=True)
    verified_preview = build({'display_name': 'A'}, {'id': 'v', 'source': 'verified', 'status': 'open'})
    assert sample['claimable'] is False
    assert verified_preview['claimable'] is False

