from backend.nss_support import match

def test_unverified_nss_rows_never_appear_as_joinable():
    assert match() == []
