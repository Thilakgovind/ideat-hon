from backend.veeramangai import digilocker_start

def test_digilocker_entry_point_is_transparent_demo_mode():
    result = digilocker_start()
    assert result['mode'] == 'manual_demo'
    assert result['connected'] is False
    assert result['provider_url'].startswith('https://www.digilocker.gov.in')
    assert 'No document was accessed' in result['message']
