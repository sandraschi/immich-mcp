import { type HealthInfo, checkBackendHealth } from "@/lib/api";
import { useCallback, useEffect, useRef, useState } from "react";

export type BackendState = "connecting" | "online" | "offline";

export function useBackendStatus() {
  const [state, setState] = useState<BackendState>("connecting");
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [restarting, setRestarting] = useState(false);
  const timerRef = useRef<number | null>(null);
  const attemptsRef = useRef(0);

  const poll = useCallback(async () => {
    const h = await checkBackendHealth();
    setHealth(h);
    setState(h.status === "ok" ? "online" : "offline");
    if (h.status === "ok") {
      attemptsRef.current = 0;
    }
  }, []);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    let cancelled = false;

    const schedule = (delayMs: number) => {
      if (cancelled) return;
      timerRef.current = window.setTimeout(async () => {
        await poll();
        const backoff = [1000, 2000, 4000, 8000, 16000];
        const idx = Math.min(attemptsRef.current, backoff.length - 1);
        attemptsRef.current += 1;
        schedule(backoff[idx]);
      }, delayMs);
    };

    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          if (event.payload === "ready") {
            void poll();
          } else if (typeof event.payload === "string" && event.payload.startsWith("error:")) {
            setState("offline");
          }
        });
      } catch {
        // Not inside Tauri - HTTP polling handles it
      }
    })();

    schedule(1000);
    return () => {
      cancelled = true;
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
      if (unlisten) unlisten();
    };
  }, [poll]);

  const restartBackend = useCallback(async () => {
    setRestarting(true);
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("start_backend");
    } catch {
      setRestarting(false);
    }
  }, []);

  return { state, health, restarting, restartBackend };
}
