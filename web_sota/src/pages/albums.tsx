import { Library, Loader2, Plus, X } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAlbums } from "./useAlbums";

export interface AlbumResult {
  id: string;
  album_name: string;
  asset_count: number;
  created_at: string;
}

export function Albums() {
  const navigate = useNavigate();
  const { albums, loading, error, reload } = useAlbums();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function createAlbum(e: React.FormEvent) {
    e.preventDefault();
    const title = name.trim();
    if (!title) {
      setFormError("Name is required.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const res = await fetch("/api/v1/albums", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: title, description: description.trim() || null }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(
          (body as { detail?: string }).detail || res.statusText || "Failed to create album",
        );
      }
      const created = (await res.json()) as { id?: string };
      setCreating(false);
      setName("");
      setDescription("");
      if (created?.id) {
        navigate(`/albums/${created.id}`);
      } else {
        await reload();
      }
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create album");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6" data-testid="albums-page">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Albums</h1>
          <p className="text-slate-400">View and manage your photo albums.</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setCreating(true);
            setFormError(null);
          }}
          className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" /> New album
        </button>
      </div>

      {creating && (
        <form
          onSubmit={createAlbum}
          className="rounded-xl border border-slate-700/50 bg-slate-900/80 p-4 space-y-3"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Create album</h2>
            <button
              type="button"
              onClick={() => setCreating(false)}
              className="text-slate-400 hover:text-white"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Album name (required)"
            className="w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
            className="w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-primary"
          />
          {formError && <p className="text-sm text-red-300">{formError}</p>}
          <button
            type="submit"
            disabled={saving}
            className="rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
          >
            {saving ? "Creating..." : "Create album"}
          </button>
        </form>
      )}

      <div className="bg-slate-950/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm min-h-[400px]">
        {loading && (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 mb-6 space-y-1">
            <p className="font-medium">No connection to Immich</p>
            <p className="text-sm">{error}</p>
            <p className="text-xs text-slate-400">
              Check .env (IMMICH_SERVER_URL, IMMICH_API_KEY) and restart the backend.
            </p>
          </div>
        )}

        {!loading && albums.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 py-12">
            <Library className="h-12 w-12 mb-4 opacity-50" />
            <p>No albums found.</p>
          </div>
        )}

        {albums.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {albums.map((album) => (
              <button
                key={album.id}
                type="button"
                onClick={() => navigate(`/albums/${album.id}`)}
                className="group relative p-4 bg-slate-900/80 hover:bg-slate-800 rounded-xl border border-slate-700/50 transition-all cursor-pointer text-left"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                    <Library className="h-5 w-5" />
                  </div>
                  <div className="overflow-hidden">
                    <h3
                      className="text-sm font-semibold text-white truncate"
                      title={album.album_name}
                    >
                      {album.album_name}
                    </h3>
                    <p className="text-xs text-slate-400">{album.asset_count} items</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
