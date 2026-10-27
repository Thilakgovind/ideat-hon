"""check_keys reports names and status only, never values."""
from backend import check_keys, config

SECRET = "sk_SECRET_value_12345"


def test_lint_reports_names_not_values(tmp_path):
    f = tmp_path / ".env"
    f.write_text(f"GEMINI_API_KEY={SECRET}\n GEMINI_API_KEY={SECRET}\nTest sece: {SECRET}\n"
                 f"{SECRET}\nSARVAM_API_KEY=a b\n", encoding="utf-8")
    issues = check_keys.lint_env(f)
    text = repr(issues)
    assert SECRET not in text
    problems = {(no, p) for no, _, p in issues}
    assert (2, "space before name") in problems
    assert any(no == 2 and p.startswith("duplicate") for no, p in problems)
    assert any(no == 3 for no, _ in problems) and any(no == 4 for no, _ in problems)
    assert (5, "value contains spaces") in problems


def test_main_never_prints_values(monkeypatch, capsys, tmp_path):
    for keys in config.SERVICE_KEYS.values():
        for k in keys:
            monkeypatch.setenv(k, SECRET)
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_live_" + SECRET)
    monkeypatch.setattr(check_keys, "ENV_FILE", tmp_path / "missing.env")
    check_keys.main(["--offline"])
    out = capsys.readouterr().out
    assert SECRET not in out and "GEMINI_API_KEY" in out


def test_live_razorpay_key_refused(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_live_x")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "y")
    assert check_keys.check_razorpay()[0] == "FAILED"


def test_health_has_no_values(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.app import app
    monkeypatch.setenv("GEMINI_API_KEY", SECRET)
    r = TestClient(app).get("/health").json()
    assert SECRET not in repr(r) and r["services"]["gemini"] == "real"
    assert r["services"]["sms_provider"] == "mock"


def test_backend_refuses_live_razorpay(monkeypatch):
    import pytest
    from fastapi.testclient import TestClient
    from backend.app import app
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_live_x")
    with pytest.raises(RuntimeError) as e:
        with TestClient(app):
            pass
    assert "rzp_live_x" not in str(e.value)


def test_textbee_device_must_exist(monkeypatch):
    from backend.tests.conftest import FakeResponse
    monkeypatch.setenv("TEXTBEE_API_KEY", SECRET)
    monkeypatch.setenv("TEXTBEE_DEVICE_ID", "dev_mine")
    monkeypatch.setattr(check_keys.httpx, "get", lambda *a, **k: FakeResponse(200, {"data": [{"_id": "other"}]}))
    status, note = check_keys.check_textbee()
    assert status == "FAILED" and "dev_mine" not in note
    monkeypatch.setattr(check_keys.httpx, "get", lambda *a, **k: FakeResponse(200, {"data": [{"_id": "dev_mine"}]}))
    assert check_keys.check_textbee()[0] == "OK"


def test_hidden_txt_extension_is_reported(tmp_path):
    (tmp_path / ".env").write_text("GEMINI_API_KEY=\n", encoding="utf-8")
    (tmp_path / ".env.txt").write_text(f"GEMINI_API_KEY={SECRET}\n", encoding="utf-8")
    issues = check_keys.lint_env(tmp_path / ".env")
    assert any(label == ".env.txt" for _, label, _ in issues) and SECRET not in repr(issues)


def test_db_migrate_never_prints_url(monkeypatch, capsys):
    import pytest
    from backend import db_migrate
    url = "postgresql://postgres.ref:" + SECRET + "@nohost.invalid:5432/postgres"
    monkeypatch.setenv("SUPABASE_DB_URL", url)
    with pytest.raises(SystemExit) as e:
        db_migrate._connect()
    assert SECRET not in str(e.value) and "nohost" not in str(e.value)
    assert SECRET not in capsys.readouterr().out


def test_set_env_replaces_or_adds_without_printing(tmp_path, capsys):
    from backend import set_env
    f = tmp_path / ".env"
    f.write_text("A=1\nRAZORPAY_KEY_SECRET=old\n", encoding="utf-8")
    assert set_env.set_value("RAZORPAY_KEY_SECRET", SECRET, f) == "replaced"
    assert set_env.set_value("SUPABASE_DB_URL", "postgresql://x", f) == "added"
    text = f.read_text(encoding="utf-8")
    assert f"RAZORPAY_KEY_SECRET={SECRET}" in text and "old" not in text and text.count("=") == 3
    assert SECRET not in capsys.readouterr().out
