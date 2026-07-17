from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from control_center import server


def _read_frontmatter(path: Path) -> tuple[dict, str]:
    return server.split_frontmatter(path.read_text(encoding="utf-8"))


def test_setup_status_flags_placeholder_values(monkeypatch, tmp_path):
    monkeypatch.setenv("VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("STRANDS_CHAT_URL", "your_strands_endpoint")
    monkeypatch.setenv("MODEL_ID", "amazon.nova-lite-v1:0")
    monkeypatch.setenv("TWITTER_API_KEY", "changeme")

    setup = server.setup_status()
    core_brain = next(group for group in setup if group["name"] == "Core Brain")
    social = next(group for group in setup if group["name"] == "Social")

    assert core_brain["ready"] is False
    assert any(item["key"] == "VAULT_PATH" and item["ready"] is True for item in core_brain["items"])
    assert any(item["key"] == "STRANDS_CHAT_URL" and item["ready"] is False for item in core_brain["items"])
    assert any(item["key"] == "TWITTER_API_KEY" and item["ready"] is False for item in social["items"])


def test_recommended_actions_include_approved_items(tmp_path):
    vault = tmp_path / "vault"
    server.ensure_vault_structure(vault)
    (vault / "Approved" / "EMAIL_APPROVED_001.md").write_text("# Approved", encoding="utf-8")

    actions = server.recommended_actions(vault)

    assert any("Execute 1 approved item(s)" in action for action in actions)


def test_failed_actions_are_visible_and_counted_in_backlog(tmp_path):
    vault = tmp_path / "vault"
    server.ensure_vault_structure(vault)
    (vault / "Failed" / "INVOICE_FAILED_001.md").write_text(
        "# Failed invoice", encoding="utf-8"
    )

    overview = server.overview_payload(vault)

    assert overview["headline"]["backlog"] == 1
    assert any(queue["key"] == "failed" and queue["count"] == 1 for queue in overview["queues"])
    assert overview["recommended_actions"][0].startswith("Inspect 1 failed action")


def test_api_capture_creates_slugged_needs_action_item(monkeypatch, tmp_path):
    vault = tmp_path / "external-vault"
    monkeypatch.setenv("VAULT_PATH", str(vault))

    with TestClient(server.app) as client:
        response = client.post(
            "/api/actions/capture",
            json={
                "title": "Client follow-up / APAC",
                "details": "Need a response drafted before tomorrow morning.",
                "capture_type": "ops",
                "priority": "high",
            },
        )

    payload = response.json()
    created = vault / "Needs_Action" / payload["filename"]
    metadata, body = _read_frontmatter(created)

    assert response.status_code == 200
    assert created.exists()
    assert payload["filename"].startswith("OPS_MANUAL_CLIENT_FOLLOW_UP_APAC_")
    assert metadata["status"] == "needs_action"
    assert metadata["source"] == "control_center"
    assert "Need a response drafted before tomorrow morning." in body


def test_api_move_updates_frontmatter_and_queue(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    monkeypatch.setenv("VAULT_PATH", str(vault))
    server.ensure_vault_structure(vault)
    source = vault / "Needs_Action" / "EMAIL_TEST_001.md"
    source.write_text("# Test item\n\nMove me", encoding="utf-8")

    with TestClient(server.app) as client:
        response = client.post(
            "/api/items/needs_action/EMAIL_TEST_001.md/move",
            json={"target": "approved"},
        )

    destination = vault / "Approved" / "EMAIL_TEST_001.md"
    metadata, body = _read_frontmatter(destination)

    assert response.status_code == 200
    assert not source.exists()
    assert destination.exists()
    assert metadata["status"] == "approved"
    assert metadata["queue"] == "approved"
    assert "updated" in metadata
    assert "# Test item" in body


def test_external_vault_paths_work_in_item_and_artifact_endpoints(monkeypatch, tmp_path):
    vault = tmp_path / "outside-root-vault"
    monkeypatch.setenv("VAULT_PATH", str(vault))
    server.ensure_vault_structure(vault)
    item = vault / "Needs_Action" / "EMAIL_001.md"
    item.write_text(
        "\n".join(
            [
                "---",
                yaml.safe_dump({"title": "External item", "status": "needs_action"}, sort_keys=False).strip(),
                "---",
                "",
                "## Note",
                "",
                "Lives outside the repo root.",
            ]
        ),
        encoding="utf-8",
    )

    with TestClient(server.app) as client:
        item_response = client.get("/api/items/needs_action/EMAIL_001.md")
        briefing_response = client.post("/api/actions/briefing")
        dashboard_response = client.post("/api/actions/dashboard")

    item_payload = item_response.json()
    briefing_payload = briefing_response.json()
    dashboard_payload = dashboard_response.json()

    assert item_response.status_code == 200
    assert item_payload["path"] == str(item)
    assert briefing_response.status_code == 200
    assert briefing_payload["path"].startswith(str(vault))
    assert dashboard_response.status_code == 200
    assert dashboard_payload["path"] == str(vault / "Dashboard.md")


def test_recent_audit_entries_returns_newest_structured_events(tmp_path):
    vault = tmp_path / "vault"
    server.ensure_vault_structure(vault)
    log_file = vault / "Logs" / "events.jsonl"
    log_file.write_text(
        "\n".join(
            [
                '{"timestamp":"2026-05-09T02:00:00+00:00","actor":"watcher","action_type":"email_received","result":"success"}',
                '{"timestamp":"2026-05-09T03:00:00+00:00","actor":"orchestrator","action_type":"approval_requested","result":"queued"}',
            ]
        ),
        encoding="utf-8",
    )

    entries = server.recent_audit_entries(vault, limit=2)

    assert [entry["action"] for entry in entries] == ["approval_requested", "email_received"]
    assert entries[0]["actor"] == "orchestrator"


def test_assistant_brief_surfaces_hotspots_and_stale_items(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    monkeypatch.setenv("VAULT_PATH", str(vault))
    server.ensure_vault_structure(vault)

    pending = vault / "Pending_Approval" / "EMAIL_PENDING_001.md"
    pending.write_text("---\ntitle: Waiting on founder\n---\n\nBody", encoding="utf-8")
    approved = vault / "Approved" / "EMAIL_APPROVED_001.md"
    approved.write_text("---\ntitle: Ready to send\n---\n\nBody", encoding="utf-8")

    brief = server.assistant_brief(vault)

    assert brief["mood"] in {"attention", "pressure"}
    assert any("execution" in hotspot.lower() for hotspot in brief["hotspots"])
    assert brief["stale_items"][0]["title"] in {"Waiting on founder", "Ready to send"}
    assert "recommended_actions" in brief
