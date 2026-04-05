import { useState, useEffect } from 'react';
import { Loader2, Library } from 'lucide-react';

interface AlbumResult {
    id: string;
    album_name: string;
    asset_count: number;
    created_at: string;
}

export function Albums() {
    const [albums, setAlbums] = useState<AlbumResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAlbums = async () => {
            try {
                const res = await fetch('/api/v1/albums');
                if (!res.ok) {
                    const body = await res.json().catch(() => ({}));
                    const msg = (body as { detail?: string }).detail || res.statusText || 'Failed to fetch albums';
                    throw new Error(msg);
                }
                const data = await res.json();
                setAlbums(Array.isArray(data) ? data : []);
            } catch (err: unknown) {
                setError(err instanceof Error ? err.message : 'Failed to fetch albums');
            } finally {
                setLoading(false);
            }
        };

        fetchAlbums();
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Albums</h1>
                    <p className="text-slate-400">View and manage your photo albums.</p>
                </div>
            </div>

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
                        <p className="text-xs text-slate-400">Check .env (IMMICH_SERVER_URL, IMMICH_API_KEY) and restart the backend.</p>
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
                        {albums.map(album => (
                            <div key={album.id} className="group relative p-4 bg-slate-900/80 hover:bg-slate-800 rounded-xl border border-slate-700/50 transition-all cursor-pointer">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                                        <Library className="h-5 w-5" />
                                    </div>
                                    <div className="overflow-hidden">
                                        <h3 className="text-sm font-semibold text-white truncate" title={album.album_name}>{album.album_name}</h3>
                                        <p className="text-xs text-slate-400">{album.asset_count} items</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
