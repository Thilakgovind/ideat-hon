from backend.offer_draft import build


def test_sample_offer_cannot_be_claimed():
    result = build({'display_name': 'A', 'district_id': 'd', 'sport_id': 's'},
                   {'id': 'sample', 'source': 'sample', 'status': 'sample'})
    assert result['claimable'] is False and result['draft'] is None


def test_verified_offer_is_editable_and_requires_consent():
    profile = {'display_name': 'A', 'district_id': 'd', 'sport_id': 's', 'language': 'ta'}
    offer = {'id': 'verified-1', 'source': 'verified', 'status': 'open'}
    preview = build(profile, offer)
    assert preview['claimable'] is False and preview['draft']['share_fields'] == ['display_name', 'district_id', 'sport_id']
    confirmed = build(profile, offer, consent=True)
    assert confirmed['claimable'] is True and confirmed['draft']['notes'] == ''
