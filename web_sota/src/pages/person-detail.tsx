import { API_BASE } from "@/lib/api";
import { ArrowLeft, Loader2, Pencil, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

interface PersonAsset {
  id: string;
  type?: string;
}

interface PersonDetail {
  id: string;
  name: string;
  birthDate: string | null;
  isHidden: boolean;
  thumbnailPath?: string | null;
  updatedAt: string;
  assets: PersonAsset[];
  asset_count: number;
}

async function readError(res: Response, fallback: string): Promise<string> {
  const body = await res.json().catch(() => ({}));
  return (body as { detail?: string }).detail || res.statusText || fallback;
}

export function PersonDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [person, setPerson] = useState<PersonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/people/${id}`);
      if (!res.ok) throw new Error(await readError(res, "Failed to load person"));
      const data = (await res.json()) as PersonDetail;
      setPerson(data);
      setName(data.name ?? "");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load person");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function save() {
    if (!id) return;
    const params = new URLSearchParams();
    params.set("name", name.trim());
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/people/${id}?${params.toString()}`, {
        method: "PUT",
      });
      if (!res.ok) throw new Error(await readError(res, "Failed to rename"));
      setEditing(false);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to rename");
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!id) return;
    setDeleting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/people/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(await readError(res, "Failed to delete person"));
      navigate("/people");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete person");
      setDeleting(false);
      setConfirmDelete(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="person-detail">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error && !person) {
    return (
      <div className="space-y-4" data-testid="person-detail">
        <button
          type="button"
          onClick={() => navigate("/people")}
          className="flex items-center gap-1 text-sm text-slate-400 hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" /> People
        </button>
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300">
          {error}
        </div>
      </div>
    );
  }

  if (!person) return null;

  return (
    <div className="space-y-6" data-testid="person-detail">
      <button
        type="button"
        onClick={() => navigate("/people")}
        className="flex items-center gap-1 text-sm text-slate-400 hover:text-white"
      >
        <ArrowLeft className="h-4 w-4" /> People
      </button>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="bg-slate-950/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row items-start gap-6">
          <div className="h-32 w-32 shrink-0 rounded-full overflow-hidden border-2 border-slate-700 bg-slate-800">
            <img
              src={`${API_BASE}/api/v1/people/${person.id}/thumbnail`}
              alt={person.name || "Unnamed face"}
              className="h-full w-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          </div>
          <div className="flex-1 min-w-0">
            {editing ? (
              <div className="space-y-3 max-w-md">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Name this person (empty clears it)"
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => void save()}
                    disabled={saving}
                    className="rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
                  >
                    {saving ? "Saving..." : "Save"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEditing(false);
                      setName(person.name ?? "");
                    }}
                    className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:text-white"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  {person.name || "Unnamed face"}
                </h1>
                <p className="mt-1 font-mono text-xs text-slate-500">{person.id}</p>
                <p className="mt-2 text-xs text-slate-500">
                  {person.asset_count} photo{person.asset_count === 1 ? "" : "s"}
                  {person.isHidden ? " · hidden" : ""}
                  {person.updatedAt ? ` · updated ${person.updatedAt.slice(0, 10)}` : ""}
                </p>
                <div className="mt-3 flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEditing(true)}
                    className="flex items-center gap-1 rounded-xl border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:text-white"
                  >
                    <Pencil className="h-4 w-4" /> {person.name ? "Rename" : "Name this person"}
                  </button>
                  {confirmDelete ? (
                    <button
                      type="button"
                      onClick={() => void remove()}
                      disabled={deleting}
                      className="rounded-xl bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50"
                    >
                      {deleting ? "Deleting..." : "Confirm delete (photos stay, faces unassigned)"}
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
              </>
            )}
          </div>
        </div>
      </div>

      <div className="bg-slate-950/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm">
        <h2 className="text-lg font-semibold text-white mb-4">
          Photos ({person.assets.length})
          {person.asset_count > person.assets.length && (
            <span className="ml-2 text-xs font-normal text-slate-500">
              showing first {person.assets.length} of {person.asset_count} — refine in Photos search
            </span>
          )}
        </h2>
        {person.assets.length === 0 ? (
          <p className="text-sm text-slate-500">
            No photos linked yet. Face re-clustering may still be running.
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {person.assets.map((a) => (
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
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
