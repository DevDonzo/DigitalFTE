const state = {
  overview: null,
  activeQueue: "needs_action",
  selected: null,
  queueItems: [],
  autoRefresh: true,
  refreshing: false,
  actionBusy: false,
};

const nodes = {
  assistantHotspots: document.getElementById("assistantHotspots"),
  assistantMetrics: document.getElementById("assistantMetrics"),
  assistantMood: document.getElementById("assistantMood"),
  assistantSummary: document.getElementById("assistantSummary"),
  auditFeed: document.getElementById("auditFeed"),
  autoRefreshButton: document.getElementById("autoRefreshButton"),
  briefingButton: document.getElementById("briefingButton"),
  captureForm: document.getElementById("captureForm"),
  copyMarkdownButton: document.getElementById("copyMarkdownButton"),
  dashboardButton: document.getElementById("dashboardButton"),
  heroMetrics: document.getElementById("heroMetrics"),
  previewBody: document.getElementById("previewBody"),
  previewChips: document.getElementById("previewChips"),
  previewMeta: document.getElementById("previewMeta"),
  previewPath: document.getElementById("previewPath"),
  previewTitle: document.getElementById("previewTitle"),
  queueBars: document.getElementById("queueBars"),
  queueFilter: document.getElementById("queueFilter"),
  queueList: document.getElementById("queueList"),
  queueStatus: document.getElementById("queueStatus"),
  queueTabs: document.getElementById("queueTabs"),
  recentFeed: document.getElementById("recentFeed"),
  recommendedActions: document.getElementById("recommendedActions"),
  refreshButton: document.getElementById("refreshButton"),
  servicesList: document.getElementById("servicesList"),
  setupGroups: document.getElementById("setupGroups"),
  staleRadar: document.getElementById("staleRadar"),
  systemLive: document.getElementById("systemLive"),
  toast: document.getElementById("toast"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function showToast(message, { error = false } = {}) {
  nodes.toast.textContent = message;
  nodes.toast.classList.toggle("is-error", error);
  nodes.toast.classList.add("is-visible");
  nodes.toast.setAttribute("role", error ? "alert" : "status");
  nodes.toast.setAttribute("aria-live", error ? "assertive" : "polite");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    nodes.toast.classList.remove("is-visible");
  }, 2200);
}

function reportError(error) {
  console.error(error);
  showToast(error?.message || "Something went wrong.", { error: true });
}

async function runSafely(action) {
  try {
    await action();
  } catch (error) {
    reportError(error);
  }
}

function formatIsoTime(value) {
  if (!value) {
    return "unknown";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function setActionBusy(busy) {
  state.actionBusy = busy;
  document.querySelectorAll("button").forEach((button) => {
    if (button.dataset.busySafe === "true") {
      return;
    }
    button.disabled = busy;
  });
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function renderLiveStatus() {
  if (!state.overview) {
    return;
  }
  nodes.systemLive.textContent = `Last sync ${formatIsoTime(state.overview.generated_at)} • auto-refresh ${
    state.autoRefresh ? "enabled" : "paused"
  }`;
  nodes.autoRefreshButton.textContent = `Auto-refresh: ${state.autoRefresh ? "on" : "off"}`;
  nodes.autoRefreshButton.setAttribute("aria-pressed", String(state.autoRefresh));
}

function renderHeroMetrics() {
  const metrics = state.overview.headline;
  const blocks = [
    ["Open backlog", metrics.backlog],
    ["Pending approvals", metrics.approvals],
    ["Completed this week", metrics.completed],
    ["Briefings on file", metrics.briefings],
  ];
  nodes.heroMetrics.innerHTML = blocks
    .map(
      ([label, value]) => `
        <div class="hero-metric">
          <strong>${escapeHtml(value)}</strong>
          <span>${escapeHtml(label)}</span>
        </div>
      `
    )
    .join("");
}

function renderQueueBars() {
  const max = Math.max(...state.overview.queues.map((queue) => queue.count), 1);
  nodes.queueBars.innerHTML = state.overview.queues
    .map(
      (queue) => `
        <div class="queue-bar">
          <div class="queue-bar-head">
            <strong>${escapeHtml(queue.label)}</strong>
            <span class="item-meta">${escapeHtml(queue.count)}</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width:${(queue.count / max) * 100}%"></div>
          </div>
        </div>
      `
    )
    .join("");
}

function renderServices() {
  nodes.servicesList.innerHTML = state.overview.services
    .map((service) => {
      const live = service.running || service.reachable;
      return `
        <div class="service-row">
          <div>
            <strong>${escapeHtml(service.label)}</strong>
            <div class="service-meta">${escapeHtml(
              service.port ? `port ${service.port}` : "background process"
            )}</div>
          </div>
          <span class="priority-pill ${live ? "priority-low" : "priority-medium"}">
            ${live ? "online" : "idle"}
          </span>
        </div>
      `;
    })
    .join("");
}

function renderRecommendedActions() {
  nodes.recommendedActions.innerHTML = state.overview.recommended_actions
    .map((item) => `<div class="action-row">${escapeHtml(item)}</div>`)
    .join("");
}

function renderAssistantBrief() {
  const brief = state.overview.assistant_brief;
  const moodClass = `mood-${brief.mood}`;

  nodes.assistantMood.innerHTML = `
    <span class="assistant-badge ${moodClass}">${escapeHtml(brief.mood)}</span>
  `;
  nodes.assistantSummary.innerHTML = `
    <strong>Operating readout</strong>
    <p>${escapeHtml(brief.summary)}</p>
  `;
  nodes.assistantHotspots.innerHTML = brief.hotspots.length
    ? brief.hotspots.map((item) => `<div class="assistant-row">${escapeHtml(item)}</div>`).join("")
    : `<div class="assistant-row">No immediate hotspots detected.</div>`;
  nodes.assistantMetrics.innerHTML = [
    ["Oldest pending", `${brief.metrics.oldest_pending_hours}h`],
    ["Oldest intake", `${brief.metrics.oldest_needs_action_hours}h`],
    ["Average approval lag", `${brief.metrics.avg_pending_hours}h`],
  ]
    .map(
      ([label, value]) => `
        <div class="assistant-metric">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `
    )
    .join("");

  nodes.staleRadar.innerHTML = brief.stale_items.length
    ? brief.stale_items
        .map(
          (item) => `
            <article class="stale-card">
              <div class="recent-item-head">
                <strong>${escapeHtml(item.queue_label)}</strong>
                <span class="item-meta">${escapeHtml(item.age)}</span>
              </div>
              <h3>${escapeHtml(item.title)}</h3>
              <div class="recent-meta">${escapeHtml(item.owner)} • ${escapeHtml(item.age_hours)}h old</div>
            </article>
          `
        )
        .join("")
    : `<div class="stale-card"><strong>No stale items.</strong><div class="recent-meta">Nothing aging badly right now.</div></div>`;

  nodes.auditFeed.innerHTML = brief.audit_feed.length
    ? brief.audit_feed
        .map(
          (entry) => `
            <article class="audit-card">
              <div class="recent-item-head">
                <strong>${escapeHtml(entry.action)}</strong>
                <span class="item-meta">${escapeHtml(formatIsoTime(entry.timestamp))}</span>
              </div>
              <div class="recent-meta">${escapeHtml(entry.actor)} • ${escapeHtml(entry.result)}</div>
            </article>
          `
        )
        .join("")
    : `<div class="audit-card"><strong>No audit events found.</strong><div class="recent-meta">Logs will appear here as the system works.</div></div>`;
}

function renderQueueTabs() {
  const focusedQueue = document.activeElement?.dataset?.queue;
  nodes.queueTabs.innerHTML = state.overview.queues
    .map(
      (queue) => `
        <button type="button" class="queue-tab ${queue.key === state.activeQueue ? "is-active" : ""}" data-queue="${escapeHtml(
          queue.key
        )}" aria-pressed="${queue.key === state.activeQueue}" aria-controls="queueList">
          ${escapeHtml(queue.label)} · ${escapeHtml(queue.count)}
        </button>
      `
    )
    .join("");

  nodes.queueTabs.querySelectorAll("[data-queue]").forEach((button) => {
    button.addEventListener("click", () =>
      runSafely(async () => {
        state.activeQueue = button.dataset.queue;
        await loadQueue();
      })
    );
  });

  if (focusedQueue) {
    nodes.queueTabs
      .querySelector(`[data-queue="${CSS.escape(focusedQueue)}"]`)
      ?.focus({ preventScroll: true });
  }
}

function filteredQueueItems() {
  const term = nodes.queueFilter.value.trim().toLowerCase();
  if (!term) {
    return state.queueItems;
  }
  return state.queueItems.filter((item) =>
    [item.title, item.owner, item.preview].some((value) =>
      String(value || "").toLowerCase().includes(term)
    )
  );
}

function renderQueueList() {
  const focusedFile = document.activeElement?.dataset?.file;
  const items = filteredQueueItems();
  nodes.queueStatus.textContent = `${items.length} queue item${items.length === 1 ? "" : "s"} shown.`;
  nodes.queueList.innerHTML = items.length
    ? items
        .map(
          (item) => `
            <button type="button" class="queue-item ${
              state.selected?.filename === item.filename ? "is-active" : ""
            }" data-file="${encodeURIComponent(item.filename)}" aria-pressed="${
              state.selected?.filename === item.filename
            }">
              <span class="queue-bar-head">
                <span class="queue-title">${escapeHtml(item.title)}</span>
                <span class="priority-pill priority-${escapeHtml(item.priority)}">${escapeHtml(
                  item.priority
                )}</span>
              </span>
              <span class="item-meta">${escapeHtml(item.owner)} · ${escapeHtml(item.age)}</span>
              <span class="item-preview">${escapeHtml(item.preview || "No preview available.")}</span>
            </button>
          `
        )
        .join("")
    : `<div class="empty-state"><strong>No items match this filter.</strong><p class="item-preview">Try a different queue or clear the search box.</p></div>`;

  nodes.queueList.querySelectorAll("[data-file]").forEach((itemNode) => {
    itemNode.addEventListener("click", () =>
      runSafely(async () => {
        const item = state.queueItems.find(
          (entry) => entry.filename === decodeURIComponent(itemNode.dataset.file)
        );
        if (!item) {
          return;
        }
        state.selected = await api(
          `/api/items/${state.activeQueue}/${encodeURIComponent(item.filename)}`
        );
        renderQueueList();
        renderPreview();
      })
    );
  });

  if (focusedFile) {
    nodes.queueList
      .querySelector(`[data-file="${CSS.escape(focusedFile)}"]`)
      ?.focus({ preventScroll: true });
  }
}

function renderPreview() {
  if (!state.selected) {
    nodes.previewMeta.textContent = "Select a queue item to inspect it.";
    nodes.previewPath.textContent = "";
    nodes.previewTitle.textContent = "No item selected";
    nodes.previewBody.textContent = "Nothing selected yet.";
    nodes.previewChips.innerHTML = "";
    return;
  }

  const item = state.selected;
  nodes.previewMeta.textContent = `${item.queue_label} • ${item.owner} • ${item.age}`;
  nodes.previewPath.textContent = item.path;
  nodes.previewTitle.textContent = item.title;
  nodes.previewBody.textContent = item.content;
  nodes.previewChips.innerHTML = [item.priority, item.type, item.status, item.filename]
    .map((value) => `<span class="chip">${escapeHtml(value)}</span>`)
    .join("");
}

function renderSetup() {
  nodes.setupGroups.innerHTML = state.overview.setup
    .map(
      (group) => `
        <div class="setup-group">
          <div class="queue-bar-head">
            <strong>${escapeHtml(group.name)}</strong>
            <span class="item-meta">${escapeHtml(group.ready_count)}/${escapeHtml(group.total)}</span>
          </div>
          ${group.items
            .map(
              (item) => `
                <div class="setup-item">
                  <span><span class="status-dot ${
                    item.ready ? "status-ready" : "status-missing"
                  }"></span>${escapeHtml(item.label)}</span>
                  <strong>${item.ready ? "ready" : "missing"}</strong>
                </div>
              `
            )
            .join("")}
        </div>
      `
    )
    .join("");
}

function renderRecentFeed() {
  nodes.recentFeed.innerHTML = state.overview.recent_activity
    .map(
      (item) => `
        <div class="recent-item">
          <div class="recent-item-head">
            <strong>${escapeHtml(item.queue_label)}</strong>
            <span class="item-meta">${escapeHtml(item.age)}</span>
          </div>
          <h3>${escapeHtml(item.title)}</h3>
          <div class="recent-meta">${escapeHtml(item.owner)}</div>
        </div>
      `
    )
    .join("");
}

async function loadOverview() {
  state.overview = await api("/api/overview");
  renderLiveStatus();
  renderHeroMetrics();
  renderQueueBars();
  renderServices();
  renderRecommendedActions();
  renderSetup();
  renderRecentFeed();
  renderAssistantBrief();
}

async function loadQueue() {
  const payload = await api(`/api/queues/${state.activeQueue}`);
  state.queueItems = payload.items;

  const selectedFilename = state.selected?.filename;
  const stillVisible = selectedFilename
    ? payload.items.find((item) => item.filename === selectedFilename)
    : null;
  const nextItem = stillVisible || payload.items[0] || null;

  const selectedIsCurrent =
    nextItem &&
    state.selected?.filename === nextItem.filename &&
    state.selected?.modified_at === nextItem.modified_at;

  state.selected = nextItem
    ? selectedIsCurrent
      ? state.selected
      : await api(`/api/items/${state.activeQueue}/${encodeURIComponent(nextItem.filename)}`)
    : null;

  renderQueueTabs();
  renderQueueList();
  renderPreview();
}

async function refreshAll({ showMessage = false } = {}) {
  if (state.refreshing) {
    return;
  }
  state.refreshing = true;
  try {
    await loadOverview();
    await loadQueue();
    if (showMessage) {
      showToast("Live state refreshed.");
    }
  } finally {
    state.refreshing = false;
  }
}

async function moveSelected(target) {
  if (!state.selected) {
    showToast("Select an item first.");
    return;
  }

  setActionBusy(true);
  try {
    await api(
      `/api/items/${state.activeQueue}/${encodeURIComponent(state.selected.filename)}/move`,
      {
        method: "POST",
        body: JSON.stringify({ target }),
      }
    );
    showToast(`Moved to ${target.replace("_", " ")}.`);
    await refreshAll();
  } finally {
    setActionBusy(false);
  }
}

async function submitCapture(event) {
  event.preventDefault();
  const formData = new FormData(nodes.captureForm);
  const payload = Object.fromEntries(formData.entries());

  setActionBusy(true);
  try {
    await api("/api/actions/capture", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    nodes.captureForm.reset();
    showToast("New vault item created.");
    state.activeQueue = "needs_action";
    await refreshAll();
  } finally {
    setActionBusy(false);
  }
}

async function copySelectedMarkdown() {
  if (!state.selected) {
    showToast("Select an item first.");
    return;
  }
  await navigator.clipboard.writeText(state.selected.content);
  showToast("Markdown copied.");
}

async function boot() {
  await refreshAll();

  nodes.refreshButton.addEventListener("click", async () => {
    await runSafely(() => refreshAll({ showMessage: true }));
  });

  nodes.autoRefreshButton.dataset.busySafe = "true";
  nodes.autoRefreshButton.addEventListener("click", () => {
    state.autoRefresh = !state.autoRefresh;
    renderLiveStatus();
    showToast(`Auto-refresh ${state.autoRefresh ? "enabled" : "paused"}.`);
  });

  nodes.briefingButton.addEventListener("click", async () => {
    await runSafely(async () => {
      setActionBusy(true);
      try {
        const result = await api("/api/actions/briefing", { method: "POST" });
        await refreshAll();
        showToast(`Briefing generated: ${result.path}`);
      } finally {
        setActionBusy(false);
      }
    });
  });

  nodes.dashboardButton.addEventListener("click", async () => {
    await runSafely(async () => {
      setActionBusy(true);
      try {
        await api("/api/actions/dashboard", { method: "POST" });
        await refreshAll();
        showToast("Vault dashboard refreshed.");
      } finally {
        setActionBusy(false);
      }
    });
  });

  document.querySelectorAll("[data-move]").forEach((button) => {
    button.addEventListener("click", () => runSafely(() => moveSelected(button.dataset.move)));
  });

  nodes.copyMarkdownButton.addEventListener("click", () => runSafely(copySelectedMarkdown));
  nodes.queueFilter.addEventListener("input", renderQueueList);
  nodes.captureForm.addEventListener("submit", (event) => runSafely(() => submitCapture(event)));

  window.setInterval(async () => {
    if (!state.autoRefresh || document.hidden) {
      return;
    }
    try {
      await refreshAll();
    } catch (error) {
      reportError(error);
    }
  }, 30000);
}

boot().catch((error) => {
  reportError(error);
});
