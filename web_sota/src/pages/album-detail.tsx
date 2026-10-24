import { API_BASE } from "@/lib/api";
import { ArrowLeft, Loader2, Pencil, Plus, Search, Trash2, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

interface AlbumAsset {
  id: string;
  type?: string;
}

interface AlbumDetail {
  id: string;
  album_name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  asset_count: number;
  shared: boolean;
  assets: AlbumAsset[];
}

interface SearchHit {
  id: string;
  original_filename?: string;
}

async function readError(res: Response, fallback: string): Promise<string> {
  const body = await res.json().catch(() => ({}));
  return (body as { detail?: string }).detail || res.statusText || fallback;
}

export function AlbumDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [album, setAlbum] = useState<AlbumDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [searching, setSearching] = useState(false);
  const [mutating, setMutating] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/albums/${id}`);
      if (!res.ok) throw new Error(await readError(res, "Failed to load album"));
      const data = (await res.json()) as AlbumDetail;
      setAlbum(data);
      setName(data.album_name);
      setDescription(data.description ?? "");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load album");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function save() {
    if (!id || !album) return;
    const title = name.trim();
    if (!title) return;
    const params = new URLSearchParams();
    params.set("name", title);
    params.set("description", description.trim());
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/albums/${id}?${params.toString()}`, {
        method: "PATCH",
      });
      if (!res.ok) throw new Error(await readError(res, "Failed to save album"));
      setEditing(false);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save album");
    } finally {
      setSaving(false);
    }
  }

  async function removeAlbum() {
    if (!id) return;
    setDeleting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/albums/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(await readError(res, "Failed to delete album"));
      navigate("/albums");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete album");
      setDeleting(false);
      setConfirmDelete(false);
    }
  }

  async function removePhoto(assetId: string) {
    if (!id) return;
    setMutating(assetId);
    try {
      const res = await fetch(`${API_BASE}/api/v1/albums/${id}/photos`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify([assetId]),
      });
      if (!res.ok) throw new Error(await readError(res, "Failed to remove photo"));
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to remove photo");
    } finally {
      setMutating(null);
    }
  }

  async function search(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setSearching(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/photos/search?query=${encodeURIComponent(q)}&search_type=smart&limit=25`,
      );
      if (!res.ok) throw new Error(await readError(res, "Search failed"));
      const data = await res.json();
      setHits(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function addPhoto(assetId: string) {
    if (!id) return;
    setMutating(assetId);
    try {
      const res = await fetch(`${API_BASE}/api/v1/albums/${id}/photos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify([assetId]),
      });
      if (!res.ok) throw new Error(await readError(res, "Failed to add photo"));
      setHits((prev) => prev.filter((h) => h.id !== assetId));
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add photo");
    } finally {
      setMutating(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="album-detail">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error && !album) {
    return (
      <div className="space-y-4" data-testid="album-detail">
        <button
          type="button"
          onClick={() => navigate("/albums")}
          className="flex items-center gap-1 text-sm text-slate-400 hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" /> Albums
        </button>
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300">
          {error}
        </div>
      </div>
    );
  }

  if (!album) return null;
  const inAlbum = new Set(album.assets.map((a) => a.id));

  return (
    <div className="space-y-6" data-testid="album-detail">
      <button
        type="button"
        onClick={() => navigate("/albums")}
        className="flex items-center gap-1 text-sm text-slate-400 hover:text-white"
      >
        <ArrowLeft className="h-4 w-4" /> Albums
      </button>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="bg-slate-950/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm">
        {editing ? (
          <div className="space-y-3 max-w-lg">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Album name"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description (optional)"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => void save()}
                disabled={saving || !name.trim()}
                className="rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setEditing(false);
                  setName(album.album_name);
                  setDescription(album.description ?? "");
                }}
                className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:text-white"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">{album.album_name}</h1>
              {album.description && (
                <p className="mt-1 text-sm text-slate-400">{album.description}</p>
              )}
              <p className="mt-2 text-xs text-slate-500">
                {album.asset_count} items
                {album.shared ? " · shared" : ""}
                {album.updated_at ? ` · updated ${album.updated_at.slice(0, 10)}` : ""}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setEditing(true)}
                className="flex items-center gap-1 rounded-xl border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:text-white"
              >
                <Pencil className="h-4 w-4" /> Rename
              </button>
              {confirmDelete ? (
                <button
                  type="button"
                  onClick={() => void removeAlbum()}
                  disabled={deleting}
                  className="rounded-xl bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50"
                >
                  {deleting ? "Deleting..." : "Confirm delete (keeps photos)"}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setConfirmDelete(true)}
                  className="flex items-center gap-1 rounded-xl border border-slate-700 px-3 py-2 text-sm text-red-300 hover:text-red-200"
                >
                  <Trash2 className="h-4 w-4" /> Delete
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="bg-slate-950/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm">
        <h2 className="text-lg font-semibold text-white mb-4">Photos ({album.assets.length})</h2>
        {album.assets.length === 0 ? (
          <p className="text-sm text-slate-500">
            No photos yet — search below and add some, or drop this album if it was a mistake.
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {album.assets.map((a) => (
              <div
                key={a.id}
                className="group relative aspect-square overflow-hidden rounded-lg border border-slate-700/50 bg-slate-900"
              >
                <img
                  src={`${API_BASE}/api/v1/photos/${a.id}/thumbnail`}
                  alt=""
                  loading="lazy"
                  className="h-full w-full object-cover"
                />
                <button
                  type="button"
                  title="Remove from album"
                  onClick={() => void removePhoto(a.id)}
                  disabled={mutating === a.id}
                  className="absolute right-1 top-1 hidden rounded-md bg-black/70 p-1 text-slate-300 hover:text-red-300 group-hover:block disabled:opacity-50"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-slate-950/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm">
        <h2 className="text-lg font-semibold text-white mb-4">Add photos</h2>
        <form onSubmit={search} className="flex gap-2 max-w-lg">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search library..."
              className="w-full rounded-lg border border-slate-700 bg-slate-900 py-2 pl-9 pr-3 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <button
            type="submit"
            disabled={searching || !query.trim()}
            className="rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
          >
            {searching ? "..." : "Search"}
          </button>
        </form>
        {hits.length > 0 && (
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {hits.map((h) => (
              <div
                key={h.id}
                className="group relative aspect-square overflow-hidden rounded-lg border border-slate-700/50 bg-slate-900"
              >
                <img
                  src={`${API_BASE}/api/v1/photos/${h.id}/thumbnail`}
                  alt={h.original_filename ?? ""}
                  title={h.original_filename ?? h.id}
                  loading="lazy"
                  className="h-full w-full object-cover"
                />
                {inAlbum.has(h.id) ? (
                  <span className="absolute bottom-1 left-1 rounded bg-black/70 px-2 py-0.5 text-[11px] text-emerald-300">
                    In album
                  </span>
                ) : (
                  <button
                    type="button"
                    title="Add to album"
                    onClick={() => void addPhoto(h.id)}
                    disabled={mutating === h.id}
                    className="absolute bottom-1 right-1 hidden items-center gap-1 rounded-md bg-primary px-2 py-1 text-[11px] font-medium text-white group-hover:flex disabled:opacity-50"
                  >
                    <Plus className="h-3 w-3" /> Add
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
