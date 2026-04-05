import { useState, useEffect } from 'react';
import { Loader2, Users, Search, User, Filter } from 'lucide-react';

interface Person {
    id: string;
    name: string;
    assetCount: number;
    thumbnailPath?: string;
}

export function People() {
    const [people, setPeople] = useState<Person[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

    useEffect(() => {
        const fetchPeople = async () => {
            try {
                const res = await fetch('/api/v1/people');
                if (!res.ok) {
                    const body = await res.json().catch(() => ({}));
                    const msg = (body as { detail?: string }).detail || res.statusText || 'Failed to fetch people';
                    throw new Error(msg);
                }
                const data = await res.json();
                setPeople(Array.isArray(data) ? data : []);
            } catch (err: unknown) {
                setError(err instanceof Error ? err.message : 'Failed to fetch people');
            } finally {
                setLoading(false);
            }
        };

        fetchPeople();
    }, []);

    const filteredPeople = people.filter(p =>
        (p.name || 'Unnamed').toLowerCase().includes(searchQuery.toLowerCase()) &&
        p.assetCount > 1
    );

    return (
        <div className="space-y-6 pb-20">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">People</h1>
                    <p className="text-slate-400">Manage face recognition clusters and identify family & friends.</p>
                </div>
                <div className="flex items-center gap-2 bg-slate-900/50 p-1 rounded-lg border border-slate-800">
                    <button
                        onClick={() => setViewMode('grid')}
                        className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${viewMode === 'grid' ? 'bg-primary text-primary-foreground shadow-lg' : 'text-slate-400 hover:text-white'}`}
                    >
                        Grid
                    </button>
                    <button
                        onClick={() => setViewMode('list')}
                        className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${viewMode === 'list' ? 'bg-primary text-primary-foreground shadow-lg' : 'text-slate-400 hover:text-white'}`}
                    >
                        List
                    </button>
                </div>
            </div>

            <div className="relative w-full max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Filter by name..."
                    className="w-full bg-slate-900/50 border border-slate-700/50 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                />
            </div>

            <div className="bg-slate-950/30 border border-slate-800/50 rounded-2xl p-6 backdrop-blur-sm min-h-[500px]">
                {loading && (
                    <div className="flex flex-col items-center justify-center h-64 text-slate-500">
                        <Loader2 className="h-10 w-10 mb-4 animate-spin text-primary" />
                        <p className="text-sm font-medium">Clustering faces...</p>
                    </div>
                )}

                {error && (
                    <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 mb-6 space-y-1">
                        <p className="font-medium">No connection to Immich</p>
                        <p className="text-sm">{error}</p>
                        <p className="text-xs text-slate-400">Check .env (IMMICH_SERVER_URL, IMMICH_API_KEY) and restart the backend.</p>
                    </div>
                )}

                {!loading && !error && filteredPeople.length === 0 && (
                    <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-500 py-12">
                        <Users className="h-12 w-12 mb-4 opacity-20" />
                        <p className="text-lg font-medium">No people found.</p>
                        <p className="text-sm opacity-60 mt-2">Try re-running face detection in the Immich dashboard.</p>
                    </div>
                )}

                {!loading && filteredPeople.length > 0 && (
                    <div className={viewMode === 'grid'
                        ? "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6"
                        : "space-y-2"
                    }>
                        {filteredPeople.map(person => (
                            viewMode === 'grid' ? (
                                <div key={person.id} className="group relative flex flex-col items-center gap-3 p-4 bg-slate-900/40 hover:bg-slate-800/60 rounded-2xl border border-slate-800/50 transition-all duration-300 cursor-pointer hover:-translate-y-1 shadow-lg border-b-2 hover:border-b-primary/50">
                                    <div className="relative h-24 w-24 rounded-full overflow-hidden border-2 border-slate-800 group-hover:border-primary/30 transition-colors shadow-2xl">
                                        {person.thumbnailPath ? (
                                            <img
                                                src={`/api/v1/people/${person.id}/thumbnail`}
                                                alt={person.name}
                                                className="h-full w-full object-cover"
                                                onError={(e) => {
                                                    const target = e.target as HTMLImageElement;
                                                    target.style.display = 'none';
                                                    target.parentElement!.classList.add('flex', 'items-center', 'justify-center', 'bg-slate-800');
                                                    const icon = document.createElement('div');
                                                    icon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-600"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';
                                                    target.parentElement!.appendChild(icon.firstChild!);
                                                }}
                                            />
                                        ) : (
                                            <div className="h-full w-full flex items-center justify-center bg-slate-800">
                                                <User className="h-10 w-10 text-slate-600" />
                                            </div>
                                        )}
                                    </div>
                                    <div className="text-center w-full overflow-hidden">
                                        <h3 className="text-sm font-bold text-white truncate px-2" title={person.name || 'Unnamed'}>
                                            {person.name || 'Unnamed'}
                                        </h3>
                                        <span className="text-[10px] font-medium text-slate-500 uppercase tracking-widest">
                                            {person.assetCount} Assets
                                        </span>
                                    </div>
                                    {/* Action button */}
                                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <div className="p-1 bg-primary/20 rounded-md border border-primary/20">
                                            <Filter className="h-3 w-3 text-primary" />
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div key={person.id} className="flex items-center justify-between p-3 bg-slate-900/30 hover:bg-slate-800/50 rounded-xl border border-slate-800/50 transition-colors cursor-pointer group">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 group-hover:border-primary/30 transition-colors overflow-hidden">
                                            <User className="h-5 w-5 text-slate-600" />
                                        </div>
                                        <div>
                                            <h3 className="text-sm font-semibold text-slate-200">{person.name || 'Unnamed'}</h3>
                                            <p className="text-xs text-slate-500">{person.id}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className="text-xs font-medium text-slate-400 bg-slate-800/50 px-2 py-1 rounded-md border border-slate-700/50">
                                            {person.assetCount} assets
                                        </span>
                                        <button className="text-primary opacity-0 group-hover:opacity-100 transition-opacity text-xs font-bold uppercase tracking-tighter">
                                            Manage
                                        </button>
                                    </div>
                                </div>
                            )
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
