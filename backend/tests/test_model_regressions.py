from training.colab_code_red import CASES, flags, summarize


def test_regressions_cover_languages_and_unique_cases():
    assert len({c[0] for c in CASES}) == len(CASES)
    assert {c[1] for c in CASES} == {'en', 'ta', 'tanglish'}


def test_flags_detect_observed_repetition_and_truncation():
    assert flags('enna seiyanum varudhu ' * 12)['repetition']
    assert flags('unfinished answer', True)['truncated']
    assert flags('')['empty']
    assert not any(flags('You can prepare a request and review it before submitting.').values())


def test_no_automatic_release_from_clean_outputs():
    result = summarize([{'language': 'en', 'flags': flags('A brief answer.')}])
    assert result['flagged'] == 0
    assert result['release'] == 'pending_independent_review'


def test_release_checklist_fails_closed():
    from training.release_review import assess
    assert assess([])['status'] == 'blocked'
    assert assess([])['deploy'] is False
    rows = [{'case_id': c[0], 'variant': v, 'reply': 'Reviewed answer',
             'language': c[1], 'human_review': 'approved', 'review_note': 'Reviewed against policy',
             'flags': flags('Reviewed answer')} for c in CASES for v in ('base', 'adapter')]
    assert assess(rows)['status'] == 'eligible_for_further_release_review'
    rows[0]['flags']['truncated'] = True
    assert assess(rows)['status'] == 'blocked'
