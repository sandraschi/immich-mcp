import { FolderOpen, HardDrive, Loader2, RefreshCw, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

interface LibraryInfo {
  id: string;
  name: string;
  type: string;
  import_paths: string[];
  exclusion_patterns: string[];
  refreshed_at: string | null;
  created_at: string | null;
  asset_count: number;
  photo_count: number;
  video_count: number;
  size_bytes: number;
}

function formatBytes(bytes: number): string {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** i).toFixed(1)} ${units[i]}`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "never";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function Libraries() {
  const [libraries, setLibraries] = useState<LibraryInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scanningId, setScanningId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const fetchLibraries = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/libraries");
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const msg =
          (body as { detail?: string }).detail || res.statusText || "Failed to fetch libraries";
        throw new Error(msg);
      }
      const data = await res.json();
      setLibraries(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to fetch libraries");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLibraries();
  }, [fetchLibraries]);

  const scanLibrary = async (id: string) => {
    setScanningId(id);
    setNotice(null);
    try {
      const res = await fetch(`/api/v1/libraries/${id}/scan`, {
        method: "POST",
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || "Scan failed");
      }
      setNotice("Scan triggered - new files will appear as they are indexed.");
      setTimeout(() => fetchLibraries(), 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setScanningId(null);
    }
  };

  const deleteLibrary = async (lib: LibraryInfo) => {
    if (lib.import_paths.length > 0) {
      setError("Only libraries without import paths can be deleted.");
      return;
    }
    if (!window.confirm(`Delete library "${lib.name}"?`)) return;
    try {
      const res = await fetch(`/api/v1/libraries/${lib.id}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || "Delete failed");
      }
      setNotice("Library deleted.");
      fetchLibraries();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  return (
    <div data-testid="libraries-page" className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Libraries</h1>
          <p className="text-slate-400">
            External folders ingested by Immich, their scan status, and storage usage.
          </p>
        </div>
      </div>

      {notice && (
        <div className="rounded-lg border border-emerald-800 bg-emerald-950/40 px-4 py-3 text-sm text-emerald-300">
          {notice}
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="bg-slate-950/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm min-h-[300px]">
        {loading && (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {!loading && libraries.length === 0 && !error && (
          <div className="text-center py-16 text-slate-500">
            <FolderOpen className="h-10 w-10 mx-auto mb-3 opacity-40" />
            <p>No libraries configured.</p>
          </div>
        )}

        {!loading &&
          libraries.map((lib) => (
            <div
              key={lib.id}
              data-testid={`library-card-${lib.id}`}
              className="mb-4 rounded-xl border border-slate-800 bg-slate-900/40 p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <FolderOpen className="h-4 w-4 text-blue-500 shrink-0" />
                    <h3 className="font-semibold text-white truncate">{lib.name}</h3>
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-400">
                      {lib.type || "EXTERNAL"}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Last scan:{" "}
                    <span className="text-slate-300">{formatDate(lib.refreshed_at)}</span>
                    {lib.created_at ? ` - created ${formatDate(lib.created_at)}` : ""}
                  </p>
                </div>
                <div className="flex shrink-0 gap-2">
                  <button
                    type="button"
                    data-testid={`library-scan-${lib.id}`}
                    onClick={() => scanLibrary(lib.id)}
                    disabled={scanningId === lib.id}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
                    title="Scan for new or changed files"
                  >
                    {scanningId === lib.id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <RefreshCw className="h-3.5 w-3.5" />
                    )}
                    Scan
                  </button>
                  <button
                    type="button"
                    data-testid={`library-delete-${lib.id}`}
                    onClick={() => deleteLibrary(lib)}
                    disabled={lib.import_paths.length > 0}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-red-900 hover:text-red-200 disabled:opacity-40 disabled:hover:bg-slate-800 disabled:hover:text-slate-300"
                    title={
                      lib.import_paths.length > 0
                        ? "Only libraries without import paths can be deleted"
                        : "Delete this library"
                    }
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete
                  </button>
                </div>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-1.5">
                    Import paths (inside container)
                  </p>
                  {lib.import_paths.length === 0 ? (
                    <p className="text-sm text-slate-600 italic">No import paths set</p>
                  ) : (
                    <ul className="space-y-1">
                      {lib.import_paths.map((p) => (
                        <li
                          key={p}
                          className="rounded bg-slate-950/80 px-2.5 py-1.5 font-mono text-xs text-emerald-300"
                        >
                          {p}
                        </li>
                      ))}
                    </ul>
                  )}
                  <p className="mt-2 text-xs text-slate-600">
                    Host mapping example:{" "}
                    <span className="font-mono">/mnt/media/external_photos</span> ={" "}
                    <span className="font-mono">E:\Multimedia Files\Photos</span> (read-only volume
                    in docker-compose.yml)
                  </p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-1.5">
                    Contents
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="rounded-lg bg-slate-950/60 px-3 py-2">
                      <span className="block text-lg font-bold text-white">{lib.asset_count}</span>
                      <span className="text-xs text-slate-400">assets</span>
                    </div>
                    <div className="rounded-lg bg-slate-950/60 px-3 py-2">
                      <span className="block text-lg font-bold text-white">
                        {lib.photo_count} / {lib.video_count}
                      </span>
                      <span className="text-xs text-slate-400">photos / videos</span>
                    </div>
                    <div className="rounded-lg bg-slate-950/60 px-3 py-2 col-span-2 flex items-center gap-2">
                      <HardDrive className="h-4 w-4 text-blue-500" />
                      <span className="text-slate-300">{formatBytes(lib.size_bytes)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {lib.exclusion_patterns.length > 0 && (
                <p className="mt-3 text-xs text-slate-500">
                  Exclusions: {lib.exclusion_patterns.join(", ")}
                </p>
              )}
            </div>
          ))}
      </div>
    </div>
  );
}
