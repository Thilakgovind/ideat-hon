"""Consent-first draft preparation for verified women-athlete offers."""


def build(profile, opportunity, *, consent=False):
    verified = opportunity.get('source') == 'verified' and opportunity.get('status') == 'open'
    if not verified:
        return {'claimable': False, 'reason': 'only verified open offers can be claimed', 'draft': None}
    draft = {
        'opportunity_id': opportunity['id'],
        'display_name': profile.get('display_name', ''),
        'district_id': profile.get('district_id'),
        'sport_id': profile.get('sport_id'),
        'language': profile.get('language', 'ta'),
        'share_fields': ['display_name', 'district_id', 'sport_id'],
        'notes': '',
    }
    return {'claimable': bool(consent),
            'reason': 'review this editable draft and confirm before sharing' if not consent else 'ready for explicit review',
            'draft': draft}
