"""FastAPI control center for operating DigitalFTE locally."""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_VAULT = ROOT / "vault"
DEFAULT_PORT = int(os.getenv("CONTROL_CENTER_PORT", "8282"))

QUEUE_DIRS = {
    "needs_action": "Needs_Action",
    "pending_approval": "Pending_Approval",
    "approved": "Approved",
    "rejected": "Rejected",
    "done": "Done",
}

DISPLAY_NAMES = {
    "needs_action": "Needs Action",
    "pending_approval": "Pending Approval",
    "approved": "Approved",
    "rejected": "Rejected",
    "done": "Done",
}

QUEUE_DESTINATIONS = {
    "needs_action": "Needs_Action",
    "pending_approval": "Pending_Approval",
    "approved": "Approved",
    "rejected": "Rejected",
    "done": "Done",
}

PROCESS_PATTERNS = {
    "control_center": "scripts/control_center.py",
    "local_orchestrator": "agents/local_orchestrator.py",
    "orchestrator": "agents/orchestrator.py",
    "gmail_watcher": "agents/gmail_watcher.py",
    "webhook": "agents/webhook_server.py",
    "watchdog": "agents/watchdog.py",
}

PORT_CHECKS = {
    "control_center": ("127.0.0.1", DEFAULT_PORT),
    "webhook": ("127.0.0.1", int(os.getenv("WEBHOOK_PORT", "8001"))),
    "odoo": ("127.0.0.1", 8069),
}

SETUP_GROUPS = [
    (
        "Core Brain",
        [
            ("OPENAI_API_KEY", "OpenAI drafting"),
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
    for folder in ["Briefings", "Logs", "Accounting", "Inbox", "Plans"]:
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
        "path": str(path.relative_to(ROOT)),
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
                value = str(get_vault_path())
            ready = bool(value)
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
    services.append(
        {
            "name": "odoo",
            "label": "Odoo",
            "running": port_open(*PORT_CHECKS["odoo"]),
            "reachable": port_open(*PORT_CHECKS["odoo"]),
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

    return {
        "done_last_7_days": len(recent_done),
        "emails_last_7_days": by_prefix.get("EMAIL", 0),
        "messages_last_7_days": by_prefix.get("WHATSAPP", 0),
        "social_last_7_days": sum(
            by_prefix.get(prefix, 0) for prefix in ["FACEBOOK", "LINKEDIN", "TWITTER", "POST"]
        ),
        "avg_pending_hours": avg_pending_hours if pending_age else 0,
        "briefings": len(list((vault / "Briefings").glob("*_briefing.md"))),
    }


def queue_counts(vault: Path) -> dict[str, int]:
    """Count queue items by stage."""
    counts = {}
    for queue_key in QUEUE_DIRS:
        counts[queue_key] = len(list(queue_path(vault, queue_key).glob("*.md")))
    return counts


def recommended_actions(vault: Path) -> list[str]:
    """Generate short operational recommendations from current state."""
    counts = queue_counts(vault)
    actions = []
    if counts["pending_approval"]:
        actions.append(f"Review {counts['pending_approval']} pending approval item(s).")
    if counts["needs_action"]:
        actions.append(f"Triage {counts['needs_action']} incoming task(s) in Needs Action.")
    setup = setup_status()
    incomplete = [group["name"] for group in setup if not group["ready"]]
    if incomplete:
        actions.append(f"Finish setup for: {', '.join(incomplete[:3])}.")
    if not actions:
        actions.append("Inbox is clear. Use Quick Capture to add your next task.")
    return actions[:3]


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
    backlog = counts["needs_action"] + counts["pending_approval"] + counts["approved"]
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
        "setup": setup_status(),
        "services": service_status(),
        "recent_activity": recent_activity(vault, limit=8),
        "recommended_actions": recommended_actions(vault),
    }


app = FastAPI(title="DigitalFTE Control Center", version="1.0.0")
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.on_event("startup")
def startup() -> None:
    """Ensure the vault exists and refresh the markdown dashboard on boot."""
    vault = get_vault_path()
    ensure_vault_structure(vault)
    write_dashboard_markdown(vault)


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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = re.sub(r"[^A-Z]", "", request.capture_type.upper()) or "TASK"
    filename = f"{prefix}_MANUAL_{timestamp}.md"
    target = vault / "Needs_Action" / filename
    metadata = {
        "type": request.capture_type.lower(),
        "title": request.title.strip(),
        "created": datetime.now(timezone.utc).isoformat(),
        "priority": request.priority.lower(),
        "status": "pending",
        "source": "control_center",
    }
    content = "\n".join(
        [
            "---",
            yaml.safe_dump(metadata, sort_keys=False).strip(),
            "---",
            "",
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
    target.write_text(content + "\n", encoding="utf-8")
    write_dashboard_markdown(vault)
    return {"ok": True, "filename": filename}


@app.post("/api/actions/briefing")
async def api_briefing() -> dict[str, Any]:
    """Generate a new briefing markdown file."""
    vault = get_vault_path()
    ensure_vault_structure(vault)
    briefing = generate_briefing_markdown(vault)
    write_dashboard_markdown(vault)
    return {"ok": True, "path": str(briefing.relative_to(ROOT))}


@app.post("/api/actions/dashboard")
async def api_dashboard_refresh() -> dict[str, Any]:
    """Refresh the markdown dashboard snapshot."""
    vault = get_vault_path()
    ensure_vault_structure(vault)
    dashboard = write_dashboard_markdown(vault)
    return {"ok": True, "path": str(dashboard.relative_to(ROOT))}


@app.get("/api/health")
async def api_health() -> dict[str, Any]:
    """Simple health endpoint."""
    return {"status": "ok", "service": "digitalfte-control-center"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("control_center.server:app", host="127.0.0.1", port=DEFAULT_PORT, reload=False)
