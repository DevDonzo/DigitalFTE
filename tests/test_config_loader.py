from pathlib import Path

from utils.config_loader import ROOT, load_config


def test_load_config_normalizes_runtime_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "CONTROL_CENTER_PORT=9191",
                "WEBHOOK_PORT=8111",
                "DRY_RUN=true",
                "VAULT_PATH=custom-vault",
                "MODEL_ID=amazon.nova-pro-v1:0",
                "STRANDS_CHAT_URL=http://localhost:18080/chat",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(env_file)

    assert config["CONTROL_CENTER_PORT"] == 9191
    assert config["WEBHOOK_PORT"] == 8111
    assert config["DRY_RUN"] is True
    assert config["MODEL_ID"] == "amazon.nova-pro-v1:0"
    assert config["STRANDS_CHAT_URL"] == "http://localhost:18080/chat"
    assert config["VAULT_PATH"] == (ROOT / "custom-vault").resolve()


def test_load_config_uses_defaults_when_values_are_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("CONTROL_CENTER_PORT", raising=False)
    monkeypatch.delenv("WEBHOOK_PORT", raising=False)
    monkeypatch.delenv("DRY_RUN", raising=False)
    monkeypatch.delenv("VAULT_PATH", raising=False)

    config = load_config(tmp_path / "missing.env")

    assert config["CONTROL_CENTER_PORT"] == 8282
    assert config["WEBHOOK_PORT"] == 8001
    assert config["DRY_RUN"] is False
    assert isinstance(config["VAULT_PATH"], Path)
