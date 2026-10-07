import {
  CheckCircle2,
  CloudOff,
  Copy,
  GitCompareArrows,
  ImagePlus,
  Loader2,
  RefreshCw,
  Upload,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

interface ReconcileSummary {
  total: number;
  placeholders: number;
  live_pairs: number;
  in_library: number;
  new: number;
  duplicates: number;
  similar_groups: number;
  total_size_bytes: number;
}

interface ReconcileItem {
  path: string;
  name: string;
  ext: string;
  size_bytes: number;
  is_placeholder: boolean;
  is_heic: boolean;
  is_mov: boolean;
  live_pair: string | null;
  checksum: string | null;
  status: "placeholder" | "in_library" | "duplicate" | "new" | "scanned";
  asset_id: string;
  library_path: string;
}

interface ImportResult {
  success: boolean;
  targeted: number;
  imported: number;
  duplicates: number;
  errors: string[];
  album: string | null;
}

function formatBytes(bytes: number): string {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** i).toFixed(1)} ${units[i]}`;
}

const STATUS_META: Record<string, { label: string; cls: string }> = {
  new: { label: "New", cls: "bg-blue-500/15 text-blue-300 border-blue-700" },
  in_library: { label: "In Library", cls: "bg-emerald-500/15 text-emerald-300 border-emerald-700" },
  duplicate: { label: "Duplicate", cls: "bg-amber-500/15 text-amber-300 border-amber-700" },
  placeholder: { label: "Placeholder", cls: "bg-rose-500/15 text-rose-300 border-rose-700" },
  scanned: { label: "Scanned", cls: "bg-slate-500/15 text-slate-300 border-slate-700" },
};

export function Reconcile() {
  const [folder, setFolder] = useState(() => localStorage.getItem("immich-reconcile-folder") ?? "");
  const [album, setAlbum] = useState("");
  const [summary, setSummary] = useState<ReconcileSummary | null>(null);
  const [items, setItems] = useState<ReconcileItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("new");
  const [algorithm, setAlgorithm] = useState<string | null>(null);
  const [reportPath, setReportPath] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const persistFolder = (value: string) => {
    setFolder(value);
    localStorage.setItem("immich-reconcile-folder", value);
  };

  const runCompare = useCallback(async () => {
    if (!folder.trim()) {
      setError("Enter a folder path first, e.g. C:\\Users\\sandr\\iCloudPhotos\\Photos");
      return;
    }
    setLoading(true);
    setError(null);
    setImportResult(null);
    try {
      const res = await fetch("/api/v1/reconcile/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder: folder.trim() }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || "Compare failed");
      }
      const data = await res.json();
      setSummary(data.summary);
      setItems(Array.isArray(data.items) ? data.items : []);
      setAlgorithm(data.algorithm ?? null);
      setReportPath(data.report_path ?? null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Compare failed");
    } finally {
      setLoading(false);
    }
  }, [folder]);

  const runScan = useCallback(async () => {
    if (!folder.trim()) {
      setError("Enter a folder path first");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/reconcile/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder: folder.trim() }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || "Scan failed");
      }
      const data = await res.json();
      setSummary(data.summary);
      setItems(Array.isArray(data.items) ? data.items : []);
      setStatusFilter("all");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  }, [folder]);

  const runImport = useCallback(async () => {
    if (!summary) return;
    setImporting(true);
    setError(null);
    setImportResult(null);
    try {
      const res = await fetch("/api/v1/reconcile/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ album_name: album.trim() || null, statuses: ["new"] }),
      });
      const data = await res.json();
      if (!res.ok || data.success === false) {
        throw new Error(data.error || data.detail || "Import failed");
      }
      setImportResult(data);
      await runCompare();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setImporting(false);
    }
  }, [summary, album, runCompare]);

  useEffect(() => {
    if (!folder.trim()) return;
    fetch("/api/v1/reconcile/status")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.summary?.total) {
          setSummary(data.summary);
          setAlgorithm(data.checksum_algorithm ?? null);
          setReportPath(data.report_path ?? null);
        }
      })
      .catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = statusFilter === "all" ? items : items.filter((i) => i.status === statusFilter);

  const kpiCards = [
    { label: "Total files", value: summary?.total ?? 0, cls: "text-white", testid: "kpi-total" },
    { label: "New to library", value: summary?.new ?? 0, cls: "text-blue-400", testid: "kpi-new" },
    {
      label: "Already in library",
      value: summary?.in_library ?? 0,
      cls: "text-emerald-400",
      testid: "kpi-in-library",
    },
    {
      label: "Cloud placeholders",
      value: summary?.placeholders ?? 0,
      cls: "text-rose-400",
      testid: "kpi-placeholders",
    },
    {
      label: "Live Photo pairs",
      value: summary?.live_pairs ?? 0,
      cls: "text-violet-400",
      testid: "kpi-live-pairs",
    },
    {
      label: "Local duplicates",
      value: summary?.duplicates ?? 0,
      cls: "text-amber-400",
      testid: "kpi-duplicates",
    },
  ];

  return (
    <div data-testid="reconcile-page" className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Library Reconcile</h1>
        <p className="text-slate-400">
          Compare a local folder (iCloud Photos, old drives) against the Immich library.
          Placeholders are never touched; Live Photos (HEIC + MOV) are preserved as pairs; checksums
          decide what is actually new.
        </p>
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <input
            data-testid="reconcile-folder"
            type="text"
            value={folder}
            onChange={(e) => persistFolder(e.target.value)}
            placeholder="C:\Users\sandr\iCloudPhotos\Photos"
            className="flex-1 min-w-64 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
          />
          <button
            data-testid="reconcile-scan"
            type="button"
            onClick={runScan}
            disabled={loading}
            className="flex items-center gap-2 rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50"
          >
            <RefreshCw className="h-4 w-4" /> {loading ? "Scanning..." : "Scan only"}
          </button>
          <button
            data-testid="reconcile-compare"
            type="button"
            onClick={runCompare}
            disabled={loading}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
          >
            <GitCompareArrows className="h-4 w-4" /> {loading ? "Comparing..." : "Scan & Compare"}
          </button>
        </div>
        {algorithm && (
          <p className="text-xs text-slate-500">
            Checksum algorithm: {algorithm} (probed from live server){" "}
            {reportPath && `· report: ${reportPath}`}
          </p>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-rose-800 bg-rose-950/40 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      {summary && (
        <div
          data-testid="reconcile-summary"
          className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3"
        >
          {kpiCards.map((kpi) => (
            <div
              key={kpi.testid}
              data-testid={kpi.testid}
              className="rounded-lg border border-slate-800 bg-slate-900/40 p-4"
            >
              <div className={`text-2xl font-bold ${kpi.cls}`}>{kpi.value}</div>
              <div className="mt-1 text-xs text-slate-400">{kpi.label}</div>
            </div>
          ))}
        </div>
      )}

      {summary && (
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <span className="text-xs text-slate-400">Filter:</span>
          {["all", "new", "in_library", "duplicate", "placeholder"].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStatusFilter(s)}
              className={`rounded-md px-2.5 py-1 text-xs border ${
                statusFilter === s
                  ? "border-blue-600 bg-blue-600/20 text-blue-300"
                  : "border-slate-700 text-slate-400 hover:bg-slate-800"
              }`}
            >
              {STATUS_META[s]?.label ?? s}
            </button>
          ))}
          <span className="ml-auto text-xs text-slate-500">{filtered.length} shown</span>
        </div>
      )}

      {items.length > 0 && (
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 overflow-hidden">
          <table data-testid="reconcile-table" className="w-full text-sm">
            <thead className="border-b border-slate-800 bg-slate-950/60 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Size</th>
                <th className="px-4 py-2">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {filtered.slice(0, 200).map((item) => {
                const meta = STATUS_META[item.status] ?? STATUS_META.scanned;
                return (
                  <tr key={item.path} className="hover:bg-slate-800/30">
                    <td className="px-4 py-2 text-slate-200 font-mono text-xs">{item.name}</td>
                    <td className="px-4 py-2">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${meta.cls}`}
                      >
                        {item.status === "placeholder" ? (
                          <CloudOff className="h-3 w-3" />
                        ) : (
                          <CheckCircle2 className="h-3 w-3" />
                        )}
                        {meta.label}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-slate-400 text-xs">
                      {formatBytes(item.size_bytes)}
                    </td>
                    <td className="px-4 py-2 text-xs text-slate-500">
                      {item.is_heic && "HEIC "}
                      {item.is_mov && "MOV "}
                      {item.live_pair && <span className="text-violet-400">· Live Photo</span>}
                      {item.status === "in_library" && item.library_path && (
                        <span className="text-emerald-400">· {item.library_path}</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {summary && (
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-3">
          <div className="flex items-center gap-3">
            <ImagePlus className="h-5 w-5 text-blue-400" />
            <span className="text-sm font-medium text-slate-200">Import new files</span>
            <span className="text-xs text-slate-500">
              ({summary.new} new · Live Photos preserved · placeholders skipped)
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              data-testid="reconcile-album"
              type="text"
              value={album}
              onChange={(e) => setAlbum(e.target.value)}
              placeholder="Album name (optional)"
              className="flex-1 min-w-48 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
            <button
              data-testid="reconcile-import"
              type="button"
              onClick={runImport}
              disabled={importing || summary.new === 0}
              className="flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              {importing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Upload className="h-4 w-4" />
              )}
              {importing ? "Importing..." : `Import ${summary.new} new`}
            </button>
          </div>
          {importResult && (
            <div className="rounded-md border border-emerald-800 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-300">
              <span className="inline-flex items-center gap-1">
                <Copy className="h-3.5 w-3.5" /> Imported {importResult.imported} files
                {importResult.duplicates > 0 && ` (${importResult.duplicates} skipped by server)`}
              </span>
              {importResult.errors.length > 0 && (
                <div className="mt-1 text-rose-300 text-xs">
                  {importResult.errors.slice(0, 5).map((e) => (
                    <div key={e}>{e}</div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
