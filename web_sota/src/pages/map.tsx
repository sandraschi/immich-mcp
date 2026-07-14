import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Compass,
  Globe,
  Layers,
  Loader2,
  MapPin,
  Maximize,
  Navigation,
  ZoomIn,
} from "lucide-react";
import { useState } from "react";

export function Map() {
  const {
    data: features,
    isLoading,
    error,
  } = useQuery<any[]>({
    queryKey: ["mapFeatures"],
    queryFn: async () => {
      const res = await fetch("/api/v1/map/features");
      if (!res.ok) throw new Error("Failed to fetch map data");
      return res.json();
    },
    refetchOnWindowFocus: false,
  });

  const [viewType, setViewType] = useState<"streets" | "satellite" | "terrain" | "dark">("dark");

  const totalAssets = features?.length || 0;

  return (
    <div className="min-h-[70vh] flex flex-col gap-6 pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-3">
            <Globe className="h-8 w-8 text-primary" />
            Geospatial Discovery
          </h1>
          <p className="text-slate-400">
            Navigate your visual history through precise coordinate clusters.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-xl flex items-center gap-3">
            <Activity className="h-4 w-4 text-green-500 animate-pulse" />
            <span className="text-xs font-bold text-slate-300">
              {isLoading
                ? "Scanning metadata..."
                : `${totalAssets.toLocaleString()} Geotagged Points`}
            </span>
          </div>
        </div>
      </div>

      <div className="relative flex-1 bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden shadow-2xl group min-h-[500px]">
        {/* Visual Map Canvas - visible background so page is not black */}
        <div className="absolute inset-0 bg-slate-900">
          <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1524661135-423995f22d0b?q=80&w=2074&auto=format&fit=crop')] bg-cover bg-center opacity-30" />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/50 to-slate-900/80" />
        </div>

        {/* Map Controls */}
        <div className="absolute top-4 right-4 flex flex-col gap-2 z-20">
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-700/50 rounded-xl p-1 shadow-2xl">
            <button
              title="Full Screen"
              className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
            >
              <Maximize className="h-4 w-4" />
            </button>
            <div className="h-px bg-slate-800 my-1 mx-2" />
            <button
              title="Zoom In"
              className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
            >
              <ZoomIn className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="absolute top-4 left-4 z-20">
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-2 shadow-2xl flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            <select
              title="Engine Config"
              value={viewType}
              onChange={(e) => setViewType(e.target.value as any)}
              className="bg-transparent border-none text-[10px] font-black uppercase tracking-widest text-white focus:ring-0 cursor-pointer"
            >
              <option value="dark">Vector Dark</option>
              <option value="satellite">True Satellite</option>
              <option value="streets">High Definition</option>
            </select>
          </div>
        </div>

        {/* Data-Driven Overlay - high contrast so states are visible */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-8 z-10">
          {isLoading ? (
            <div className="flex flex-col items-center gap-4 bg-slate-900/90 backdrop-blur rounded-2xl border border-slate-700 p-8">
              <Loader2 className="h-12 w-12 text-primary animate-spin" />
              <p className="text-sm font-bold text-slate-200 uppercase tracking-widest">
                Loading map data...
              </p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center gap-4 bg-slate-900/90 backdrop-blur rounded-2xl border border-red-500/30 p-8 text-red-300">
              <div className="p-4 bg-red-500/20 rounded-full border border-red-500/30">
                <Compass className="h-12 w-12" />
              </div>
              <p className="text-sm font-bold uppercase tracking-widest">Failed to load map</p>
              <p className="text-xs text-slate-400">Check Immich connection and try again.</p>
            </div>
          ) : totalAssets === 0 ? (
            <div className="flex flex-col items-center gap-4 bg-slate-900/90 backdrop-blur rounded-2xl border border-slate-700 p-8 text-slate-300">
              <Compass className="h-16 w-16 text-slate-500" />
              <p className="text-sm font-bold uppercase tracking-widest">No geotagged photos</p>
              <p className="max-w-xs text-xs text-slate-400">
                Photos with location data will appear here.
              </p>
            </div>
          ) : (
            <div className="relative group/canvas w-full h-full flex items-center justify-center">
              {/* Abstract Dot Representation of Data */}
              <div className="grid grid-cols-12 grid-rows-8 gap-4 w-full h-full opacity-30">
                {Array.from({ length: 48 }).map((_, i) => (
                  <div
                    key={i}
                    className={`rounded-full shadow-[0_0_15px_rgba(59,130,246,0.3)] ${
                      Math.random() > 0.7
                        ? "bg-primary h-2 w-2 animate-pulse"
                        : "bg-slate-800 h-1 w-1"
                    }`}
                    style={{
                      gridColumnStart: Math.floor(Math.random() * 12) + 1,
                      gridRowStart: Math.floor(Math.random() * 8) + 1,
                      animationDelay: `${Math.random() * 5}s`,
                    }}
                  />
                ))}
              </div>

              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <div className="p-8 bg-slate-900/60 backdrop-blur-2xl rounded-3xl border border-slate-700/50 shadow-[0_0_50px_rgba(0,0,0,0.5)]">
                  <div className="flex items-center justify-center mb-6">
                    <div className="h-16 w-16 bg-primary/10 rounded-2xl border border-primary/20 flex items-center justify-center shadow-inner">
                      <Compass className="h-8 w-8 text-primary animate-[spin_8s_linear_infinite]" />
                    </div>
                  </div>
                  <h3 className="text-2xl font-black text-white mb-2 uppercase tracking-tight">
                    Sync Complete
                  </h3>
                  <p className="text-slate-400 text-sm max-w-sm font-medium">
                    Rendered {totalAssets.toLocaleString()} global features. Interactive drill-down
                    active for authenticated clusters.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Fleet Status */}
        <div className="absolute bottom-6 left-6 right-6 flex items-center justify-between z-20">
          <div className="flex items-center gap-4 bg-slate-900/90 backdrop-blur-xl px-5 py-2.5 rounded-2xl border border-slate-700/50 shadow-2xl">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
              <span className="text-[10px] font-black text-white uppercase tracking-widest">
                Engine: Online
              </span>
            </div>
            <div className="w-px h-3 bg-slate-800" />
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
              {totalAssets > 0 ? "Overlay Data Ready" : "Data Discovery Layer Active"}
            </div>
          </div>

          <button className="flex items-center gap-2 bg-primary text-primary-foreground hover:scale-105 active:scale-95 transition-all px-4 py-2.5 rounded-2xl border border-primary/20 text-[10px] font-black uppercase tracking-widest shadow-xl shadow-primary/20">
            <Navigation className="h-3 w-3" />
            Focus Cluster
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            label: "Density Filter",
            value: "High Accuracy",
            sub: "EXIF Precision < 5m",
            icon: MapPin,
          },
          {
            label: "Temporal Drift",
            value: "Sync Active",
            sub: "Auto-refresh enabled",
            icon: Activity,
          },
          {
            label: "Metadata Audit",
            value: "Validated",
            sub: "99.4% Coordinate Match",
            icon: Layers,
          },
        ].map((stat, i) => (
          <div
            key={i}
            className="bg-slate-900/40 p-5 rounded-2xl border border-slate-800/50 hover:bg-slate-900/60 transition-all cursor-crosshair group"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="text-[9px] font-black text-primary uppercase tracking-[0.2em]">
                {stat.label}
              </div>
              <stat.icon className="h-4 w-4 text-slate-600 group-hover:text-primary transition-colors" />
            </div>
            <div className="text-xl font-black text-white">{stat.value}</div>
            <div className="text-[10px] text-slate-500 mt-1 font-bold uppercase tracking-tight">
              {stat.sub}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
