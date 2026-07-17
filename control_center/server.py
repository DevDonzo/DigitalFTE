"""FastAPI control center for operating DigitalFTE locally."""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
from contextlib import asynccontextmanager
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from utils.config_loader import load_config

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_VAULT = ROOT / "vault"
RUNTIME_CONFIG = load_config()
DEFAULT_PORT = RUNTIME_CONFIG["CONTROL_CENTER_PORT"]
PLACEHOLDER_FRAGMENTS = (
    "your_",
    "example",
    "changeme",
    "replace-me",
    "replace_me",
    "todo",
    "/path/to/",
)

QUEUE_DIRS = {
    "needs_action": "Needs_Action",
    "pending_approval": "Pending_Approval",
    "approved": "Approved",
    "rejected": "Rejected",
    "failed": "Failed",
    "done": "Done",
}

DISPLAY_NAMES = {
    "needs_action": "Needs Action",
    "pending_approval": "Pending Approval",
    "approved": "Approved",
    "rejected": "Rejected",
    "failed": "Failed",
    "done": "Done",
}

QUEUE_DESTINATIONS = {
    "needs_action": "Needs_Action",
    "pending_approval": "Pending_Approval",
    "approved": "Approved",
    "rejected": "Rejected",
    "failed": "Failed",
    "done": "Done",
}

PROCESS_PATTERNS = {
    "control_center": "scripts/control_center.py",
    "orchestrator": "scripts/orchestrator.py",
    "gmail_watcher": "agents/gmail_watcher.py",
    "webhook": "scripts/webhook_server.py",
}

PORT_CHECKS = {
    "control_center": ("127.0.0.1", DEFAULT_PORT),
    "webhook": ("127.0.0.1", RUNTIME_CONFIG["WEBHOOK_PORT"]),
    "odoo": ("127.0.0.1", 8069),
}

SETUP_GROUPS = [
    (
        "Core Brain",
        [
            ("STRANDS_CHAT_URL", "Strands chat endpoint"),
            ("MODEL_ID", "Bedrock model id"),
            ("VAULT_PATH", "Vault path"),
        ],
    ),
    (
        "Gmail",
        [
            ("GMAIL_CLIENT_ID", "OAuth client id"),
            ("GMAIL_CLIENT_SECRET", "OAuth client secret"),
        ],
    ),
    (
        "WhatsApp",
        [
            ("TWILIO_ACCOUNT_SID", "Twilio account"),
            ("TWILIO_AUTH_TOKEN", "Twilio auth token"),
            ("TWILIO_WHATSAPP_NUMBER", "WhatsApp sender"),
        ],
    ),
    (
        "Finance",
        [
            ("ODOO_URL", "Odoo URL"),
            ("ODOO_DB", "Odoo database"),
            ("ODOO_USERNAME", "Odoo username"),
            ("ODOO_PASSWORD", "Odoo password"),
        ],
    ),
    (
        "Social",
        [
            ("LINKEDIN_ACCESS_TOKEN", "LinkedIn access token"),
            ("TWITTER_API_KEY", "Twitter API key"),
            ("TWITTER_API_SECRET", "Twitter API secret"),
            ("FACEBOOK_ACCESS_TOKEN", "Facebook access token"),
        ],
    ),
]


class MoveRequest(BaseModel):
    target: str = Field(..., description="Target queue key or folder name")


class CaptureRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    details: str = Field(..., min_length=5, max_length=6000)
    capture_type: str = Field(default="ops")
    priority: str = Field(default="medium")


def get_vault_path() -> Path:
    """Resolve the active vault path."""
    raw = os.getenv("VAULT_PATH")
    if not raw:
        return DEFAULT_VAULT
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate
    return (ROOT / candidate).resolve()


def ensure_vault_structure(vault: Path) -> None:
    """Create the minimum vault structure the control center expects."""
    for folder in QUEUE_DIRS.values():
        (vault / folder).mkdir(parents=True, exist_ok=True)
    for folder in ["Logs", "Agent_Transcripts"]:
        (vault / folder).mkdir(parents=True, exist_ok=True)


def split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Split YAML frontmatter from markdown content."""
    if not content.startswith("---\n"):
        return {}, content

    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content

    raw_meta = content[4:end]
    body = content[end + 5 :]
    try:
        metadata = yaml.safe_load(raw_meta) or {}
        if not isinstance(metadata, dict):
            metadata = {}
    except yaml.YAMLError:
        metadata = {}
    return metadata, body


def dump_frontmatter(metadata: dict[str, Any], body: str) -> str:
    """Serialize normalized frontmatter back to markdown."""
    cleaned_body = body.lstrip("\n")
    return "\n".join(
        [
            "---",
            yaml.safe_dump(metadata, sort_keys=False).strip(),
            "---",
            "",
            cleaned_body.rstrip(),
            "",
        ]
    )


def path_for_display(path: Path) -> str:
    """Return a stable display path for repo-local and external vault files."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def is_configured_value(value: Any) -> bool:
    """Treat obvious placeholder values as missing setup."""
    if value is None:
        return False
    if isinstance(value, Path):
        return True

    text = str(value).strip()
    if not text:
        return False

    lowered = text.lower()
    if lowered in {"none", "null", "false", "todo"}:
        return False
    return not any(fragment in lowered for fragment in PLACEHOLDER_FRAGMENTS)


def slugify_filename(value: str, *, fallback: str = "TASK") -> str:
    """Build readable uppercase filename fragments."""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.upper()).strip("_")
    return slug[:48] or fallback


def scrub_text(value: str) -> str:
    """Collapse markdown and HTML into plain text for previews."""
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", value)
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"(?m)^#+\s*", "", text)
    text = re.sub(r"[*_`>\-\[\]\(\)]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def age_label(modified_at: float) -> str:
    """Return a compact age label for the UI."""
    delta = datetime.now(timezone.utc) - datetime.fromtimestamp(modified_at, timezone.utc)
    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def hours_since(modified_at: float) -> float:
    """Return the age of a file in fractional hours."""
    delta = datetime.now(timezone.utc) - datetime.fromtimestamp(modified_at, timezone.utc)
    return round(delta.total_seconds() / 3600, 1)


def item_title(path: Path, metadata: dict[str, Any], body: str) -> str:
    """Choose the most useful item title."""
    for key in ("subject", "original_subject", "title", "from_name", "contact_name"):
        value = metadata.get(key)
        if value:
            return str(value)

    for line in body.splitlines():
        cleaned = line.strip()
        if cleaned.startswith("**Subject**:"):
            return cleaned.split(":", 1)[1].strip()
        if cleaned.startswith("## ") and len(cleaned) > 3:
            return cleaned.replace("## ", "", 1)

    return path.stem.replace("_", " ")


def item_owner(metadata: dict[str, Any]) -> str:
    """Best-effort actor/source string for a queue item."""
    for key in ("from", "original_from", "from_name", "contact_name", "platform"):
        value = metadata.get(key)
        if value:
            return str(value)
    return "DigitalFTE"


def infer_priority(metadata: dict[str, Any], body: str) -> str:
    """Infer priority when it is not explicitly set."""
    for key in ("priority", "urgency"):
        value = metadata.get(key)
        if value:
            lowered = str(value).lower()
            if lowered in {"high", "urgent"}:
                return "high"
            if lowered in {"low", "info"}:
                return "low"
            return "medium"

    lowered = body.lower()
    if any(token in lowered for token in ["urgent", "asap", "critical", "payment", "invoice"]):
        return "high"
    return "medium"


def read_item(path: Path, queue_key: str, include_content: bool = True) -> dict[str, Any]:
    """Read and normalize a vault markdown item."""
    content = path.read_text(encoding="utf-8")
    metadata, body = split_frontmatter(content)
    cleaned = scrub_text(body)
    title = item_title(path, metadata, body)
    payload = {
        "filename": path.name,
        "queue": queue_key,
        "queue_label": DISPLAY_NAMES[queue_key],
        "path": path_for_display(path),
        "title": title,
        "owner": item_owner(metadata),
        "priority": infer_priority(metadata, body),
        "type": str(metadata.get("type", "note")),
        "status": str(metadata.get("status", queue_key)),
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        "age": age_label(path.stat().st_mtime),
        "preview": cleaned[:220],
        "metadata": metadata,
    }
    if include_content:
        payload["content"] = content
    return payload


def queue_path(vault: Path, queue_key: str) -> Path:
    """Resolve a queue key into its directory path."""
    if queue_key not in QUEUE_DIRS:
        raise HTTPException(status_code=404, detail=f"Unknown queue '{queue_key}'")
    directory = vault / QUEUE_DIRS[queue_key]
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def find_item(vault: Path, queue_key: str, filename: str) -> Path:
    """Resolve an item path safely."""
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    path = queue_path(vault, queue_key) / safe_name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Item '{filename}' not found")
    return path


def process_running(pattern: str) -> bool:
    """Check whether a process matching the pattern is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", pattern],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


def port_open(host: str, port: int) -> bool:
    """Check whether a TCP port is reachable."""
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except OSError:
        return False


def setup_status() -> list[dict[str, Any]]:
    """Return grouped setup readiness information."""
    results: list[dict[str, Any]] = []
    for group_name, checks in SETUP_GROUPS:
        items = []
        for key, label in checks:
            value = os.getenv(key)
            if key == "VAULT_PATH":
                value = get_vault_path()
            ready = is_configured_value(value)
            items.append(
                {
                    "key": key,
                    "label": label,
                    "ready": ready,
                }
            )
        ready_count = sum(1 for item in items if item["ready"])
        results.append(
            {
                "name": group_name,
                "items": items,
                "ready_count": ready_count,
                "total": len(items),
                "ready": ready_count == len(items),
            }
        )
    return results


def service_status() -> list[dict[str, Any]]:
    """Return process and port visibility for core services."""
    services = []
    for name, pattern in PROCESS_PATTERNS.items():
        host, port = PORT_CHECKS.get(name, ("127.0.0.1", 0))
        services.append(
            {
                "name": name,
                "label": name.replace("_", " ").title(),
                "running": process_running(pattern),
                "reachable": port_open(host, port) if port else False,
                "port": port,
            }
        )
    odoo_reachable = port_open(*PORT_CHECKS["odoo"])
    services.append(
        {
            "name": "odoo",
            "label": "Odoo",
            "running": odoo_reachable,
            "reachable": odoo_reachable,
            "port": PORT_CHECKS["odoo"][1],
        }
    )
    return services


def recent_activity(vault: Path, limit: int = 10) -> list[dict[str, Any]]:
    """Return the newest items across the major vault queues."""
    items = []
    for queue_key in QUEUE_DIRS:
        directory = queue_path(vault, queue_key)
        for path in directory.glob("*.md"):
            items.append(read_item(path, queue_key, include_content=False))
    items.sort(key=lambda item: item["modified_at"], reverse=True)
    return items[:limit]


def activity_metrics(vault: Path) -> dict[str, Any]:
    """Aggregate vault-derived activity metrics."""
    done_dir = queue_path(vault, "done")
    done_files = list(done_dir.glob("*.md"))
    last_week = datetime.now(timezone.utc) - timedelta(days=7)
    recent_done = [
        path for path in done_files if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) >= last_week
    ]

    by_prefix = Counter(path.name.split("_", 1)[0] for path in recent_done)
    pending_age = [
        datetime.now(timezone.utc) - datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        for path in queue_path(vault, "pending_approval").glob("*.md")
    ]
    avg_pending_hours = round(
        sum(delta.total_seconds() for delta in pending_age) / max(len(pending_age), 1) / 3600,
        1,
    )
    oldest_pending_hours = max((round(delta.total_seconds() / 3600, 1) for delta in pending_age), default=0)
    needs_action_ages = [
        datetime.now(timezone.utc) - datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        for path in queue_path(vault, "needs_action").glob("*.md")
    ]
    oldest_needs_action_hours = max(
        (round(delta.total_seconds() / 3600, 1) for delta in needs_action_ages),
        default=0,
    )

    return {
        "done_last_7_days": len(recent_done),
        "emails_last_7_days": by_prefix.get("EMAIL", 0),
        "messages_last_7_days": by_prefix.get("WHATSAPP", 0),
        "social_last_7_days": sum(
            by_prefix.get(prefix, 0) for prefix in ["FACEBOOK", "LINKEDIN", "TWITTER", "POST"]
        ),
        "avg_pending_hours": avg_pending_hours if pending_age else 0,
        "oldest_pending_hours": oldest_pending_hours,
        "oldest_needs_action_hours": oldest_needs_action_hours,
        "briefings": len(list((vault / "Briefings").glob("*_briefing.md"))),
    }


def queue_counts(vault: Path) -> dict[str, int]:
    """Count queue items by stage."""
    counts = {}
    for queue_key in QUEUE_DIRS:
        counts[queue_key] = len(list(queue_path(vault, queue_key).glob("*.md")))
    return counts


def recommended_actions(
    vault: Path,
    *,
    counts: dict[str, int] | None = None,
    setup: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Generate short operational recommendations from current state."""
    if counts is None:
        counts = queue_counts(vault)
    actions = []
    if counts["failed"]:
        actions.append(f"Inspect {counts['failed']} failed action(s) before retrying.")
    if counts["pending_approval"]:
        actions.append(f"Review {counts['pending_approval']} pending approval item(s).")
    if counts["needs_action"]:
        actions.append(f"Triage {counts['needs_action']} incoming task(s) in Needs Action.")
    if counts["approved"]:
        actions.append(f"Execute {counts['approved']} approved item(s) waiting to run.")
    if setup is None:
        setup = setup_status()
    incomplete = [group["name"] for group in setup if not group["ready"]]
    if incomplete:
        actions.append(f"Finish setup for: {', '.join(incomplete[:3])}.")
    if not actions:
        actions.append("Inbox is clear. Use Quick Capture to add your next task.")
    return actions[:3]


def recent_audit_entries(vault: Path, limit: int = 8) -> list[dict[str, Any]]:
    """Read the newest structured audit events from the vault logs directory."""
    logs_dir = vault / "Logs"
    if not logs_dir.exists():
        return []

    entries: list[dict[str, Any]] = []
    log_files = sorted(
        [*logs_dir.glob("*.json"), *logs_dir.glob("*.jsonl")],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    for log_file in log_files:
        try:
            for raw_line in reversed(log_file.read_text(encoding="utf-8").splitlines()):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                timestamp = str(payload.get("timestamp") or payload.get("created_at") or "")
                entries.append(
                    {
                        "timestamp": timestamp,
                        "actor": str(payload.get("actor") or "system"),
                        "action": str(payload.get("action_type") or payload.get("action") or "event"),
                        "result": str(payload.get("result") or payload.get("status") or "recorded"),
                        "details": payload.get("details") if isinstance(payload.get("details"), dict) else {},
                    }
                )
                if len(entries) >= limit * 3:
                    break
        except OSError:
            continue
        if len(entries) >= limit * 3:
            break

    def parse_timestamp(value: str) -> datetime:
        if not value:
            return datetime.fromtimestamp(0, timezone.utc)
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return datetime.fromtimestamp(0, timezone.utc)

    entries.sort(key=lambda item: parse_timestamp(item["timestamp"]), reverse=True)
    return entries[:limit]


def assistant_brief(
    vault: Path,
    *,
    counts: dict[str, int] | None = None,
    metrics: dict[str, Any] | None = None,
    services: list[dict[str, Any]] | None = None,
    setup: list[dict[str, Any]] | None = None,
    recommendations: list[str] | None = None,
) -> dict[str, Any]:
    """Build a concise assistant-style operational brief from local state."""
    if counts is None:
        counts = queue_counts(vault)
    if metrics is None:
        metrics = activity_metrics(vault)
    if services is None:
        services = service_status()
    if setup is None:
        setup = setup_status()
    if recommendations is None:
        recommendations = recommended_actions(vault, counts=counts, setup=setup)

    hotspots = []
    if counts["needs_action"] >= 3:
        hotspots.append(f"Needs Action is building up with {counts['needs_action']} open items.")
    if counts["pending_approval"] >= 2:
        hotspots.append(f"Approval queue has {counts['pending_approval']} items waiting on you.")
    if counts["approved"] >= 1:
        hotspots.append(f"{counts['approved']} approved item(s) are ready for execution.")
    if counts["failed"] >= 1:
        hotspots.append(f"{counts['failed']} action(s) failed and need review.")

    blockers = [group["name"] for group in setup if not group["ready"]]
    service_alerts = [
        service["label"]
        for service in services
        if not service["running"] and not service["reachable"]
    ]

    stale_items = []
    for queue_key in ("pending_approval", "needs_action", "approved", "failed"):
        for path in queue_path(vault, queue_key).glob("*.md"):
            item = read_item(path, queue_key, include_content=False)
            item["age_hours"] = hours_since(path.stat().st_mtime)
            stale_items.append(item)
    stale_items.sort(key=lambda item: item["age_hours"], reverse=True)

    mood = "stable"
    if blockers or service_alerts or counts["pending_approval"] >= 3 or counts["failed"]:
        mood = "attention"
    if counts["needs_action"] >= 6 or counts["approved"] >= 3:
        mood = "pressure"

    summary_parts = []
    if counts["pending_approval"]:
        summary_parts.append(f"{counts['pending_approval']} approval(s) waiting")
    if counts["approved"]:
        summary_parts.append(f"{counts['approved']} execution-ready")
    if counts["failed"]:
        summary_parts.append(f"{counts['failed']} failed")
    if counts["done"]:
        summary_parts.append(f"{counts['done']} completed items on record")
    if not summary_parts:
        summary_parts.append("queues are clear")

    return {
        "mood": mood,
        "summary": " | ".join(summary_parts),
        "hotspots": hotspots[:3],
        "setup_blockers": blockers[:4],
        "service_alerts": service_alerts[:4],
        "stale_items": stale_items[:5],
        "audit_feed": recent_audit_entries(vault, limit=6),
        "recommended_actions": recommendations,
        "metrics": {
            "oldest_pending_hours": metrics["oldest_pending_hours"],
            "oldest_needs_action_hours": metrics["oldest_needs_action_hours"],
            "avg_pending_hours": metrics["avg_pending_hours"],
        },
    }


def update_item_status(path: Path, target_key: str) -> None:
    """Persist workflow state transitions inside the moved markdown item."""
    content = path.read_text(encoding="utf-8")
    metadata, body = split_frontmatter(content)
    metadata["status"] = target_key
    metadata["queue"] = target_key
    metadata["updated"] = datetime.now(timezone.utc).isoformat()
    path.write_text(dump_frontmatter(metadata, body), encoding="utf-8")


def generate_briefing_markdown(vault: Path) -> Path:
    """Generate a compact weekly briefing from local vault activity."""
    metrics = activity_metrics(vault)
    counts = queue_counts(vault)
    lines = [
        "# Monday Morning CEO Briefing",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Executive Summary",
        "",
        f"- Completed in the last 7 days: **{metrics['done_last_7_days']}**",
        f"- Open work right now: **{counts['needs_action'] + counts['pending_approval']}**",
        f"- Approval backlog age: **{metrics['avg_pending_hours']} hours avg**",
        "",
        "## Communication Stats",
        "",
        "| Channel | Count |",
        "|---------|-------|",
        f"| Email | {metrics['emails_last_7_days']} |",
        f"| WhatsApp | {metrics['messages_last_7_days']} |",
        f"| Social | {metrics['social_last_7_days']} |",
        "",
        "## Financial",
        "",
        "- Odoo remains the source of truth for invoices and books.",
        "- Use the control center setup panel to confirm finance credentials before automation.",
        "",
        "## Attention Now",
        "",
    ]
    for action in recommended_actions(vault):
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "## Queue Snapshot",
            "",
            "| Stage | Count |",
            "|-------|-------|",
            f"| Needs Action | {counts['needs_action']} |",
            f"| Pending Approval | {counts['pending_approval']} |",
            f"| Approved | {counts['approved']} |",
            f"| Failed | {counts['failed']} |",
            f"| Done | {counts['done']} |",
            "",
            "*Generated by the DigitalFTE Control Center.*",
        ]
    )

    briefings_dir = vault / "Briefings"
    briefings_dir.mkdir(parents=True, exist_ok=True)
    target = briefings_dir / f"{datetime.now().strftime('%Y-%m-%d')}_briefing.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def write_dashboard_markdown(vault: Path) -> Path:
    """Write a richer markdown dashboard for Obsidian users."""
    counts = queue_counts(vault)
    metrics = activity_metrics(vault)
    recent = recent_activity(vault, limit=6)
    setup = setup_status()

    lines = [
        "# Digital FTE Dashboard",
        "",
        f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Control Center**: http://127.0.0.1:{DEFAULT_PORT}",
        "",
        "## Quick Stats",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Needs Action | {counts['needs_action']} |",
        f"| Pending Approval | {counts['pending_approval']} |",
        f"| Failed | {counts['failed']} |",
        f"| Done This Week | {metrics['done_last_7_days']} |",
        f"| Briefings Generated | {metrics['briefings']} |",
        "",
        "## System Status",
        "",
    ]
    for service in service_status():
        label = "Online" if service["running"] or service["reachable"] else "Idle"
        lines.append(f"- **{service['label']}**: {label}")

    lines.extend(
        [
            "",
            "## Setup Readiness",
            "",
        ]
    )
    for group in setup:
        lines.append(f"- **{group['name']}**: {group['ready_count']}/{group['total']} configured")

    lines.extend(
        [
            "",
            "## Recent Activity",
            "",
        ]
    )
    for item in recent:
        lines.append(f"- **{item['queue_label']}**: {item['title']} ({item['age']})")

    lines.extend(
        [
            "",
            "## Suggested Next Moves",
            "",
        ]
    )
    for action in recommended_actions(vault):
        lines.append(f"- {action}")

    lines.extend(
        [
            "",
            "*Auto-updated by the DigitalFTE Control Center.*",
        ]
    )

    dashboard = vault / "Dashboard.md"
    dashboard.write_text("\n".join(lines), encoding="utf-8")
    return dashboard


def overview_payload(vault: Path) -> dict[str, Any]:
    """Build the complete control center overview payload."""
    counts = queue_counts(vault)
    metrics = activity_metrics(vault)
    setup = setup_status()
    services = service_status()
    recommendations = recommended_actions(vault, counts=counts, setup=setup)
    backlog = (
        counts["needs_action"]
        + counts["pending_approval"]
        + counts["approved"]
        + counts["failed"]
    )
    queues = [
        {
            "key": queue_key,
            "label": DISPLAY_NAMES[queue_key],
            "count": count,
        }
        for queue_key, count in counts.items()
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "vault_path": str(vault),
        "headline": {
            "backlog": backlog,
            "approvals": counts["pending_approval"],
            "completed": metrics["done_last_7_days"],
            "briefings": metrics["briefings"],
        },
        "queues": queues,
        "metrics": metrics,
        "setup": setup,
        "services": services,
        "recent_activity": recent_activity(vault, limit=8),
        "recommended_actions": recommendations,
        "assistant_brief": assistant_brief(
            vault,
            counts=counts,
            metrics=metrics,
            services=services,
            setup=setup,
            recommendations=recommendations,
        ),
    }


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Ensure the vault exists and refresh the markdown dashboard on boot."""
    vault = get_vault_path()
    ensure_vault_structure(vault)
    write_dashboard_markdown(vault)
    yield


app = FastAPI(title="DigitalFTE Control Center", version="1.0.0", lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the control center UI."""
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/api/overview")
async def api_overview() -> dict[str, Any]:
    """Return a single payload for the home screen."""
    vault = get_vault_path()
    ensure_vault_structure(vault)
    return overview_payload(vault)


@app.get("/api/queues/{queue_key}")
async def api_queue(queue_key: str) -> dict[str, Any]:
    """Return all items for a queue."""
    vault = get_vault_path()
    directory = queue_path(vault, queue_key)
    items = [
        read_item(path, queue_key, include_content=False)
        for path in sorted(directory.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True)
    ]
    return {
        "queue": queue_key,
        "label": DISPLAY_NAMES[queue_key],
        "items": items,
    }


@app.get("/api/items/{queue_key}/{filename}")
async def api_item(queue_key: str, filename: str) -> dict[str, Any]:
    """Return a single queue item."""
    vault = get_vault_path()
    path = find_item(vault, queue_key, filename)
    return read_item(path, queue_key)


@app.post("/api/items/{queue_key}/{filename}/move")
async def api_move(queue_key: str, filename: str, request: MoveRequest) -> dict[str, Any]:
    """Move a queue item between vault stages."""
    vault = get_vault_path()
    source = find_item(vault, queue_key, filename)
    target_key = request.target.lower().strip()
    target_dir_name = QUEUE_DESTINATIONS.get(target_key, request.target)
    target_dir = vault / target_dir_name
    if target_dir_name not in QUEUE_DIRS.values():
        raise HTTPException(status_code=400, detail=f"Unknown target '{request.target}'")

    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / source.name
    source.rename(destination)
    update_item_status(destination, target_key)
    write_dashboard_markdown(vault)
    return {
        "ok": True,
        "from": queue_key,
        "to": target_dir_name,
        "filename": destination.name,
    }


@app.post("/api/actions/capture")
async def api_capture(request: CaptureRequest) -> dict[str, Any]:
    """Create a new operator task directly in the vault."""
    vault = get_vault_path()
    ensure_vault_structure(vault)

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
    prefix = slugify_filename(request.capture_type, fallback="TASK")
    title_slug = slugify_filename(request.title, fallback="REQUEST")
    filename = f"{prefix}_MANUAL_{title_slug}_{timestamp}.md"
    target = vault / "Needs_Action" / filename
    metadata = {
        "type": request.capture_type.lower(),
        "title": request.title.strip(),
        "created": now.astimezone(timezone.utc).isoformat(),
        "priority": request.priority.lower(),
        "status": "needs_action",
        "source": "control_center",
    }
    body = "\n".join(
        [
            "## Request",
            "",
            request.details.strip(),
            "",
            "## Actions",
            "",
            "- [ ] Review request",
            "- [ ] Decide next step",
            "- [ ] Move to Pending Approval or Done",
        ]
    )
    target.write_text(dump_frontmatter(metadata, body), encoding="utf-8")
    write_dashboard_markdown(vault)
    return {"ok": True, "filename": filename}


@app.post("/api/actions/briefing")
async def api_briefing() -> dict[str, Any]:
    """Generate a new briefing markdown file."""
    vault = get_vault_path()
    ensure_vault_structure(vault)
    briefing = generate_briefing_markdown(vault)
    write_dashboard_markdown(vault)
    return {"ok": True, "path": path_for_display(briefing)}


@app.post("/api/actions/dashboard")
async def api_dashboard_refresh() -> dict[str, Any]:
    """Refresh the markdown dashboard snapshot."""
    vault = get_vault_path()
    ensure_vault_structure(vault)
    dashboard = write_dashboard_markdown(vault)
    return {"ok": True, "path": path_for_display(dashboard)}


@app.get("/api/health")
async def api_health() -> dict[str, Any]:
    """Simple health endpoint."""
    return {"status": "ok", "service": "digitalfte-control-center"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("control_center.server:app", host="127.0.0.1", port=DEFAULT_PORT, reload=False)
