export async function invoke(command, payload = {}) {
  if (window.__TAURI__ && window.__TAURI__.core && window.__TAURI__.core.invoke) {
    return window.__TAURI__.core.invoke(command, payload);
  }
  return mockInvoke(command, payload);
}

async function mockInvoke(command, payload) {
  switch (command) {
    case "inbox_view": {
      const params = new URLSearchParams();
      params.set("limit", String(payload.limit ?? 20));
      params.set("offset", String(payload.offset ?? 0));
      params.set("sort", payload.sort ?? "updated_desc");
      if (payload.status) params.set("status", payload.status);
      if (payload.privacy) params.set("privacy", payload.privacy);
      return fetchJson(`/api/inbox?${params.toString()}`);
    }
    case "item_view": {
      return fetchJson(`/api/item?path=${encodeURIComponent(payload.path)}`);
    }
    case "search": {
      const params = new URLSearchParams();
      params.set("q", payload.query ?? "");
      params.set("limit", String(payload.limit ?? 20));
      params.set("offset", String(payload.offset ?? 0));
      if (payload.status) params.set("status", payload.status);
      if (payload.privacy) params.set("privacy", payload.privacy);
      return fetchJson(`/api/search?${params.toString()}`);
    }
    case "capture": {
      return fetchJson("/api/capture", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }
    case "promote": {
      return fetchJson("/api/promote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }
    case "validate": {
      return fetchJson("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }
    case "item_update": {
      return fetchJson("/api/item/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }
    case "daily_open": {
      const params = new URLSearchParams();
      if (payload && payload.date) {
        params.set("date", payload.date);
      }
      const suffix = params.toString();
      const url = suffix ? `/api/daily/open?${suffix}` : "/api/daily/open";
      return fetchJson(url);
    }
    case "daily_append": {
      return fetchJson("/api/daily/append", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }
    default:
      throw new Error(`Unknown command: ${command}`);
  }
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message = payload.error || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return response.json();
}
