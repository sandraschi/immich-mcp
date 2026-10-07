// Same-origin relative by default (works on localhost, LAN names, Tailscale
// MagicDNS). Absolute backend URL only inside the Tauri WebView, where
// same-origin does not exist. Without this gate every absolute call from a
// non-localhost tab dies on CORS while curl "proves" the backend is healthy.
function isTauriWebView(): boolean {
  return (
    typeof window !== "undefined" && ("__TAURI__" in window || "__TAURI_INTERNALS__" in window)
  );
}

export const API_BASE = isTauriWebView() ? "http://127.0.0.1:10839" : "";

export interface HealthInfo {
  status: "ok" | "degraded" | "offline";
  server?: string;
  version?: string;
  tool_count?: number;
  uptime_seconds?: number;
  error?: string;
}

export async function checkBackendHealth(): Promise<HealthInfo> {
  try {
    const r = await fetch(`${API_BASE}/api/v1/health`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) {
      return { status: "offline", error: `HTTP ${r.status}` };
    }
    const data = (await r.json()) as Record<string, unknown>;
    return {
      status: "ok",
      server: (data.server as string) || "immich-mcp",
      version: (data.version as string) || undefined,
      tool_count: (data.tool_count as number) || undefined,
      uptime_seconds: (data.uptime_seconds as number) || undefined,
    };
  } catch (e) {
    return { status: "offline", error: e instanceof Error ? e.message : "Network error" };
  }
}

export async function fetchCapabilities(): Promise<Record<string, unknown>> {
  try {
    const r = await fetch(`${API_BASE}/api/v1/capabilities`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) return {};
    return (await r.json()) as Record<string, unknown>;
  } catch {
    return {};
  }
}
