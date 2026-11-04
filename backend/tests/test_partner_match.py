from backend import partner_match


def test_partner_match_never_returns_unverified_rows(monkeypatch):
    monkeypatch.setattr(partner_match, 'read', lambda: ([{
        'id': 'x', 'partner_name': 'Sample', 'offer_type': 'equipment',
        'verified': False, 'status': 'sample',
    }], 'sample_fallback'))
    assert partner_match.match(query='equipment') == []


def test_partner_match_returns_only_approved_open_rows(monkeypatch):
    monkeypatch.setattr(partner_match, 'read', lambda: ([{
        'id': 'x', 'partner_name': 'Women Sports Store', 'offer_type': 'equipment',
        'verified': True, 'status': 'open',
    }], 'supabase'))
    assert partner_match.match(query='sports equipment')[0]['id'] == 'x'
