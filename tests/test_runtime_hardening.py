import importlib
import base64
import hashlib
import hmac
import os
import re
import subprocess
import threading
from types import SimpleNamespace
from pathlib import Path

import pytest

from control_center import server
from agents.orchestrator import VaultHandler


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_webhook(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    needs_action = vault / "Needs_Action"
    needs_action.mkdir(parents=True)

    monkeypatch.setenv("VAULT_PATH", str(vault))
    webhook_server = importlib.import_module("agents.webhook_server")

    monkeypatch.setattr(webhook_server, "VAULT_PATH", vault)
    monkeypatch.setattr(webhook_server, "NEEDS_ACTION", needs_action)
    monkeypatch.setattr(webhook_server, "PROCESSED_FILE", vault / ".processed_twilio_messages")
    monkeypatch.setattr(webhook_server, "PROCESSED_MESSAGES", set())
    monkeypatch.setattr(
        webhook_server,
        "INCOMING_STORE",
        vault / ".whatsapp_incoming.json",
        raising=False,
    )
    return webhook_server, vault, needs_action


def twilio_message(message_id="SM-runtime-hardening-001"):
    return {
        "MessageSid": message_id,
        "From": "whatsapp:+14165550123",
        "Body": "Urgent: please review the invoice today.",
    }


@pytest.mark.asyncio
async def test_twilio_webhook_creates_needs_action_without_incoming_queue(isolated_webhook):
    webhook_server, vault, needs_action = isolated_webhook

    await webhook_server.handle_twilio_webhook(twilio_message())

    action_files = list(needs_action.glob("WHATSAPP_*.md"))
    assert len(action_files) == 1
    content = action_files[0].read_text(encoding="utf-8")
    metadata, _ = server.split_frontmatter(content)
    assert metadata["message_id"] == "SM-runtime-hardening-001"
    assert metadata["from"] == "+14165550123"
    assert metadata["urgency"] == "URGENT"
    assert not (vault / ".whatsapp_incoming.json").exists()


@pytest.mark.asyncio
async def test_duplicate_twilio_message_id_is_idempotent(isolated_webhook):
    webhook_server, vault, needs_action = isolated_webhook
    message = twilio_message("SM-runtime-hardening-duplicate")

    await webhook_server.handle_twilio_webhook(message)
    await webhook_server.handle_twilio_webhook(message)

    action_files = list(needs_action.glob("WHATSAPP_*.md"))
    assert len(action_files) == 1
    assert webhook_server.PROCESSED_MESSAGES == {"SM-runtime-hardening-duplicate"}
    assert (vault / ".processed_twilio_messages").read_text(encoding="utf-8").splitlines() == [
        "SM-runtime-hardening-duplicate"
    ]
    assert not (vault / ".whatsapp_incoming.json").exists()


@pytest.mark.asyncio
async def test_webhook_write_failure_does_not_mark_message_processed(
    isolated_webhook, monkeypatch
):
    webhook_server, vault, _ = isolated_webhook

    def fail_write(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(webhook_server, "create_whatsapp_action_file", fail_write)

    with pytest.raises(OSError, match="disk full"):
        await webhook_server.handle_twilio_webhook(twilio_message("SM-write-failure"))

    assert "SM-write-failure" not in webhook_server.PROCESSED_MESSAGES
    assert not (vault / ".processed_twilio_messages").exists()


def test_webhook_signature_validation_uses_provider_hmacs(isolated_webhook, monkeypatch):
    webhook_server, _, _ = isolated_webhook
    url = "https://example.test/webhook"
    form = {"Body": "Hello", "From": "whatsapp:+14165550123"}
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "twilio-secret")
    signed = url + "BodyHello" + "Fromwhatsapp:+14165550123"
    twilio_signature = base64.b64encode(
        hmac.new(b"twilio-secret", signed.encode(), hashlib.sha1).digest()
    ).decode()

    assert webhook_server.validate_twilio_signature(url, form, twilio_signature)
    assert not webhook_server.validate_twilio_signature(url, form, "invalid")

    body = b'{"entry":[]}'
    monkeypatch.setenv("META_APP_SECRET", "meta-secret")
    meta_signature = "sha256=" + hmac.new(
        b"meta-secret", body, hashlib.sha256
    ).hexdigest()
    assert webhook_server.validate_meta_signature(body, meta_signature)
    assert not webhook_server.validate_meta_signature(body, "sha256=invalid")


def _probe_env_has(tmp_path: Path, key: str, value: str) -> subprocess.CompletedProcess:
    launcher = (ROOT / "start_all.sh").read_text(encoding="utf-8")
    activation_marker = 'if [ -f ".venv/bin/activate" ]; then'
    assert activation_marker in launcher
    probe = launcher.replace(
        activation_marker,
        f'env_has "{key}"\nexit $?\n\n{activation_marker}',
        1,
    )

    probe_path = tmp_path / "start_all.sh"
    probe_path.write_text(probe, encoding="utf-8")
    (tmp_path / ".env").write_text(f"{key}={value}\n", encoding="utf-8")

    environment = os.environ.copy()
    environment.pop(key, None)
    return subprocess.run(
        ["bash", str(probe_path)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_launcher_guards_live_pids_and_rejects_placeholder_credentials(tmp_path):
    launcher = (ROOT / "start_all.sh").read_text(encoding="utf-8")

    assert re.search(r"kill\s+-0\s+", launcher), "launcher must verify that recorded PIDs are live"
    assert "RUNTIME_DIR" in launcher and "pids" in launcher

    for placeholder in ("your_gmail_client_id", "changeme", "replace-me", "example-token"):
        result = _probe_env_has(tmp_path, "GMAIL_CLIENT_ID", placeholder)
        assert result.returncode != 0, f"placeholder credential was accepted: {placeholder}"

    configured = _probe_env_has(tmp_path, "GMAIL_CLIENT_ID", "client-id.apps.googleusercontent.com")
    assert configured.returncode == 0


def test_control_and_stop_patterns_match_launcher_entrypoints():
    stopper = (ROOT / "stop_all.sh").read_text(encoding="utf-8")

    assert server.PROCESS_PATTERNS["orchestrator"] == "scripts/orchestrator.py"
    assert server.PROCESS_PATTERNS["webhook"] == "scripts/webhook_server.py"
    assert 'pkill -f "scripts/orchestrator.py"' in stopper
    assert 'pkill -f "scripts/webhook_server.py"' in stopper


def test_odoo_legacy_stdio_uses_esm_readline_import():
    source = (ROOT / "mcp_servers" / "odoo_mcp" / "index.js").read_text(encoding="utf-8")

    assert re.search(
        r"^import\s+.+\s+from\s+['\"](?:node:)?readline['\"];?\s*$",
        source,
        re.MULTILINE,
    )
    assert "require('readline')" not in source
    assert 'require("readline")' not in source
    assert "for await (const line of rl)" in source
    assert "rl.on('close'" not in source


def test_failed_action_moves_out_of_approved(tmp_path, monkeypatch):
    handler = object.__new__(VaultHandler)
    handler.vault = tmp_path
    handler.approved = tmp_path / "Approved"
    handler.done = tmp_path / "Done"
    handler.failed = tmp_path / "Failed"
    handler.approved.mkdir()
    handler.done.mkdir()
    handler.executed_files = set()
    handler.dedup_lock = threading.Lock()
    monkeypatch.setattr(handler, "_execute_email", lambda *_args: (_ for _ in ()).throw(RuntimeError("send failed")))
    monkeypatch.setattr(handler, "_log_action", lambda *_args, **_kwargs: None)

    action = handler.approved / "EMAIL_FAIL_001.md"
    action.write_text("# Approval", encoding="utf-8")
    handler._execute_action(action)

    assert not action.exists()
    assert (handler.failed / action.name).exists()
    assert not (handler.done / action.name).exists()
    assert action.name not in handler.executed_files


def test_odoo_adapter_rejects_errors_and_accepts_confirmed_response(tmp_path, monkeypatch):
    handler = object.__new__(VaultHandler)
    handler.vault = tmp_path
    monkeypatch.setenv("ODOO_USERNAME", "admin")
    monkeypatch.setenv("ODOO_PASSWORD", "secret")

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout='{"status":"error","detail":"rejected"}\n',
            stderr="",
        ),
    )
    with pytest.raises(RuntimeError, match="rejected"):
        handler._call_odoo_adapter("create_invoice", {})

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout='{"status":"created","invoice_id":42}\n',
            stderr="",
        ),
    )
    assert handler._call_odoo_adapter("create_invoice", {})["invoice_id"] == 42
