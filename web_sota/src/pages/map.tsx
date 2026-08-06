import { useQuery } from "@tanstack/react-query";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Layers, Loader2, MapPin } from "lucide-react";
import { useState } from "react";
import { CircleMarker, MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";

interface MapFeature {
  id: string;
  lat: number;
  lon: number;
  city?: string | null;
  state?: string | null;
  country?: string | null;
}

const TILE_SETS: Record<string, { label: string; url: string; attribution: string }> = {
  dark: {
    label: "Dark",
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; CARTO',
  },
  streets: {
    label: "Streets",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  },
  satellite: {
    label: "Satellite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "Tiles &copy; Esri",
  },
};

const MARKER_ICON = L.icon({
  iconUrl: `data:image/svg+xml;base64,${btoa(
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="#3b82f6" stroke="#0f172a" stroke-width="1.5"><circle cx="12" cy="12" r="8"/></svg>',
  )}`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

export function Map() {
  const {
    data: features,
    isLoading,
    error,
  } = useQuery<MapFeature[]>({
    queryKey: ["mapFeatures"],
    queryFn: async () => {
      const res = await fetch("/api/v1/map/features");
      if (!res.ok) throw new Error("Failed to fetch map data");
      return res.json();
    },
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000,
  });

  const [tileKey, setTileKey] = useState<"dark" | "streets" | "satellite">("dark");
  const tile = TILE_SETS[tileKey];

  const totalAssets = features?.length || 0;

  return (
    <div className="min-h-[70vh] flex flex-col gap-6 pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-3">
            <MapPin className="h-8 w-8 text-primary" />
            Geospatial Discovery
          </h1>
          <p className="text-slate-400">
            {totalAssets.toLocaleString()} geotagged photos rendered from Immich EXIF data.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-xl flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-xs font-bold text-slate-300">
              {isLoading ? "Loading..." : `${totalAssets.toLocaleString()} Geotagged Points`}
            </span>
          </div>
          <div className="px-3 py-2 bg-slate-900/50 border border-slate-800 rounded-xl flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            <select
              title="Map style"
              value={tileKey}
              onChange={(e) => setTileKey(e.target.value as "dark" | "streets" | "satellite")}
              className="bg-transparent border-none text-xs font-semibold text-white focus:ring-0 cursor-pointer"
            >
              {Object.entries(TILE_SETS).map(([key, set]) => (
                <option key={key} value={key} className="bg-slate-900 text-white">
                  {set.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div
        data-testid="photo-map"
        className="relative flex-1 bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden shadow-2xl min-h-[60vh]"
      >
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center z-20 bg-slate-950/70 backdrop-blur">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-10 w-10 text-primary animate-spin" />
              <p className="text-sm font-semibold text-slate-300">Loading map data...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center z-20 bg-slate-950/80 text-red-300 p-8">
            <p className="text-sm font-bold uppercase tracking-widest">Failed to load map</p>
            <p className="text-xs text-slate-400 mt-2">
              Check the Immich connection and try again.
            </p>
          </div>
        )}

        {!isLoading && !error && totalAssets === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center z-20 text-slate-400 p-8">
            <MapPin className="h-12 w-12 opacity-40 mb-3" />
            <p className="text-sm font-bold uppercase tracking-widest">No geotagged photos</p>
            <p className="text-xs mt-2">Photos with EXIF location data will appear here.</p>
          </div>
        )}

        {!isLoading && !error && totalAssets > 0 && (
          <MapContainer
            center={[48.2, 16.35]}
            zoom={5}
            minZoom={2}
            className="h-full w-full z-0"
            style={{ height: "60vh", background: "#0f172a" }}
          >
            <TileLayer key={tileKey} url={tile.url} attribution={tile.attribution} />
            <MarkerClusterGroup chunkedLoading>
              {features!.map((f) =>
                f.lat && f.lon ? (
                  <Marker key={f.id} position={[f.lat, f.lon]} icon={MARKER_ICON}>
                    <Popup>
                      <div className="text-xs">
                        <div className="font-semibold text-slate-800">
                          {[f.city, f.state, f.country].filter(Boolean).join(", ") || "Photo"}
                        </div>
                        <div className="text-slate-500">
                          {f.lat.toFixed(4)}, {f.lon.toFixed(4)}
                        </div>
                        <div className="text-slate-400 mt-1 break-all">{f.id}</div>
                      </div>
                    </Popup>
                  </Marker>
                ) : (
                  <CircleMarker
                    key={f.id}
                    center={[f.lat, f.lon]}
                    radius={2}
                    pathOptions={{ color: "#3b82f6", fillColor: "#3b82f6", fillOpacity: 0.8 }}
                  >
                    <Popup>
                      <div className="text-xs">
                        <div className="font-semibold text-slate-800">
                          {[f.city, f.state, f.country].filter(Boolean).join(", ") || "Photo"}
                        </div>
                        <div className="text-slate-400 mt-1 break-all">{f.id}</div>
                      </div>
                    </Popup>
                  </CircleMarker>
                ),
              )}
            </MarkerClusterGroup>
          </MapContainer>
        )}
      </div>
    </div>
  );
}
