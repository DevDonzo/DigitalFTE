const state = {
  overview: null,
  activeQueue: "needs_action",
  selected: null,
  queueItems: [],
};

const nodes = {
  heroMetrics: document.getElementById("heroMetrics"),
  queueBars: document.getElementById("queueBars"),
  servicesList: document.getElementById("servicesList"),
  recommendedActions: document.getElementById("recommendedActions"),
  queueTabs: document.getElementById("queueTabs"),
  queueList: document.getElementById("queueList"),
  queueFilter: document.getElementById("queueFilter"),
  previewMeta: document.getElementById("previewMeta"),
  previewTitle: document.getElementById("previewTitle"),
  previewChips: document.getElementById("previewChips"),
  previewBody: document.getElementById("previewBody"),
  setupGroups: document.getElementById("setupGroups"),
  captureForm: document.getElementById("captureForm"),
  recentFeed: document.getElementById("recentFeed"),
  toast: document.getElementById("toast"),
};

function showToast(message) {
  nodes.toast.textContent = message;
  nodes.toast.classList.add("is-visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    nodes.toast.classList.remove("is-visible");
  }, 2200);
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
          <strong>${value}</strong>
          <span>${label}</span>
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
            <strong>${queue.label}</strong>
            <span class="item-meta">${queue.count}</span>
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
            <strong>${service.label}</strong>
            <div class="service-meta">${service.port ? `port ${service.port}` : "background process"}</div>
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
    .map((item) => `<div class="action-row">${item}</div>`)
    .join("");
}

function renderQueueTabs() {
  nodes.queueTabs.innerHTML = state.overview.queues
    .map(
      (queue) => `
        <button class="queue-tab ${queue.key === state.activeQueue ? "is-active" : ""}" data-queue="${queue.key}">
          ${queue.label} · ${queue.count}
        </button>
      `
    )
    .join("");

  nodes.queueTabs.querySelectorAll("[data-queue]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeQueue = button.dataset.queue;
      loadQueue();
    });
  });
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
  const items = filteredQueueItems();
  nodes.queueList.innerHTML = items.length
    ? items
        .map(
          (item, index) => `
            <article class="queue-item ${state.selected?.filename === item.filename ? "is-active" : ""}" data-file="${encodeURIComponent(item.filename)}" style="animation-delay:${index * 30}ms">
              <div class="queue-bar-head">
                <h3>${item.title}</h3>
                <span class="priority-pill priority-${item.priority}">${item.priority}</span>
              </div>
              <div class="item-meta">${item.owner} · ${item.age}</div>
              <p class="item-preview">${item.preview || "No preview available."}</p>
            </article>
          `
        )
        .join("")
    : `<div class="queue-item"><strong>No items match this filter.</strong><p class="item-preview">Try a different queue or clear the search box.</p></div>`;

  nodes.queueList.querySelectorAll("[data-file]").forEach((itemNode) => {
    itemNode.addEventListener("click", async () => {
      const item = state.queueItems.find(
        (entry) => entry.filename === decodeURIComponent(itemNode.dataset.file)
      );
      state.selected = await api(
        `/api/items/${state.activeQueue}/${encodeURIComponent(item.filename)}`
      );
      renderQueueList();
      renderPreview();
    });
  });
}

function renderPreview() {
  if (!state.selected) {
    nodes.previewMeta.textContent = "Select a queue item to inspect it.";
    nodes.previewTitle.textContent = "No item selected";
    nodes.previewBody.textContent = "Nothing selected yet.";
    nodes.previewChips.innerHTML = "";
    return;
  }

  const item = state.selected;
  nodes.previewMeta.textContent = `${item.queue_label} · ${item.owner} · ${item.age}`;
  nodes.previewTitle.textContent = item.title;
  nodes.previewBody.textContent = item.content;
  nodes.previewChips.innerHTML = [
    item.priority,
    item.type,
    item.status,
    item.filename,
  ]
    .map((value) => `<span class="chip">${value}</span>`)
    .join("");
}

function renderSetup() {
  nodes.setupGroups.innerHTML = state.overview.setup
    .map(
      (group) => `
        <div class="setup-group">
          <div class="queue-bar-head">
            <strong>${group.name}</strong>
            <span class="item-meta">${group.ready_count}/${group.total}</span>
          </div>
          ${group.items
            .map(
              (item) => `
                <div class="setup-item">
                  <span><span class="status-dot ${item.ready ? "status-ready" : "status-missing"}"></span>${item.label}</span>
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
            <strong>${item.queue_label}</strong>
            <span class="item-meta">${item.age}</span>
          </div>
          <h3>${item.title}</h3>
          <div class="recent-meta">${item.owner}</div>
        </div>
      `
    )
    .join("");
}

async function loadOverview() {
  state.overview = await api("/api/overview");
  renderHeroMetrics();
  renderQueueBars();
  renderServices();
  renderRecommendedActions();
  renderQueueTabs();
  renderSetup();
  renderRecentFeed();
}

async function loadQueue() {
  const payload = await api(`/api/queues/${state.activeQueue}`);
  state.queueItems = payload.items;
  state.selected = payload.items[0]
    ? await api(`/api/items/${state.activeQueue}/${encodeURIComponent(payload.items[0].filename)}`)
    : null;
  renderQueueTabs();
  renderQueueList();
  renderPreview();
}

async function moveSelected(target) {
  if (!state.selected) {
    showToast("Select an item first.");
    return;
  }

  await api(
    `/api/items/${state.activeQueue}/${encodeURIComponent(state.selected.filename)}/move`,
    {
      method: "POST",
      body: JSON.stringify({ target }),
    }
  );
  showToast(`Moved to ${target.replace("_", " ")}.`);
  await loadOverview();
  await loadQueue();
}

async function submitCapture(event) {
  event.preventDefault();
  const formData = new FormData(nodes.captureForm);
  const payload = Object.fromEntries(formData.entries());
  await api("/api/actions/capture", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  nodes.captureForm.reset();
  showToast("New vault item created.");
  await loadOverview();
  state.activeQueue = "needs_action";
  await loadQueue();
}

async function boot() {
  await loadOverview();
  await loadQueue();

  document.getElementById("refreshButton").addEventListener("click", async () => {
    await loadOverview();
    await loadQueue();
    showToast("Live state refreshed.");
  });

  document.getElementById("briefingButton").addEventListener("click", async () => {
    const result = await api("/api/actions/briefing", { method: "POST" });
    await loadOverview();
    showToast(`Briefing generated: ${result.path}`);
  });

  document.getElementById("dashboardButton").addEventListener("click", async () => {
    await api("/api/actions/dashboard", { method: "POST" });
    await loadOverview();
    showToast("Vault dashboard refreshed.");
  });

  document.querySelectorAll("[data-move]").forEach((button) => {
    button.addEventListener("click", () => moveSelected(button.dataset.move));
  });

  nodes.queueFilter.addEventListener("input", renderQueueList);
  nodes.captureForm.addEventListener("submit", submitCapture);

  window.setInterval(async () => {
    await loadOverview();
  }, 30000);
}

boot().catch((error) => {
  console.error(error);
  showToast(error.message);
});
