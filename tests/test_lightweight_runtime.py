from pathlib import Path

from control_center import server


ROOT = Path(__file__).resolve().parents[1]


def test_default_launcher_has_one_approval_executor():
    launcher = (ROOT / "start_all.sh").read_text(encoding="utf-8")

    assert launcher.count("python3 scripts/orchestrator.py") == 1
    assert "python3 agents/local_orchestrator.py" not in launcher
    assert "python3 scripts/watchdog.py" not in launcher


def test_public_page_avoids_decorative_network_and_scroll_work():
    html = (ROOT / "public" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "public" / "assets" / "styles.css").read_text(encoding="utf-8")
    javascript = (ROOT / "public" / "assets" / "app.js").read_text(encoding="utf-8")

    assert "fonts.googleapis.com" not in html
    assert "grainy-gradients" not in css
    assert "mousemove" not in javascript
    assert 'addEventListener("scroll"' not in javascript


def test_overview_reuses_expensive_snapshots(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    server.ensure_vault_structure(vault)
    calls = {"counts": 0, "metrics": 0, "setup": 0, "services": 0}

    original_counts = server.queue_counts
    original_metrics = server.activity_metrics

    def counted_queue_counts(path):
        calls["counts"] += 1
        return original_counts(path)

    def counted_activity_metrics(path):
        calls["metrics"] += 1
        return original_metrics(path)

    def counted_setup_status():
        calls["setup"] += 1
        return []

    def counted_service_status():
        calls["services"] += 1
        return []

    monkeypatch.setattr(server, "queue_counts", counted_queue_counts)
    monkeypatch.setattr(server, "activity_metrics", counted_activity_metrics)
    monkeypatch.setattr(server, "setup_status", counted_setup_status)
    monkeypatch.setattr(server, "service_status", counted_service_status)

    payload = server.overview_payload(vault)

    assert payload["assistant_brief"]["metrics"]["avg_pending_hours"] == 0
    assert calls == {"counts": 1, "metrics": 1, "setup": 1, "services": 1}
