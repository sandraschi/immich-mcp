import { API_BASE } from "@/lib/api";
import { Calendar, Image as ImageIcon, Loader2, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

interface PhotoResult {
  id: string;
  original_filename: string;
  created_at: string;
  smart_search_score?: number;
}

export function Photos() {
  const [query, setQuery] = useState("");
  const [photos, setPhotos] = useState<PhotoResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"timeline" | "search">("timeline");

  const loadTimeline = async () => {
    setLoading(true);
    setError(null);
    setMode("timeline");
    try {
      const res = await fetch(`${API_BASE}/api/v1/photos/timeline?page=1&limit=200`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const msg =
          (body as { detail?: string }).detail || res.statusText || "Failed to load timeline";
        throw new Error(msg);
      }
      const data = await res.json();
      setPhotos(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load photos");
      setPhotos([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline();
  }, []);

  const searchPhotos = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) {
      loadTimeline();
      return;
    }

    setLoading(true);
    setError(null);
    setMode("search");
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/photos/search?query=${encodeURIComponent(query)}&search_type=smart&limit=100`,
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const msg = (body as { detail?: string }).detail || res.statusText || "Search failed";
        throw new Error(msg);
      }
      const data = await res.json();
      setPhotos(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
      setPhotos([]);
    } finally {
      setLoading(false);
    }
  };

  const groupedPhotos = useMemo(() => {
    const groups: { [key: string]: PhotoResult[] } = {};

    // Sort photos by date descending
    const sorted = [...photos].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    sorted.forEach((photo) => {
      const date = new Date(photo.created_at);
      const key = date.toLocaleString("en-US", { month: "long", year: "numeric" });
      if (!groups[key]) groups[key] = [];
      groups[key].push(photo);
    });

    return Object.entries(groups);
  }, [photos]);

  return (
    <div className="space-y-6 pb-20">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Photos</h1>
          <p className="text-slate-400">Search and manage your Immich photo library.</p>
        </div>
      </div>

      <form onSubmit={searchPhotos} className="flex flex-wrap items-center gap-2 w-full max-w-3xl">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search or leave empty for timeline..."
            className="w-full bg-slate-900/50 border border-slate-700/50 rounded-lg pl-10 pr-4 py-3 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all shadow-lg backdrop-blur-md"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-3 rounded-lg text-sm font-medium transition-all disabled:opacity-50 shrink-0"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
        </button>
        {mode === "search" && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              loadTimeline();
            }}
            className="px-4 py-3 rounded-lg text-sm font-medium border border-slate-600 text-slate-300 hover:bg-slate-800 shrink-0"
          >
            Show all
          </button>
        )}
      </form>

      <div className="bg-slate-950/30 border border-slate-800/50 rounded-2xl p-6 backdrop-blur-sm min-h-[500px]">
        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 mb-6 space-y-1">
            <p className="font-medium">No connection to Immich</p>
            <p className="text-sm">{error}</p>
            <p className="text-xs text-slate-400">
              Check .env (IMMICH_SERVER_URL, IMMICH_API_KEY) and restart the backend.
            </p>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center h-64 text-slate-500 animate-in fade-in duration-500">
            <Loader2 className="h-10 w-10 mb-4 animate-spin text-primary" />
            <p className="text-sm font-medium">Analyzing results...</p>
          </div>
        )}

        {!loading && photos.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-500 py-24 border-2 border-dashed border-slate-800/50 rounded-2xl bg-slate-900/10">
            <div className="bg-slate-900/50 p-6 rounded-full mb-4 ring-1 ring-slate-800 shadow-xl">
              <ImageIcon className="h-12 w-12 opacity-50" />
            </div>
            <p className="text-lg font-medium">
              {mode === "search" ? "No matching photos." : "No photos in library yet."}
            </p>
            <p className="text-sm opacity-60 mt-2 text-center max-w-md">
              {mode === "search"
                ? "Try a different search or click Show all."
                : "Add photos via Immich or run a scan."}
            </p>
          </div>
        )}

        {!loading && photos.length > 0 && (
          <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {groupedPhotos.map(([month, monthPhotos]) => (
              <div key={month} className="space-y-4">
                <div className="flex items-center gap-3 sticky top-0 py-4 bg-slate-950/80 backdrop-blur-xl z-10 -mx-6 px-6">
                  <div className="p-1.5 bg-primary/10 rounded-lg">
                    <Calendar className="h-4 w-4 text-primary" />
                  </div>
                  <h2 className="text-lg font-bold text-white tracking-tight">{month}</h2>
                  <div className="h-px flex-1 bg-gradient-to-r from-slate-800/50 to-transparent" />
                  <span className="text-xs text-slate-500 font-medium bg-slate-900/50 px-2 py-1 rounded-full border border-slate-800">
                    {monthPhotos.length} photos
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                  {monthPhotos.map((photo) => (
                    <div
                      key={photo.id}
                      className="group relative aspect-square bg-slate-900 rounded-2xl overflow-hidden border border-slate-800/50 hover:border-primary/50 transition-all duration-500 hover:shadow-[0_20px_50px_rgba(0,0,0,0.5)] hover:shadow-primary/5 hover:-translate-y-2 cursor-pointer shadow-lg shadow-black/20"
                    >
                      <img
                        src={`${API_BASE}/api/v1/photos/${photo.id}/thumbnail`}
                        alt={photo.original_filename}
                        className="w-full h-full object-cover transition-all duration-700 group-hover:scale-110 filter brightness-90 group-hover:brightness-105"
                        loading="lazy"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.parentElement?.classList.add(
                            "flex",
                            "items-center",
                            "justify-center",
                          );
                          target.style.display = "none";
                          const icon = document.createElement("div");
                          icon.innerHTML =
                            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-8 w-8 text-slate-700 opacity-20"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>';
                          target.parentElement?.appendChild(icon.firstChild!);
                        }}
                      />
                      {/* Interaction Overlay */}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                      <div className="absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black/95 via-black/40 to-transparent translate-y-4 group-hover:translate-y-0 opacity-0 group-hover:opacity-100 transition-all duration-400 ease-out">
                        <p
                          className="text-[11px] text-white font-semibold truncate mb-1.5"
                          title={photo.original_filename}
                        >
                          {photo.original_filename}
                        </p>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] text-slate-400 font-medium">
                            {new Date(photo.created_at).toLocaleDateString(undefined, {
                              day: "numeric",
                              month: "short",
                            })}
                          </span>
                          {photo.smart_search_score && (
                            <div className="bg-primary/30 backdrop-blur-md px-1.5 py-0.5 rounded-md text-[9px] text-primary font-black tracking-wider border border-primary/20">
                              {Math.round(photo.smart_search_score * 100)}%
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
