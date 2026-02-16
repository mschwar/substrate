import { invoke } from "./bridge.js";

const state = {
  currentPath: null,
  item: null,
  frontmatter: {},
  body: "",
  dirty: false,
  saving: false,
  dailyBusy: false,
  validation: {
    status: "idle",
    valid: true,
    errors: [],
    warnings: [],
  },
  validationTimer: null,
  validationSeq: 0,
  lastValidatedPayloadKey: null,
};

function getFilters() {
  const status = document.getElementById("filter-status").value;
  const privacy = document.getElementById("filter-privacy").value;
  return {
    status: status || null,
    privacy: privacy || null,
  };
}

function showError(message) {
  const banner = document.getElementById("banner");
  banner.textContent = message;
  banner.classList.remove("hidden");
}

function clearError() {
  const banner = document.getElementById("banner");
  banner.textContent = "";
  banner.classList.add("hidden");
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

async function validatePayload(payload) {
  return invoke("validate", payload);
}

async function updateItem(payload) {
  return invoke("item_update", payload);
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

async function openDaily(dateValue) {
  return invoke("daily_open", { date: dateValue || todayIso() });
}

async function appendDaily(text, dateValue) {
  return invoke("daily_append", { text, date: dateValue || todayIso() });
}

function setInputValue(id, value) {
  const input = document.getElementById(id);
  if (!input) {
    return;
  }
  input.value = value ?? "";
}

function clearEditor(message) {
  state.currentPath = null;
  state.item = null;
  state.frontmatter = {};
  state.body = "";
  state.dirty = false;
  state.saving = false;
  state.validation = { status: "idle", valid: true, errors: [] };
  state.validation.warnings = [];
  state.lastValidatedPayloadKey = null;

  setInputValue("fm-title", "");
  setInputValue("fm-type", "");
  setInputValue("fm-status", "");
  setInputValue("fm-privacy", "");
  setInputValue("fm-summary", "");
  setInputValue("fm-tags", "");
  setInputValue("fm-confidence", "");
  setInputValue("fm-schema", "");
  setInputValue("fm-id", "");
  setInputValue("fm-created", "");
  setInputValue("fm-updated", "");
  setInputValue("item-body", "");

  const title = document.getElementById("item-title");
  const meta = document.getElementById("item-meta");
  if (title) {
    title.textContent = message || "Select an item";
  }
  if (meta) {
    meta.textContent = "";
  }

  const promoteInput = document.getElementById("promote-confirm");
  if (promoteInput) {
    promoteInput.value = "";
  }

  updateValidationUI();
  updateSaveState();
  updatePromoteState();
}

function applyItemToForm(payload) {
  const fm = payload.frontmatter || {};
  setInputValue("fm-title", fm.title ?? "");
  setInputValue("fm-summary", fm.summary ?? "");
  const tags = Array.isArray(fm.tags)
    ? fm.tags.join(", ")
    : fm.tags
      ? String(fm.tags)
      : "";
  setInputValue("fm-tags", tags);
  setInputValue("fm-type", fm.type ?? "");
  setInputValue("fm-status", fm.status ?? "");
  setInputValue("fm-privacy", fm.privacy ?? "");
  setInputValue("fm-confidence", fm.confidence ?? "");
  setInputValue("fm-schema", fm.schema_version ?? "");
  setInputValue("fm-id", fm.id ?? "");
  setInputValue("fm-created", fm.created ?? "");
  setInputValue("fm-updated", fm.updated ?? "");
  setInputValue("item-body", payload.body ?? "");
}

function updateItemHeader() {
  const titleEl = document.getElementById("item-title");
  const metaEl = document.getElementById("item-meta");
  if (!titleEl || !metaEl) {
    return;
  }
  const title = state.frontmatter.title || "(Untitled)";
  titleEl.textContent = title;

  const parts = [];
  if (state.frontmatter.type) parts.push(state.frontmatter.type);
  if (state.frontmatter.status) parts.push(state.frontmatter.status);
  if (state.frontmatter.privacy) parts.push(state.frontmatter.privacy);
  if (state.currentPath) parts.push(state.currentPath);
  metaEl.textContent = parts.join(" · ");
}

function parseTags(value) {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function setOptionalString(key, value) {
  const trimmed = value.trim();
  if (trimmed) {
    state.frontmatter[key] = trimmed;
  } else {
    delete state.frontmatter[key];
  }
}

function setOptionalArray(key, values) {
  if (values.length) {
    state.frontmatter[key] = values;
  } else {
    delete state.frontmatter[key];
  }
}

function setConfidence(value) {
  const trimmed = value.trim();
  if (!trimmed) {
    delete state.frontmatter.confidence;
    return;
  }
  const parsed = Number(trimmed);
  state.frontmatter.confidence = Number.isFinite(parsed) ? parsed : trimmed;
}

function handleEditorInput(target) {
  if (!state.currentPath) {
    return;
  }
  const { id, value } = target;
  switch (id) {
    case "fm-title":
      setOptionalString("title", value);
      break;
    case "fm-summary":
      setOptionalString("summary", value);
      break;
    case "fm-tags":
      setOptionalArray("tags", parseTags(value));
      break;
    case "fm-type":
      state.frontmatter.type = value;
      break;
    case "fm-status":
      state.frontmatter.status = value;
      break;
    case "fm-privacy":
      state.frontmatter.privacy = value;
      break;
    case "fm-confidence":
      setConfidence(value);
      break;
    case "item-body":
      state.body = value;
      break;
    default:
      return;
  }

  state.dirty = true;
  updateItemHeader();
  updateSaveState();
  updatePromoteState();
  scheduleValidation();
}

function buildUpdatePayload() {
  return {
    path: state.currentPath,
    frontmatter: state.frontmatter,
    body: state.body,
    validate_only: false,
  };
}

function buildValidatePayload() {
  return {
    frontmatter: state.frontmatter,
    body: state.body,
  };
}

function scheduleValidation() {
  if (state.validationTimer) {
    clearTimeout(state.validationTimer);
  }
  state.validationTimer = setTimeout(() => {
    validateCurrent().catch(() => {});
  }, 400);
}

function normalizeValidationResponse(payload) {
  if (!payload || typeof payload !== "object") {
    return { valid: false, errors: ["Validation failed."], warnings: [] };
  }
  let errors = [];
  let warnings = [];
  if (Array.isArray(payload.errors)) {
    errors = payload.errors;
  } else if (Array.isArray(payload.issues)) {
    errors = payload.issues;
  } else if (Array.isArray(payload.messages)) {
    errors = payload.messages;
  } else if (payload.error) {
    errors = [payload.error];
  }
  if (Array.isArray(payload.warnings)) {
    warnings = payload.warnings;
  } else if (payload.warning) {
    warnings = [payload.warning];
  }
  let valid;
  if (typeof payload.valid === "boolean") {
    valid = payload.valid;
  } else {
    valid = errors.length === 0;
  }
  if (errors.length) {
    valid = false;
  }
  return { valid, errors, warnings };
}

async function validateCurrent({ force = false } = {}) {
  if (!state.currentPath) {
    return false;
  }
  const payload = buildValidatePayload();
  const payloadKey = JSON.stringify(payload);
  if (!force && payloadKey === state.lastValidatedPayloadKey) {
    return state.validation.valid;
  }
  state.validation.status = "pending";
  state.validation.errors = [];
  state.validation.warnings = [];
  updateValidationUI();
  updateSaveState();

  const seq = (state.validationSeq += 1);
  try {
    const response = await validatePayload(payload);
    if (seq !== state.validationSeq) {
      return state.validation.valid;
    }
    const normalized = normalizeValidationResponse(response);
    state.validation = {
      status: "done",
      valid: normalized.valid,
      errors: normalized.errors,
      warnings: normalized.warnings,
    };
    state.lastValidatedPayloadKey = payloadKey;
  } catch (err) {
    if (seq !== state.validationSeq) {
      return state.validation.valid;
    }
    state.validation = {
      status: "done",
      valid: false,
      errors: [String(err)],
      warnings: [],
    };
  }
  updateValidationUI();
  updateSaveState();
  return state.validation.valid;
}

function updateValidationUI() {
  const block = document.getElementById("validation-block");
  const list = document.getElementById("validation-errors");
  if (!block || !list) {
    return;
  }
  if (!state.currentPath) {
    block.classList.add("hidden");
    return;
  }
  block.classList.remove("hidden");
  list.innerHTML = "";

  if (state.validation.status === "pending") {
    block.dataset.state = "pending";
    const li = document.createElement("li");
    li.textContent = "Validating...";
    list.appendChild(li);
    return;
  }

  if (state.validation.valid) {
    if (state.validation.warnings.length) {
      block.dataset.state = "warning";
      const li = document.createElement("li");
      li.textContent = "Valid with warnings:";
      list.appendChild(li);
      state.validation.warnings.forEach((warn) => {
        const warningItem = document.createElement("li");
        warningItem.textContent = `Warning: ${warn}`;
        list.appendChild(warningItem);
      });
    } else {
      block.dataset.state = "valid";
      const li = document.createElement("li");
      li.textContent = "All checks passed.";
      list.appendChild(li);
    }
    return;
  }

  block.dataset.state = "invalid";
  if (!state.validation.errors.length) {
    const li = document.createElement("li");
    li.textContent = "Validation failed.";
    list.appendChild(li);
    return;
  }

  state.validation.errors.forEach((err) => {
    const li = document.createElement("li");
    li.textContent = err;
    list.appendChild(li);
  });
  if (state.validation.warnings.length) {
    state.validation.warnings.forEach((warn) => {
      const li = document.createElement("li");
      li.textContent = `Warning: ${warn}`;
      list.appendChild(li);
    });
  }
}

function updateSaveState() {
  const saveBtn = document.getElementById("save-btn");
  const hint = document.getElementById("save-hint");
  if (!saveBtn || !hint) {
    return;
  }
  let message = "No changes";
  let disabled = true;

  if (!state.currentPath) {
    message = "No item loaded";
  } else if (state.saving) {
    message = "Saving...";
  } else if (state.validation.status === "pending") {
    message = "Validating...";
  } else if (!state.dirty) {
    message = "No changes";
  } else if (!state.validation.valid) {
    message = "Fix validation errors";
  } else {
    message = state.validation.warnings.length ? "Ready to save (warnings)" : "Ready to save";
    disabled = false;
  }

  saveBtn.disabled = disabled;
  hint.textContent = message;
}

function updatePromoteState() {
  const button = document.getElementById("promote-btn");
  const input = document.getElementById("promote-confirm");
  const hint = document.getElementById("promote-hint");
  if (!button || !input || !hint) {
    return;
  }
  const confirm = input.value.trim() === "PROMOTE";
  const isInbox = state.frontmatter.status === "inbox";

  if (!state.currentPath) {
    button.disabled = true;
    hint.textContent = "Load an inbox item to promote.";
    return;
  }
  if (!isInbox) {
    button.disabled = true;
    hint.textContent = "Only inbox items can be promoted.";
    return;
  }
  if (!confirm) {
    button.disabled = true;
    hint.textContent = "Type PROMOTE to enable.";
    return;
  }
  button.disabled = false;
  hint.textContent = "Ready to promote.";
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
  state.item = payload;
  state.frontmatter = { ...(payload.frontmatter || {}) };
  state.body = payload.body || "";
  state.dirty = false;
  state.saving = false;
  state.validation = { status: "idle", valid: true, errors: [], warnings: [] };
  state.lastValidatedPayloadKey = null;

  applyItemToForm(payload);
  updateItemHeader();

  const promoteInput = document.getElementById("promote-confirm");
  if (promoteInput) {
    promoteInput.value = "";
  }

  updateValidationUI();
  updateSaveState();
  updatePromoteState();
  scheduleValidation();
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
    clearError();
    const payload = await fetchItem(path);
    renderItem(payload);
  } catch (err) {
    showError(String(err));
    clearEditor("Failed to load");
  }
}

async function refreshInbox({ selectPath = null, preserveSelection = false } = {}) {
  const payload = await fetchInbox();
  renderInbox(payload);
  if (!payload.items.length) {
    clearEditor("Inbox is empty");
    return;
  }

  if (selectPath) {
    await loadItem(selectPath);
    return;
  }

  if (preserveSelection && state.currentPath) {
    const match = payload.items.find((item) => item.path === state.currentPath);
    if (match) {
      await loadItem(match.path);
      return;
    }
    if (preserveSelection) {
      return;
    }
  }

  await loadItem(payload.items[0].path);
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
      clearError();
      const payload = await fetchSearch(query);
      renderSearch(payload);
    } catch (err) {
      showError(String(err));
      clearEditor("Search failed");
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
      clearError();
      const payload = await captureNote(title, body);
      titleInput.value = "";
      bodyInput.value = "";
      await refreshInbox({ preserveSelection: true });
      await loadItem(payload.path);
    } catch (err) {
      showError(String(err));
      clearEditor("Capture failed");
    }
  });
}

function wireFilters() {
  const status = document.getElementById("filter-status");
  const privacy = document.getElementById("filter-privacy");
  [status, privacy].forEach((select) => {
    select.addEventListener("change", () => {
      refreshInbox().catch((err) => showError(String(err)));
    });
  });
}

function wirePromote() {
  const button = document.getElementById("promote-btn");
  const input = document.getElementById("promote-confirm");
  if (input) {
    input.addEventListener("input", updatePromoteState);
  }
  button.addEventListener("click", async () => {
    if (!state.currentPath || button.disabled) {
      return;
    }
    try {
      clearError();
      const payload = await promoteNote(state.currentPath);
      await refreshInbox({ preserveSelection: true });
      const nextPath = payload.path || (payload.item && payload.item.path) || state.currentPath;
      if (nextPath) {
        await loadItem(nextPath);
      }
    } catch (err) {
      showError(String(err));
      clearEditor("Promote failed");
    }
  });
}

function wireEditor() {
  const form = document.getElementById("editor-form");
  if (!form) {
    return;
  }
  form.addEventListener("input", (event) => {
    const target = event.target;
    if (target && typeof target.id === "string") {
      handleEditorInput(target);
    }
  });
  form.addEventListener("change", (event) => {
    const target = event.target;
    if (target && typeof target.id === "string") {
      handleEditorInput(target);
    }
  });
}

function wireSave() {
  const button = document.getElementById("save-btn");
  button.addEventListener("click", async () => {
    if (!state.currentPath || button.disabled) {
      return;
    }
    const isValid = await validateCurrent({ force: true });
    if (!isValid) {
      return;
    }
    try {
      clearError();
      state.saving = true;
      updateSaveState();
      const payload = await updateItem(buildUpdatePayload());
      const nextPath = payload.path || (payload.item && payload.item.path) || state.currentPath;
      await refreshInbox({ preserveSelection: true });
      if (nextPath) {
        await loadItem(nextPath);
      }
    } catch (err) {
      showError(String(err));
    } finally {
      state.saving = false;
      updateSaveState();
    }
  });
}

function wireDaily() {
  const openBtn = document.getElementById("daily-open-btn");
  const appendBtn = document.getElementById("daily-append-btn");
  const appendInput = document.getElementById("daily-append-text");

  async function setBusy(isBusy) {
    state.dailyBusy = isBusy;
    openBtn.disabled = isBusy;
    appendBtn.disabled = isBusy;
  }

  openBtn.addEventListener("click", async () => {
    if (state.dailyBusy) {
      return;
    }
    try {
      clearError();
      await setBusy(true);
      const payload = await openDaily();
      const targetPath = payload.path || (payload.item && payload.item.path);
      if (targetPath) {
        await loadItem(targetPath);
      }
    } catch (err) {
      showError(String(err));
    } finally {
      await setBusy(false);
    }
  });

  appendBtn.addEventListener("click", async () => {
    const text = appendInput.value.trim();
    if (!text || state.dailyBusy) {
      return;
    }
    try {
      clearError();
      await setBusy(true);
      const payload = await appendDaily(text);
      appendInput.value = "";
      const targetPath = payload.path || (payload.item && payload.item.path);
      if (targetPath) {
        await loadItem(targetPath);
      }
    } catch (err) {
      showError(String(err));
    } finally {
      await setBusy(false);
    }
  });
}

async function init() {
  try {
    clearError();
    await refreshInbox();
    wireSearch();
    wireCapture();
    wireFilters();
    wirePromote();
    wireEditor();
    wireSave();
    wireDaily();
  } catch (err) {
    showError(String(err));
    clearEditor("Failed to load inbox");
  }
}

init();
