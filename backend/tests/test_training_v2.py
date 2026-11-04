from training.build_v2 import build


def test_v2_balanced_tasks_and_disjoint_families():
    rows=build()
    assert len(rows)>=152
    groups={s:{r['family'] for r in rows if r['split']==s} for s in ('train','validation','test')}
    assert not groups['train'] & groups['validation']
    assert not groups['train'] & groups['test']
    assert not groups['validation'] & groups['test']
    train=[r for r in rows if r['split']=='train']
    assert sum(r['category']=='app_task' for r in train)==72
    assert sum(r['category']=='safety' for r in train)==34
    assert all(not r['clinically_reviewed'] and not r['language_reviewed'] for r in rows)
    assert len({r['id'] for r in rows})==len(rows)


def test_legitimate_task_targets_do_not_medically_refuse():
    for row in build():
        if row['category']=='app_task':
            answer=row['messages'][-1]['content'].lower()
            assert 'healthcare professional' not in answer
            assert 'cannot assist with financial' not in answer
