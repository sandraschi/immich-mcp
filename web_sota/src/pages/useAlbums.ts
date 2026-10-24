import { useCallback, useEffect, useState } from "react";
import type { AlbumResult } from "./albums";

export function useAlbums() {
  const [albums, setAlbums] = useState<AlbumResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/albums");
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const msg =
          (body as { detail?: string }).detail || res.statusText || "Failed to fetch albums";
        throw new Error(msg);
      }
      const data = await res.json();
      setAlbums(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to fetch albums");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { albums, loading, error, reload };
}
