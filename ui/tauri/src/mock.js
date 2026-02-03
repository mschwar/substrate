import { invoke } from "./bridge.js";

const state = {
  currentPath: null,
};

function getFilters() {
  const status = document.getElementById("filter-status").value;
  const privacy = document.getElementById("filter-privacy").value;
  return {
    status: status || null,
    privacy: privacy || null,
  };
}

async function fetchInbox() {
  const filters = getFilters();
  return invoke("inbox_view", {
    limit: 20,
    offset: 0,
    sort: "updated_desc",
    status: filters.status,
    privacy: filters.privacy,
  });
}

async function fetchItem(path) {
  return invoke("item_view", { path });
}

async function fetchSearch(query) {
  const filters = getFilters();
  return invoke("search", {
    query,
    limit: 20,
    offset: 0,
    status: filters.status,
    privacy: filters.privacy,
  });
}

async function captureNote(title, body) {
  return invoke("capture", { title, body });
}

async function promoteNote(path) {
  return invoke("promote", { path, status: "canonical" });
}

function renderInbox(payload) {
  const list = document.getElementById("inbox");
  list.innerHTML = "";
  if (!payload.items.length) {
    const empty = document.createElement("li");
    empty.className = "inbox-item";
    empty.textContent = "Inbox is empty";
    list.appendChild(empty);
    return;
  }

  payload.items.forEach((item) => {
    const li = document.createElement("li");
    li.className = "inbox-item";
    li.dataset.path = item.path;
    li.innerHTML = `
      <strong>${item.title || "(Untitled)"}</strong>
      <span>Status: ${item.status}</span>
      <span>Privacy: ${item.privacy}</span>
      <span>Updated: ${item.updated}</span>
    `;
    li.addEventListener("click", () => loadItem(item.path));
    list.appendChild(li);
  });
}

function renderItem(payload) {
  state.currentPath = payload.path;
  document.getElementById("item-title").textContent = payload.title || "(Untitled)";
  document.getElementById("item-meta").textContent = `${payload.type} · ${payload.status} · ${payload.privacy}`;
  document.getElementById("item-content").textContent = payload.body || "";
}

function renderSearch(payload) {
  const block = document.getElementById("search-block");
  const list = document.getElementById("search-results");
  list.innerHTML = "";
  block.style.display = "block";

  if (!payload.results.length) {
    const empty = document.createElement("li");
    empty.className = "search-item";
    empty.textContent = "No results";
    list.appendChild(empty);
    return;
  }

  payload.results.forEach((result) => {
    const li = document.createElement("li");
    li.className = "search-item";
    li.innerHTML = `
      <strong>${result.title || "(Untitled)"}</strong>
      <span>${result.type} · ${result.status} · ${result.privacy}</span>
      <span>${result.snippet || ""}</span>
    `;
    li.addEventListener("click", () => loadItem(result.path));
    list.appendChild(li);
  });
}

async function loadItem(path) {
  try {
    const payload = await fetchItem(path);
    renderItem(payload);
  } catch (err) {
    document.getElementById("item-title").textContent = "Failed to load";
    document.getElementById("item-meta").textContent = String(err);
    document.getElementById("item-content").textContent = "";
  }
}

async function refreshInbox() {
  const payload = await fetchInbox();
  renderInbox(payload);
  if (payload.items.length) {
    await loadItem(payload.items[0].path);
  }
}

function wireSearch() {
  const form = document.getElementById("search-form");
  const input = document.getElementById("search-input");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = input.value.trim();
    if (!query) {
      return;
    }
    try {
      const payload = await fetchSearch(query);
      renderSearch(payload);
    } catch (err) {
      document.getElementById("item-title").textContent = "Search failed";
      document.getElementById("item-meta").textContent = String(err);
    }
  });
}

function wireCapture() {
  const form = document.getElementById("capture-form");
  const titleInput = document.getElementById("capture-title");
  const bodyInput = document.getElementById("capture-body");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const title = titleInput.value.trim();
    const body = bodyInput.value.trim();
    if (!title) {
      return;
    }
    try {
      const payload = await captureNote(title, body);
      titleInput.value = "";
      bodyInput.value = "";
      await refreshInbox();
      await loadItem(payload.path);
    } catch (err) {
      document.getElementById("item-title").textContent = "Capture failed";
      document.getElementById("item-meta").textContent = String(err);
    }
  });
}

function wireFilters() {
  const status = document.getElementById("filter-status");
  const privacy = document.getElementById("filter-privacy");
  [status, privacy].forEach((select) => {
    select.addEventListener("change", () => {
      refreshInbox().catch(() => undefined);
    });
  });
}

function wirePromote() {
  const button = document.getElementById("promote-btn");
  button.addEventListener("click", async () => {
    if (!state.currentPath) {
      return;
    }
    try {
      const payload = await promoteNote(state.currentPath);
      await refreshInbox();
      await loadItem(payload.path);
    } catch (err) {
      document.getElementById("item-title").textContent = "Promote failed";
      document.getElementById("item-meta").textContent = String(err);
    }
  });
}

async function init() {
  try {
    await refreshInbox();
    wireSearch();
    wireCapture();
    wireFilters();
    wirePromote();
  } catch (err) {
    document.getElementById("item-title").textContent = "Failed to load inbox";
    document.getElementById("item-meta").textContent = String(err);
  }
}

init();
