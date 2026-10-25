import { API_BASE } from "@/lib/api";
import {
  AlertTriangle,
  ArrowUpDown,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Search,
  Sparkles,
  Square,
  Trash2,
  User,
  Users,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

interface Person {
  id: string;
  name: string;
  birthDate?: string | null;
  isHidden?: boolean;
  thumbnailPath?: string | null;
  updatedAt?: string;
  asset_count?: number;
  has_more_photos?: boolean;
}

type FilterKind = "all" | "named" | "unnamed" | "single" | "hidden";
type SortKind =
  | "photos-desc"
  | "photos-asc"
  | "name-asc"
  | "name-desc"
  | "updated-desc"
  | "updated-asc";

const PAGE_SIZE = 20;

const FILTERS: { id: FilterKind; label: string }[] = [
  { id: "all", label: "All" },
  { id: "named", label: "Named" },
  { id: "unnamed", label: "Unnamed" },
  { id: "single", label: "≤1 photo" },
  { id: "hidden", label: "Hidden" },
];

const SORTS: { id: SortKind; label: string }[] = [
  { id: "photos-desc", label: "Most photos" },
  { id: "photos-asc", label: "Fewest photos" },
  { id: "name-asc", label: "Name A–Z" },
  { id: "name-desc", label: "Name Z–A" },
  { id: "updated-desc", label: "Recently updated" },
  { id: "updated-asc", label: "Oldest updated" },
];

function photoCount(p: Person): number {
  return p.asset_count ?? 0;
}

function countLabel(p: Person): string {
  const n = photoCount(p);
  if (p.has_more_photos) return `${n}+ photos`;
  return `${n} photo${n === 1 ? "" : "s"}`;
}

export function People() {
  const navigate = useNavigate();
  const [people, setPeople] = useState<Person[]>([]);
  const [loading, setLoading] = useState(true);
  const [countsLoading, setCountsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState<FilterKind>("all");
  const [sort, setSort] = useState<SortKind>(() => {
    try {
      return (localStorage.getItem("people-sort") as SortKind) || "photos-desc";
    } catch {
      return "photos-desc";
    }
  });
  const [viewMode, setViewMode] = useState<"grid" | "list">(() => {
    try {
      return (localStorage.getItem("people-view") as "grid" | "list") || "grid";
    } catch {
      return "grid";
    }
  });
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [confirmBulk, setConfirmBulk] = useState(false);
  // Single-photo cleanup assist
  const [cleanupPreview, setCleanupPreview] = useState<number | null>(null);
  const [cleanupBusy, setCleanupBusy] = useState(false);
  const [cleanupError, setCleanupError] = useState<string | null>(null);
  const [cleanupDone, setCleanupDone] = useState<string | null>(null);

  const fetchPeople = async (withCounts: boolean) => {
    const params = new URLSearchParams();
    if (withCounts) {
      params.set("with_counts", "true");
      params.set("include_hidden", "true");
    }
    const qs = params.toString();
    const res = await fetch(`${API_BASE}/api/v1/people${qs ? `?${qs}` : ""}`);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(
        (body as { detail?: string }).detail || res.statusText || "Failed to fetch people",
      );
    }
    const data = await res.json();
    return Array.isArray(data) ? (data as Person[]) : [];
  };

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        // Fast first paint: raw list, then enrich with counts.
        const raw = await fetchPeople(false);
        if (cancelled) return;
        setPeople(raw);
        setLoading(false);
        setCountsLoading(true);
        const enriched = await fetchPeople(true);
        if (cancelled) return;
        setPeople(enriched);
      } catch (err: unknown) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to fetch people");
        setLoading(false);
      } finally {
        if (!cancelled) setCountsLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem("people-sort", sort);
    } catch {
      /* ignore */
    }
  }, [sort]);

  // Reset pagination + selection scope whenever the result set definition changes.
  useEffect(() => {
    setPage(1);
  }, [searchQuery, filter, sort]);

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    let rows = people.filter((p) => {
      if (filter === "hidden" && !p.isHidden) return false;
      if (filter !== "hidden" && filter !== "all") {
        if (p.isHidden) return false;
        if (filter === "named" && !p.name) return false;
        if (filter === "unnamed" && p.name) return false;
        if (filter === "single" && photoCount(p) > 1) return false;
      } else if (filter === "all" && q === "") {
        // "all" shows everything except hidden unless searching
        if (p.isHidden) return false;
      }
      if (q && !(p.name || "Unnamed").toLowerCase().includes(q)) return false;
      return true;
    });
    const byName = (a: Person, b: Person) =>
      (a.name || "zzz").toLowerCase().localeCompare((b.name || "zzz").toLowerCase());
    switch (sort) {
      case "photos-desc":
        rows = [...rows].sort((a, b) => photoCount(b) - photoCount(a) || byName(a, b));
        break;
      case "photos-asc":
        rows = [...rows].sort((a, b) => photoCount(a) - photoCount(b) || byName(a, b));
        break;
      case "name-asc":
        rows = [...rows].sort(byName);
        break;
      case "name-desc":
        rows = [...rows].sort((a, b) => byName(b, a));
        break;
      case "updated-desc":
        rows = [...rows].sort((a, b) => (b.updatedAt || "").localeCompare(a.updatedAt || ""));
        break;
      case "updated-asc":
        rows = [...rows].sort((a, b) => (a.updatedAt || "").localeCompare(b.updatedAt || ""));
        break;
    }
    return rows;
  }, [people, searchQuery, filter, sort]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageRows = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  const namedCount = people.filter((p) => !p.isHidden && p.name).length;
  const singleCount = people.filter((p) => !p.isHidden && photoCount(p) <= 1).length;
  const visibleCount = people.filter((p) => !p.isHidden).length;

  const pageIds = pageRows.map((p) => p.id);
  const allPageSelected = pageIds.length > 0 && pageIds.every((id) => selected.has(id));

  const toggleOne = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const togglePage = () => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (allPageSelected) pageIds.forEach((id) => next.delete(id));
      else pageIds.forEach((id) => next.add(id));
      return next;
    });
  };

  const selectFiltered = () => setSelected(new Set(filtered.map((p) => p.id)));
  const selectSinglePhoto = () =>
    setSelected(new Set(people.filter((p) => !p.isHidden && photoCount(p) <= 1).map((p) => p.id)));
  const clearSelection = () => {
    setSelected(new Set());
    setConfirmBulk(false);
  };

  const refreshAfterMutation = async () => {
    try {
      setPeople(await fetchPeople(true));
    } catch {
      setPeople(await fetchPeople(false));
    }
  };

  const bulkDelete = async () => {
    if (selected.size === 0) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/people/bulk-delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: [...selected], confirm: true }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error((body as { detail?: string }).detail || "Bulk delete failed");
      clearSelection();
      setConfirmBulk(false);
      await refreshAfterMutation();
    } catch (err: unknown) {
      setDeleteError(err instanceof Error ? err.message : "Bulk delete failed");
    } finally {
      setDeleting(false);
    }
  };

  const previewCleanup = async () => {
    setCleanupBusy(true);
    setCleanupError(null);
    setCleanupDone(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/people/cleanup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ threshold: 1, dry_run: true, limit: 500 }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok)
        throw new Error((body as { detail?: string }).detail || "Cleanup preview failed");
      setCleanupPreview((body as { candidate_count?: number }).candidate_count ?? 0);
    } catch (err: unknown) {
      setCleanupError(err instanceof Error ? err.message : "Cleanup preview failed");
    } finally {
      setCleanupBusy(false);
    }
  };

  const runCleanup = async () => {
    setCleanupBusy(true);
    setCleanupError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/people/cleanup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ threshold: 1, dry_run: false, limit: 500 }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error((body as { detail?: string }).detail || "Cleanup failed");
      const n = (body as { deleted_count?: number }).deleted_count ?? 0;
      setCleanupDone(
        `Deleted ${n} single-photo face${n === 1 ? "" : "s"}. Photos stay in the library.`,
      );
      setCleanupPreview(null);
      clearSelection();
      await refreshAfterMutation();
    } catch (err: unknown) {
      setCleanupError(err instanceof Error ? err.message : "Cleanup failed");
    } finally {
      setCleanupBusy(false);
    }
  };

  const openPerson = (id: string) => navigate(`/people/${id}`);

  return (
    <div className="space-y-6 pb-24" data-testid="people-page">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="mb-2 text-3xl font-bold tracking-tight text-white">People</h1>
          <p className="text-slate-400">
            Manage face recognition clusters and identify family &amp; friends.
            {people.length > 0 && (
              <span className="ml-2 text-slate-500">
                {visibleCount} shown{countsLoading ? " · counting photos…" : ""}
                {namedCount > 0 ? ` · ${namedCount} named` : " · none named yet"}
                {singleCount > 0 ? ` · ${singleCount} with ≤1 photo` : ""}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 p-1">
          <button
            type="button"
            onClick={() => {
              setViewMode("grid");
              try {
                localStorage.setItem("people-view", "grid");
              } catch {
                /* ignore */
              }
            }}
            data-testid="people-view-grid"
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${viewMode === "grid" ? "bg-primary text-primary-foreground shadow-lg" : "text-slate-400 hover:text-white"}`}
          >
            Grid
          </button>
          <button
            type="button"
            onClick={() => {
              setViewMode("list");
              try {
                localStorage.setItem("people-view", "list");
              } catch {
                /* ignore */
              }
            }}
            data-testid="people-view-list"
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${viewMode === "list" ? "bg-primary text-primary-foreground shadow-lg" : "text-slate-400 hover:text-white"}`}
          >
            List
          </button>
        </div>
      </div>

      {/* List-page standard: search / filter / sort / count */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by name..."
            data-testid="people-search"
            className="w-full rounded-xl border border-slate-700/50 bg-slate-900/50 py-2 pl-10 pr-4 text-sm text-slate-200 placeholder:text-slate-500 transition-all focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div
            className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/50 p-1"
            data-testid="people-filter"
          >
            {FILTERS.map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => setFilter(f.id)}
                data-testid={`people-filter-${f.id}`}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${filter === f.id ? "bg-primary text-primary-foreground shadow-lg" : "text-slate-400 hover:text-white"}`}
              >
                {f.label}
              </button>
            ))}
          </div>
          <label className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-1.5 text-xs text-slate-400">
            <ArrowUpDown className="h-3 w-3" />
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortKind)}
              data-testid="people-sort"
              className="bg-transparent text-xs font-medium text-slate-200 focus:outline-none [&>option]:bg-slate-900"
            >
              {SORTS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
          <span className="text-xs text-slate-500" data-testid="people-count">
            {filtered.length} of {people.length}
          </span>
        </div>
      </div>

      {/* Crowd-photo cleanup assist */}
      <div className="flex flex-col gap-2 rounded-xl border border-slate-800/50 bg-slate-950/50 p-4 backdrop-blur-sm">
        <div className="flex flex-wrap items-center gap-2">
          <Sparkles className="h-4 w-4 text-amber-400" />
          <span className="text-sm font-medium text-slate-200">Crowd-photo cleanup</span>
          <span className="text-xs text-slate-500">
            Faces with ≤1 photo are almost never real people — preview, then delete them in one go.
            Photos stay in the library.
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => void previewCleanup()}
            disabled={cleanupBusy || countsLoading}
            data-testid="people-cleanup-preview"
            className="rounded-xl border border-slate-700 px-3 py-2 text-xs font-medium text-slate-300 hover:text-white disabled:opacity-50"
          >
            {cleanupBusy ? "Working…" : "Preview single-photo faces"}
          </button>
          {cleanupPreview !== null && (
            <span className="text-xs text-slate-300" data-testid="people-cleanup-preview-count">
              {cleanupPreview} candidate{cleanupPreview === 1 ? "" : "s"} found.{" "}
              <button
                type="button"
                onClick={() => void runCleanup()}
                disabled={cleanupBusy}
                data-testid="people-cleanup-confirm"
                className="ml-1 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-500 disabled:opacity-50"
              >
                {cleanupBusy ? "Deleting…" : `Delete ${cleanupPreview}`}
              </button>
            </span>
          )}
          {cleanupError && <span className="text-xs text-red-300">{cleanupError}</span>}
          {cleanupDone && <span className="text-xs text-emerald-300">{cleanupDone}</span>}
        </div>
      </div>

      {deleteError && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
          {deleteError}
        </div>
      )}

      <div className="rounded-2xl border border-slate-800/50 bg-slate-950/30 p-6 backdrop-blur-sm min-h-[500px]">
        {loading && (
          <div className="flex h-64 flex-col items-center justify-center text-slate-500">
            <Loader2 className="mb-4 h-10 w-10 animate-spin text-primary" />
            <p className="text-sm font-medium">Clustering faces...</p>
          </div>
        )}

        {error && (
          <div className="mb-6 space-y-1 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">
            <p className="font-medium">No connection to Immich</p>
            <p className="text-sm">{error}</p>
            <p className="text-xs text-slate-400">
              Check .env (IMMICH_SERVER_URL, IMMICH_API_KEY) and restart the backend.
            </p>
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="flex min-h-[400px] flex-col items-center justify-center py-12 text-slate-500">
            <Users className="mb-4 h-12 w-12 opacity-20" />
            <p className="text-lg font-medium">No people found.</p>
            <p className="mt-2 text-sm opacity-60">
              {searchQuery || filter !== "all"
                ? "No one matches — clear the search or filter."
                : people.length > 0
                  ? "Everyone here is hidden — unhide people in the Immich app."
                  : "No faces detected yet — run face detection in Immich first."}
            </p>
          </div>
        )}

        {!loading && filtered.length > 0 && (
          <>
            {/* Selection toolbar */}
            <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
              <button
                type="button"
                onClick={togglePage}
                data-testid="people-select-page"
                className="flex items-center gap-1 rounded-lg border border-slate-700 px-2.5 py-1.5 font-medium text-slate-300 hover:text-white"
              >
                {allPageSelected ? (
                  <CheckSquare className="h-3.5 w-3.5" />
                ) : (
                  <Square className="h-3.5 w-3.5" />
                )}
                {allPageSelected ? "Deselect page" : "Select page"}
              </button>
              <button
                type="button"
                onClick={selectFiltered}
                data-testid="people-select-filtered"
                className="rounded-lg border border-slate-700 px-2.5 py-1.5 font-medium text-slate-300 hover:text-white"
              >
                Select all {filtered.length}
              </button>
              <button
                type="button"
                onClick={selectSinglePhoto}
                disabled={countsLoading}
                data-testid="people-select-single-photo"
                className="rounded-lg border border-slate-700 px-2.5 py-1.5 font-medium text-slate-300 hover:text-white disabled:opacity-50"
              >
                Select ≤1-photo faces ({singleCount})
              </button>
              {selected.size > 0 && (
                <button
                  type="button"
                  onClick={clearSelection}
                  data-testid="people-select-clear"
                  className="flex items-center gap-1 rounded-lg border border-slate-700 px-2.5 py-1.5 font-medium text-slate-400 hover:text-white"
                >
                  <X className="h-3.5 w-3.5" /> Clear ({selected.size})
                </button>
              )}
            </div>

            <div
              className={
                viewMode === "grid"
                  ? "grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6"
                  : "space-y-2"
              }
            >
              {pageRows.map((person) =>
                viewMode === "grid" ? (
                  <button
                    key={person.id}
                    type="button"
                    onClick={() => openPerson(person.id)}
                    data-testid={`person-card-${person.id}`}
                    className={`group relative flex cursor-pointer flex-col items-center gap-3 rounded-2xl border border-b-2 border-slate-800/50 bg-slate-900/40 p-4 text-left shadow-lg transition-all duration-300 hover:-translate-y-1 hover:bg-slate-800/60 hover:border-b-primary/50 ${selected.has(person.id) ? "border-primary/60 ring-1 ring-primary/40" : ""}`}
                  >
                    {/* biome-ignore lint/a11y/useSemanticElements: nested <button> is invalid HTML — span+role is the correct pattern here */}
                    <span
                      role="checkbox"
                      aria-checked={selected.has(person.id)}
                      tabIndex={0}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleOne(person.id);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === " " || e.key === "Enter") {
                          e.preventDefault();
                          e.stopPropagation();
                          toggleOne(person.id);
                        }
                      }}
                      data-testid={`person-select-${person.id}`}
                      title={selected.has(person.id) ? "Deselect" : "Select"}
                      aria-label={
                        selected.has(person.id)
                          ? `Deselect ${person.name || "unnamed face"}`
                          : `Select ${person.name || "unnamed face"}`
                      }
                      className="absolute left-2 top-2 z-10 cursor-pointer rounded-md bg-slate-950/70 p-1 text-slate-300 hover:text-white"
                    >
                      {selected.has(person.id) ? (
                        <CheckSquare className="h-4 w-4 text-primary" />
                      ) : (
                        <Square className="h-4 w-4 opacity-60 group-hover:opacity-100" />
                      )}
                    </span>
                    <div className="relative h-24 w-24 overflow-hidden rounded-full border-2 border-slate-800 shadow-2xl transition-colors group-hover:border-primary/30">
                      {person.thumbnailPath ? (
                        <img
                          src={`${API_BASE}/api/v1/people/${person.id}/thumbnail`}
                          alt={person.name || "Unnamed face"}
                          loading="lazy"
                          className="h-full w-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = "none";
                          }}
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center bg-slate-800">
                          <User className="h-10 w-10 text-slate-600" />
                        </div>
                      )}
                    </div>
                    <div className="w-full overflow-hidden text-center">
                      <h3
                        className="truncate px-2 text-sm font-bold text-white"
                        title={person.name || "Unnamed"}
                      >
                        {person.name || "Unnamed"}
                      </h3>
                      <span className="text-[10px] font-medium uppercase tracking-widest text-slate-500">
                        {person.isHidden ? "Hidden" : person.name ? "Named" : "Unnamed face"} ·{" "}
                        {countLabel(person)}
                      </span>
                      {person.updatedAt && (
                        <div className="mt-0.5 text-[10px] text-slate-600">
                          updated {person.updatedAt.slice(0, 10)}
                        </div>
                      )}
                    </div>
                  </button>
                ) : (
                  <button
                    key={person.id}
                    type="button"
                    onClick={() => openPerson(person.id)}
                    data-testid={`person-row-${person.id}`}
                    className={`flex w-full cursor-pointer items-center justify-between rounded-xl border border-slate-800/50 bg-slate-900/30 p-3 text-left transition-colors hover:bg-slate-800/50 ${selected.has(person.id) ? "border-primary/60 ring-1 ring-primary/40" : ""}`}
                  >
                    <div className="flex min-w-0 items-center gap-4">
                      {/* biome-ignore lint/a11y/useSemanticElements: nested <button> is invalid HTML — span+role is the correct pattern here */}
                      <span
                        role="checkbox"
                        aria-checked={selected.has(person.id)}
                        tabIndex={0}
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleOne(person.id);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === " " || e.key === "Enter") {
                            e.preventDefault();
                            e.stopPropagation();
                            toggleOne(person.id);
                          }
                        }}
                        data-testid={`person-select-${person.id}`}
                        aria-label={
                          selected.has(person.id)
                            ? `Deselect ${person.name || "unnamed face"}`
                            : `Select ${person.name || "unnamed face"}`
                        }
                        className="shrink-0 cursor-pointer rounded p-0.5 text-slate-300 hover:text-white"
                      >
                        {selected.has(person.id) ? (
                          <CheckSquare className="h-4 w-4 text-primary" />
                        ) : (
                          <Square className="h-4 w-4 opacity-60" />
                        )}
                      </span>
                      <div className="h-10 w-10 shrink-0 overflow-hidden rounded-full border border-slate-700 bg-slate-800">
                        {person.thumbnailPath ? (
                          <img
                            src={`${API_BASE}/api/v1/people/${person.id}/thumbnail`}
                            alt=""
                            loading="lazy"
                            className="h-full w-full object-cover"
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = "none";
                            }}
                          />
                        ) : (
                          <div className="flex h-full w-full items-center justify-center">
                            <User className="h-5 w-5 text-slate-600" />
                          </div>
                        )}
                      </div>
                      <div className="min-w-0">
                        <h3 className="truncate text-sm font-semibold text-slate-200">
                          {person.name || "Unnamed"}
                        </h3>
                        <p className="truncate font-mono text-xs text-slate-500">{person.id}</p>
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <span className="rounded-md border border-slate-700/50 bg-slate-800/50 px-2 py-1 text-xs font-medium text-slate-400">
                        {countLabel(person)}
                      </span>
                      <span className="rounded-md border border-slate-700/50 bg-slate-800/50 px-2 py-1 text-xs font-medium text-slate-400">
                        {person.isHidden ? "Hidden" : person.name ? "Named" : "Unnamed"}
                      </span>
                      {person.updatedAt && (
                        <span className="hidden text-xs text-slate-600 md:inline">
                          {person.updatedAt.slice(0, 10)}
                        </span>
                      )}
                    </div>
                  </button>
                ),
              )}
            </div>

            {/* Pagination (list-page standard: 20/page, reset on filter change) */}
            {totalPages > 1 && (
              <div
                className="mt-6 flex items-center justify-center gap-1"
                data-testid="people-pagination"
              >
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={safePage <= 1}
                  data-testid="people-page-prev"
                  className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-800 text-slate-400 hover:text-white disabled:opacity-40"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((n) => n === 1 || n === totalPages || Math.abs(n - safePage) <= 2)
                  .map((n, idx, arr) => (
                    <span key={n} className="flex items-center gap-1">
                      {idx > 0 && arr[idx - 1] !== n - 1 && (
                        <span className="text-slate-600">…</span>
                      )}
                      <button
                        type="button"
                        onClick={() => setPage(n)}
                        data-testid={`people-page-${n}`}
                        className={`h-8 min-w-8 rounded-md border px-2 text-xs font-medium ${n === safePage ? "border-primary bg-primary text-primary-foreground" : "border-slate-800 text-slate-400 hover:text-white"}`}
                      >
                        {n}
                      </button>
                    </span>
                  ))}
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={safePage >= totalPages}
                  data-testid="people-page-next"
                  className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-800 text-slate-400 hover:text-white disabled:opacity-40"
                  aria-label="Next page"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
                <span className="ml-2 text-xs text-slate-500">
                  Page {safePage} of {totalPages}
                </span>
              </div>
            )}
          </>
        )}
      </div>

      {/* Sticky bulk-action bar */}
      {selected.size > 0 && (
        <div
          className="fixed bottom-4 left-1/2 z-40 flex -translate-x-1/2 flex-wrap items-center gap-2 rounded-2xl border border-slate-700 bg-slate-900/95 px-4 py-3 shadow-2xl backdrop-blur-xl"
          data-testid="people-bulk-bar"
        >
          <span className="text-sm font-medium text-slate-200">{selected.size} selected</span>
          {confirmBulk ? (
            <>
              <span className="flex items-center gap-1 text-xs text-amber-300">
                <AlertTriangle className="h-3.5 w-3.5" /> Photos stay — faces unassigned. Undo is
                impossible.
              </span>
              <button
                type="button"
                onClick={() => void bulkDelete()}
                disabled={deleting}
                data-testid="people-bulk-delete-confirm"
                className="flex items-center gap-1 rounded-xl bg-red-600 px-3 py-2 text-xs font-medium text-white hover:bg-red-500 disabled:opacity-50"
              >
                {deleting ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Trash2 className="h-3.5 w-3.5" />
                )}
                {deleting ? "Deleting…" : `Delete ${selected.size}`}
              </button>
              <button
                type="button"
                onClick={() => setConfirmBulk(false)}
                data-testid="people-bulk-delete-cancel"
                className="rounded-xl border border-slate-700 px-3 py-2 text-xs text-slate-300 hover:text-white"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setConfirmBulk(true)}
              data-testid="people-bulk-delete"
              className="flex items-center gap-1 rounded-xl border border-red-500/50 px-3 py-2 text-xs font-medium text-red-300 hover:bg-red-500/10"
            >
              <Trash2 className="h-3.5 w-3.5" /> Delete selected
            </button>
          )}
        </div>
      )}
    </div>
  );
}
