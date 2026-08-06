import { API_BASE } from "@/lib/api";
import {
  Archive,
  Calendar,
  CalendarRange,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Filter,
  Image as ImageIcon,
  Info,
  Loader2,
  MapPin,
  Maximize2,
  Minimize2,
  RotateCcw,
  Search,
  Star,
  Video,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

interface PhotoResult {
  id: string;
  original_filename: string;
  created_at: string;
  type?: string;
  smart_search_score?: number;
}

interface TimelineResponse {
  items: PhotoResult[];
  page: number;
  limit: number;
  total: number;
  has_more: boolean;
}

interface TimelineFilters {
  assetType: "" | "IMAGE" | "VIDEO";
  isFavorite: boolean;
  withArchived: boolean;
  takenAfter: string;
  takenBefore: string;
}

const EMPTY_FILTERS: TimelineFilters = {
  assetType: "",
  isFavorite: false,
  withArchived: false,
  takenAfter: "",
  takenBefore: "",
};

const PAGE_SIZE = 200;

const VIDEO_EXT = /\.(mov|mp4|mkv|insv|webm|avi|m4v)$/i;
const ZOOM_MIN = 1;
const ZOOM_MAX = 8;
const ZOOM_STEP = 1.25;

interface PhotoExif {
  make?: string;
  model?: string;
  lensModel?: string;
  fNumber?: number;
  exposureTime?: number | string;
  iso?: number;
  focalLength?: string;
  exifImageWidth?: number;
  exifImageHeight?: number;
  fileSizeInByte?: number;
  dateTimeOriginal?: string;
  timeZone?: string;
  gpsLatitude?: number;
  gpsLongitude?: number;
}

interface PhotoMeta {
  id: string;
  original_filename?: string;
  file_path?: string;
  type?: string;
  created_at?: string;
  file_created_at?: string;
  is_favorite?: boolean;
  is_archived?: boolean;
  is_trashed?: boolean;
  file_size_bytes?: number;
  exif_info?: PhotoExif;
  smart_info?: { description?: string; tags?: string[] };
  people?: { name?: string }[];
  albums?: { album_name?: string }[];
}

function isVideo(photo: PhotoResult): boolean {
  if (photo.type) return photo.type === "VIDEO";
  return VIDEO_EXT.test(photo.original_filename);
}

function formatBytes(bytes?: number): string {
  if (!bytes || bytes <= 0) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 100 ? 0 : 1)} ${units[unit]}`;
}

function formatDateTime(iso?: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function MetaRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="py-2 border-b border-slate-800/60 last:border-0">
      <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-0.5">
        {label}
      </dt>
      <dd className="text-sm text-slate-200 break-words">{children}</dd>
    </div>
  );
}

function PhotoViewer({
  photo,
  hasNav,
  onPrev,
  onNext,
  onClose,
}: {
  photo: PhotoResult;
  hasNav: boolean;
  onPrev: () => void;
  onNext: () => void;
  onClose: () => void;
}) {
  const src = `${API_BASE}/api/v1/photos/${photo.id}/file`;
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mediaWrapRef = useRef<HTMLDivElement | null>(null);
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showMeta, setShowMeta] = useState(false);
  const [meta, setMeta] = useState<PhotoMeta | null>(null);
  const [metaLoading, setMetaLoading] = useState(false);
  const [metaError, setMetaError] = useState<string | null>(null);
  const scaleRef = useRef(scale);
  scaleRef.current = scale;
  const translateRef = useRef(translate);
  translateRef.current = translate;
  const dragRef = useRef<{ startX: number; startY: number; tx: number; ty: number } | null>(null);

  useEffect(() => {
    setScale(1);
    setTranslate({ x: 0, y: 0 });
    setShowMeta(false);
    setMeta(null);
  }, [photo.id]);

  const clampTranslate = useCallback((x: number, y: number) => {
    const el = mediaWrapRef.current;
    if (!el) return { x, y };
    const rect = el.getBoundingClientRect();
    const maxX = (rect.width / 2) * (scaleRef.current - 1);
    const maxY = (rect.height / 2) * (scaleRef.current - 1);
    return {
      x: Math.min(Math.max(x, -maxX), maxX),
      y: Math.min(Math.max(y, -maxY), maxY),
    };
  }, []);

  const zoomAt = useCallback(
    (clientX: number, clientY: number, factor: number) => {
      const el = mediaWrapRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const px = clientX - rect.left - rect.width / 2;
      const py = clientY - rect.top - rect.height / 2;
      const { x: tx, y: ty } = translateRef.current;
      const current = scaleRef.current;
      const next = Math.min(Math.max(current * factor, ZOOM_MIN), ZOOM_MAX);
      const nextX = px - ((px - tx) * next) / current;
      const nextY = py - ((py - ty) * next) / current;
      setScale(next);
      setTranslate(clampTranslate(nextX, nextY));
    },
    [clampTranslate],
  );

  const resetZoom = useCallback(() => {
    setScale(1);
    setTranslate({ x: 0, y: 0 });
  }, []);

  // Wheel zoom — attached non-passively so preventDefault works.
  useEffect(() => {
    const el = mediaWrapRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      zoomAt(e.clientX, e.clientY, e.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [zoomAt]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (document.fullscreenElement) {
          void document.exitFullscreen();
          return;
        }
        onClose();
        return;
      }
      if (e.key === "ArrowLeft" && hasNav) onPrev();
      if (e.key === "ArrowRight" && hasNav) onNext();
      if (e.key === "+" || e.key === "=") {
        zoomAt(window.innerWidth / 2, window.innerHeight / 2, ZOOM_STEP);
      }
      if (e.key === "-" || e.key === "_") {
        zoomAt(window.innerWidth / 2, window.innerHeight / 2, 1 / ZOOM_STEP);
      }
      if (e.key === "0") resetZoom();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, onPrev, onNext, hasNav, zoomAt, resetZoom]);

  useEffect(() => {
    const onChange = () => setIsFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  useEffect(() => {
    if (!showMeta) return;
    setMetaLoading(true);
    setMetaError(null);
    fetch(`${API_BASE}/api/v1/photos/${photo.id}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => setMeta(d as PhotoMeta))
      .catch((e: unknown) =>
        setMetaError(e instanceof Error ? e.message : "Failed to load metadata"),
      )
      .finally(() => setMetaLoading(false));
  }, [showMeta, photo.id]);

  const toggleFullscreen = () => {
    if (document.fullscreenElement) {
      void document.exitFullscreen();
    } else {
      void containerRef.current?.requestFullscreen();
    }
  };

  const onPointerDown = (e: React.PointerEvent) => {
    if (scaleRef.current <= 1) return;
    e.stopPropagation();
    (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId);
    dragRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      tx: translateRef.current.x,
      ty: translateRef.current.y,
    };
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (!dragRef.current) return;
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;
    setTranslate(clampTranslate(dragRef.current.tx + dx, dragRef.current.ty + dy));
  };

  const onPointerUp = (e: React.PointerEvent) => {
    dragRef.current = null;
    (e.currentTarget as HTMLElement).releasePointerCapture?.(e.pointerId);
  };

  const onDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (scaleRef.current > 1) {
      resetZoom();
    } else {
      zoomAt(e.clientX, e.clientY, 2.5);
    }
  };

  const exif = meta?.exif_info ?? {};
  const gps =
    typeof exif.gpsLatitude === "number" && typeof exif.gpsLongitude === "number"
      ? { lat: exif.gpsLatitude, lon: exif.gpsLongitude }
      : null;
  const shutter =
    typeof exif.exposureTime === "number"
      ? `1/${Math.round(1 / exif.exposureTime)} s`
      : exif.exposureTime;

  const navButtonClass =
    "absolute top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-slate-900/70 border border-slate-700/60 text-slate-300 hover:bg-slate-800 hover:text-white transition-all backdrop-blur-md";
  const toolButtonClass =
    "p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/70 transition-all";

  const mediaTransform = {
    transform: `scale(${scale}) translate(${translate.x}px, ${translate.y}px)`,
  };

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-50 flex flex-col bg-black/95 backdrop-blur-sm animate-in fade-in duration-200"
      data-testid="photo-viewer"
      onClick={onClose}
    >
      <div
        className="relative z-30 flex items-center justify-between px-6 py-4 shrink-0 border-b border-slate-800/60"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 min-w-0">
          <p
            className="text-base font-semibold text-white truncate"
            title={photo.original_filename}
          >
            {photo.original_filename}
          </p>
          <span className="text-sm text-slate-300 shrink-0">
            {new Date(photo.created_at).toLocaleDateString(undefined, {
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </span>
          {photo.smart_search_score != null && (
            <span className="bg-primary/30 px-2 py-0.5 rounded-md text-xs text-primary font-black tracking-wider border border-primary/20 shrink-0">
              {Math.round(photo.smart_search_score * 100)}% match
            </span>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={toggleFullscreen}
            data-testid="photo-viewer-fullscreen"
            className={toolButtonClass}
            title={isFullscreen ? "Exit fullscreen (F11)" : "Fullscreen (F11)"}
          >
            {isFullscreen ? <Minimize2 className="h-5 w-5" /> : <Maximize2 className="h-5 w-5" />}
          </button>
          <button
            type="button"
            onClick={() => setShowMeta((v) => !v)}
            data-testid="photo-viewer-meta-toggle"
            className={`${toolButtonClass} ${showMeta ? "text-primary bg-primary/10" : ""}`}
            title="Metadata (i)"
          >
            <Info className="h-5 w-5" />
          </button>
          <button
            type="button"
            onClick={onClose}
            data-testid="photo-viewer-close"
            className={toolButtonClass}
            title="Close (Esc)"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      <div
        ref={mediaWrapRef}
        className="relative flex-1 flex items-center justify-center min-h-0 px-20 py-4 overflow-hidden select-none"
        onClick={onClose}
      >
        {hasNav && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onPrev();
            }}
            className={`${navButtonClass} left-4`}
            data-testid="photo-viewer-prev"
            title="Previous (←)"
          >
            <ChevronLeft className="h-6 w-6" />
          </button>
        )}
        {isVideo(photo) ? (
          // biome-ignore lint/a11y/useMediaCaption: user home videos have no caption tracks
          <video
            src={src}
            controls
            autoPlay
            className="max-h-full max-w-full rounded-lg shadow-2xl cursor-grab active:cursor-grabbing"
            style={mediaTransform}
            onClick={(e) => e.stopPropagation()}
            onDoubleClick={onDoubleClick}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            data-testid="photo-viewer-media"
          />
        ) : (
          <img
            src={src}
            alt={photo.original_filename}
            className="max-h-full max-w-full object-contain rounded-lg shadow-2xl cursor-grab active:cursor-grabbing"
            style={mediaTransform}
            onClick={(e) => e.stopPropagation()}
            onDoubleClick={onDoubleClick}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            data-testid="photo-viewer-media"
          />
        )}
        {hasNav && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onNext();
            }}
            className={`${navButtonClass} right-4`}
            data-testid="photo-viewer-next"
            title="Next (→)"
          >
            <ChevronRight className="h-6 w-6" />
          </button>
        )}

        {/* Zoom controls */}
        <div
          className="absolute bottom-5 left-1/2 -translate-x-1/2 z-10 flex items-center gap-1 rounded-xl bg-slate-900/85 border border-slate-700/60 backdrop-blur-md px-2 py-1.5"
          onClick={(e) => e.stopPropagation()}
          data-testid="photo-viewer-zoom"
        >
          <button
            type="button"
            onClick={() =>
              zoomAt(
                mediaWrapRef.current?.getBoundingClientRect().left ?? window.innerWidth / 2,
                mediaWrapRef.current?.getBoundingClientRect().top ?? window.innerHeight / 2,
                1 / ZOOM_STEP,
              )
            }
            className="p-1.5 rounded-md text-slate-300 hover:text-white hover:bg-slate-700/60 transition-all"
            title="Zoom out (-)"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <span className="w-14 text-center text-sm text-slate-200 font-medium tabular-nums">
            {Math.round(scale * 100)}%
          </span>
          <button
            type="button"
            onClick={() =>
              zoomAt(
                mediaWrapRef.current?.getBoundingClientRect().left ?? window.innerWidth / 2,
                mediaWrapRef.current?.getBoundingClientRect().top ?? window.innerHeight / 2,
                ZOOM_STEP,
              )
            }
            className="p-1.5 rounded-md text-slate-300 hover:text-white hover:bg-slate-700/60 transition-all"
            title="Zoom in (+)"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={resetZoom}
            className="p-1.5 rounded-md text-slate-300 hover:text-white hover:bg-slate-700/60 transition-all"
            title="Reset zoom (0)"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>

        {scale > 1 && (
          <div
            className="absolute bottom-5 left-1/2 translate-x-[9rem] z-10 text-xs text-slate-400 pointer-events-none"
            onClick={(e) => e.stopPropagation()}
          >
            Drag to pan · double-click to reset
          </div>
        )}
      </div>

      {/* Metadata panel */}
      {showMeta && (
        <aside
          className="absolute top-16 inset-y-0 right-0 z-20 w-80 max-w-[85%] bg-slate-950/95 border-l border-slate-800/70 backdrop-blur-xl overflow-y-auto p-5"
          onClick={(e) => e.stopPropagation()}
          data-testid="photo-viewer-meta"
        >
          <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Metadata</h3>
          {metaLoading && <p className="text-sm text-slate-400">Loading…</p>}
          {metaError && (
            <p className="text-sm text-red-400">Failed to load metadata: {metaError}</p>
          )}
          {meta && (
            <dl>
              <MetaRow label="Filename">{meta.original_filename ?? "—"}</MetaRow>
              {meta.file_path && <MetaRow label="Path">{meta.file_path}</MetaRow>}
              <MetaRow label="Type">{meta.type ?? "—"}</MetaRow>
              <MetaRow label="Size">
                {formatBytes(meta.file_size_bytes ?? exif.fileSizeInByte)}
              </MetaRow>
              <MetaRow label="Dimensions">
                {exif.exifImageWidth && exif.exifImageHeight
                  ? `${exif.exifImageWidth} × ${exif.exifImageHeight}`
                  : "—"}
              </MetaRow>
              <MetaRow label="Date taken">
                {formatDateTime(exif.dateTimeOriginal ?? meta.file_created_at)}
              </MetaRow>
              <MetaRow label="Imported">{formatDateTime(meta.created_at)}</MetaRow>
              <MetaRow label="Camera">
                {[exif.make, exif.model].filter(Boolean).join(" ") || "—"}
              </MetaRow>
              <MetaRow label="Lens">{exif.lensModel || "—"}</MetaRow>
              <MetaRow label="Aperture">
                {typeof exif.fNumber === "number" ? `f/${exif.fNumber}` : "—"}
              </MetaRow>
              <MetaRow label="Shutter">{shutter ?? "—"}</MetaRow>
              <MetaRow label="ISO">
                {typeof exif.iso === "number" ? `ISO ${exif.iso}` : "—"}
              </MetaRow>
              <MetaRow label="Focal length">
                {exif.focalLength ? `${exif.focalLength}` : "—"}
              </MetaRow>
              {gps && (
                <MetaRow label="Location">
                  <a
                    href={`https://www.google.com/maps?q=${gps.lat},${gps.lon}`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-primary hover:underline"
                  >
                    <MapPin className="h-3.5 w-3.5" />
                    {gps.lat.toFixed(5)}, {gps.lon.toFixed(5)}
                  </a>
                </MetaRow>
              )}
              <MetaRow label="Status">
                {meta.is_favorite || meta.is_archived || meta.is_trashed ? (
                  <span className="inline-flex flex-wrap gap-1.5">
                    {meta.is_favorite && (
                      <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/15 border border-amber-500/40 px-2 py-0.5 text-xs font-medium text-amber-300">
                        <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> Favorite
                      </span>
                    )}
                    {meta.is_archived && (
                      <span className="inline-flex items-center gap-1 rounded-md bg-slate-700/40 border border-slate-600/50 px-2 py-0.5 text-xs font-medium text-slate-300">
                        <Archive className="h-3 w-3" /> Archived
                      </span>
                    )}
                    {meta.is_trashed && (
                      <span className="inline-flex items-center gap-1 rounded-md bg-red-500/15 border border-red-500/40 px-2 py-0.5 text-xs font-medium text-red-300">
                        Trashed
                      </span>
                    )}
                  </span>
                ) : (
                  "—"
                )}
              </MetaRow>
              {meta.smart_info?.description && (
                <MetaRow label="Description">{meta.smart_info.description}</MetaRow>
              )}
              {meta.smart_info?.tags && meta.smart_info.tags.length > 0 && (
                <MetaRow label="Tags">{meta.smart_info.tags.join(", ")}</MetaRow>
              )}
              {meta.people && meta.people.length > 0 && (
                <MetaRow label="People">
                  {meta.people.map((p) => p.name ?? "Unknown").join(", ")}
                </MetaRow>
              )}
              {meta.albums && meta.albums.length > 0 && (
                <MetaRow label="Albums">
                  {meta.albums.map((a) => a.album_name ?? "Untitled").join(", ")}
                </MetaRow>
              )}
            </dl>
          )}
        </aside>
      )}

      {hasNav && !showMeta && (
        <div
          className="text-center text-sm text-slate-400 py-3 shrink-0"
          onClick={(e) => e.stopPropagation()}
        >
          Use ← → to browse
        </div>
      )}
    </div>
  );
}

function buildQuery(filters: TimelineFilters, page: number): string {
  const params = new URLSearchParams({ page: String(page), limit: String(PAGE_SIZE) });
  if (filters.assetType) params.set("asset_type", filters.assetType);
  if (filters.isFavorite) params.set("is_favorite", "true");
  if (filters.withArchived) params.set("with_archived", "true");
  // <input type="date"> yields YYYY-MM-DD; Immich needs full ISO datetimes.
  if (filters.takenAfter) params.set("taken_after", `${filters.takenAfter}T00:00:00.000Z`);
  if (filters.takenBefore) params.set("taken_before", `${filters.takenBefore}T23:59:59.999Z`);
  return params.toString();
}

export function Photos() {
  const [query, setQuery] = useState("");
  const [photos, setPhotos] = useState<PhotoResult[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"timeline" | "search">("timeline");
  const [filters, setFilters] = useState<TimelineFilters>(EMPTY_FILTERS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const busyRef = useRef(false);
  const pageRef = useRef(1);
  const reqSeqRef = useRef(0);

  const selectedIndex = photos.findIndex((p) => p.id === selectedId);
  const selected = selectedIndex >= 0 ? photos[selectedIndex] : null;
  const hasNav = photos.length > 1;

  const stepSelection = useCallback(
    (dir: number) => {
      if (photos.length === 0) return;
      const next = (selectedIndex + dir + photos.length) % photos.length;
      setSelectedId(photos[next].id);
    },
    [photos, selectedIndex],
  );

  const loadTimeline = useCallback(
    async (reset: boolean) => {
      // Reset loads always win (rapid filter edits must not be dropped);
      // stale in-flight responses are discarded via the sequence counter.
      // Load-more stays guarded so the sentinel cannot double-fetch.
      if (!reset && busyRef.current) return;
      const seq = ++reqSeqRef.current;
      busyRef.current = true;
      const targetPage = reset ? 1 : pageRef.current + 1;
      if (reset) setLoading(true);
      else setLoadingMore(true);
      setError(null);
      setMode("timeline");
      try {
        const res = await fetch(
          `${API_BASE}/api/v1/photos/timeline?${buildQuery(filters, targetPage)}`,
        );
        if (seq !== reqSeqRef.current) return;
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          const msg =
            (body as { detail?: string }).detail || res.statusText || "Failed to load timeline";
          throw new Error(msg);
        }
        const data = (await res.json()) as TimelineResponse;
        const items = Array.isArray(data.items) ? data.items : [];
        setPhotos((prev) => {
          if (reset) return items;
          const seen = new Set(prev.map((p) => p.id));
          return [...prev, ...items.filter((p) => !seen.has(p.id))];
        });
        setTotal(typeof data.total === "number" ? data.total : 0);
        setHasMore(Boolean(data.has_more));
        pageRef.current = targetPage;
      } catch (err: unknown) {
        if (seq !== reqSeqRef.current) return;
        setError(err instanceof Error ? err.message : "Failed to load photos");
        if (reset) setPhotos([]);
      } finally {
        if (seq === reqSeqRef.current) {
          setLoading(false);
          setLoadingMore(false);
          busyRef.current = false;
        }
      }
    },
    [filters],
  );

  useEffect(() => {
    loadTimeline(true);
  }, [filters]);

  // Infinite scroll: fetch the next page when the sentinel scrolls into view.
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || mode !== "timeline") return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (
          entries[0]?.isIntersecting &&
          hasMore &&
          !loading &&
          !loadingMore &&
          !jumpInProgressRef.current
        ) {
          loadTimeline(false);
        }
      },
      { rootMargin: "600px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, loading, loadingMore, loadTimeline, mode]);

  const searchPhotos = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) {
      loadTimeline(true);
      return;
    }

    setLoading(true);
    setError(null);
    setMode("search");
    setPhotos([]);
    setTotal(0);
    setHasMore(false);
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

  const clearFilters = () => setFilters(EMPTY_FILTERS);

  const hasActiveFilters = useMemo(
    () => JSON.stringify(filters) !== JSON.stringify(EMPTY_FILTERS),
    [filters],
  );

  const groupedPhotos = useMemo(() => {
    const groups: { [key: string]: PhotoResult[] } = {};

    // Sort photos by date descending
    const sorted = [...photos].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    sorted.forEach((photo) => {
      const date = new Date(photo.created_at);
      if (Number.isNaN(date.getTime())) return;
      const key = date.toLocaleString("en-US", { month: "long", year: "numeric" });
      if (!groups[key]) groups[key] = [];
      groups[key].push(photo);
    });

    return Object.entries(groups);
  }, [photos]);

  const [activeMonth, setActiveMonth] = useState<string | null>(null);
  const jumpInProgressRef = useRef(false);

  // Scroll-spy: highlight the month currently in view in the timeline rail.
  useEffect(() => {
    const onScroll = () => {
      const els = document.querySelectorAll<HTMLElement>("[data-month-group]");
      let current: string | null = null;
      els.forEach((el) => {
        if (el.getBoundingClientRect().top <= 260) {
          current = el.dataset.monthGroup ?? null;
        }
      });
      setActiveMonth(current);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, [photos.length]);

  const jumpToMonth = (month: string) => {
    // Suppress sentinel auto-load while smooth-scrolling: a mid-jump page
    // append grows the current month group, shifts the target month down and
    // cancels the browser's smooth scroll. Target the sticky header element so
    // it pins at the top and replaces the previous month's header.
    jumpInProgressRef.current = true;
    const group = document.querySelector(`[data-month-group="${CSS.escape(month)}"]`);
    (group?.firstElementChild as HTMLElement | null | undefined)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
    window.setTimeout(() => {
      jumpInProgressRef.current = false;
    }, 3000);
  };

  const filterButtonClass = (active: boolean) =>
    `inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium border transition-all shrink-0 ${
      active
        ? "bg-primary/20 border-primary/50 text-primary"
        : "border-slate-600/70 text-slate-300 hover:bg-slate-800/70 hover:text-white"
    }`;

  return (
    <div className="space-y-6 pb-20" data-testid="photos-page">
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
              loadTimeline(true);
            }}
            className="px-4 py-3 rounded-lg text-sm font-medium border border-slate-600 text-slate-300 hover:bg-slate-800 shrink-0"
          >
            Show all
          </button>
        )}
      </form>

      {/* Filter bar */}
      {mode === "timeline" && (
        <div
          className="flex flex-wrap items-center gap-2 p-3 bg-slate-950/40 border border-slate-800/60 rounded-xl backdrop-blur-sm"
          data-testid="photos-filters"
        >
          <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-300 uppercase tracking-wider mr-1">
            <Filter className="h-4 w-4" />
            Filters
          </span>

          <div className="relative inline-flex">
            <select
              value={filters.assetType}
              onChange={(e) =>
                setFilters((f) => ({ ...f, assetType: e.target.value as "" | "IMAGE" | "VIDEO" }))
              }
              data-testid="photos-filter-type"
              className="appearance-none bg-slate-900/70 border border-slate-600/70 text-slate-200 text-sm font-medium rounded-lg pl-3 pr-8 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50 cursor-pointer"
            >
              <option value="">All media</option>
              <option value="IMAGE">Photos</option>
              <option value="VIDEO">Videos</option>
            </select>
            <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          </div>

          <button
            type="button"
            onClick={() => setFilters((f) => ({ ...f, isFavorite: !f.isFavorite }))}
            className={filterButtonClass(filters.isFavorite)}
            data-testid="photos-filter-favorite"
            title="Only favorites"
          >
            <Star className={`h-3.5 w-3.5 ${filters.isFavorite ? "fill-primary" : ""}`} />
            Favorites
          </button>

          <button
            type="button"
            onClick={() => setFilters((f) => ({ ...f, withArchived: !f.withArchived }))}
            className={filterButtonClass(filters.withArchived)}
            data-testid="photos-filter-archived"
            title="Include archived photos"
          >
            <Archive className="h-3.5 w-3.5" />
            Include archived
          </button>

          <div className="flex items-center gap-1.5 ml-1">
            <CalendarRange className="h-4 w-4 text-slate-400" />
            <input
              type="date"
              value={filters.takenAfter}
              onChange={(e) => setFilters((f) => ({ ...f, takenAfter: e.target.value }))}
              data-testid="photos-filter-from"
              title="Taken after"
              className="bg-slate-900/70 border border-slate-600/70 text-slate-200 text-sm rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <span className="text-slate-400 text-sm">to</span>
            <input
              type="date"
              value={filters.takenBefore}
              onChange={(e) => setFilters((f) => ({ ...f, takenBefore: e.target.value }))}
              data-testid="photos-filter-to"
              title="Taken before"
              className="bg-slate-900/70 border border-slate-600/70 text-slate-200 text-sm rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {hasActiveFilters && (
            <button
              type="button"
              onClick={clearFilters}
              className="inline-flex items-center gap-1 px-2.5 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800/70 transition-all"
              data-testid="photos-filter-clear"
            >
              <X className="h-4 w-4" />
              Clear
            </button>
          )}

          {!loading && photos.length > 0 && (
            <span className="ml-auto text-sm text-slate-300 font-medium" data-testid="photos-count">
              {total > 0
                ? `Showing ${photos.length} of ${total} photos`
                : `Showing ${photos.length} photos`}
            </span>
          )}
        </div>
      )}

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
              {mode === "search"
                ? "No matching photos."
                : hasActiveFilters
                  ? "No photos match the current filters."
                  : "No photos in library yet."}
            </p>
            <p className="text-sm opacity-60 mt-2 text-center max-w-md">
              {mode === "search"
                ? "Try a different search or click Show all."
                : hasActiveFilters
                  ? "Try widening the date range or clearing filters."
                  : "Add photos via Immich or run a scan."}
            </p>
          </div>
        )}

        {!loading && photos.length > 0 && (
          <div className="flex gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Timeline rail: month navigation with scroll-spy */}
            {mode === "timeline" && (
              <nav
                className="hidden lg:block w-44 shrink-0"
                data-testid="timeline-rail"
                aria-label="Timeline months"
              >
                <div className="sticky top-24 space-y-0.5 border-l border-slate-700/70 pl-4">
                  {groupedPhotos.map(([month]) => (
                    <button
                      key={month}
                      type="button"
                      onClick={() => jumpToMonth(month)}
                      className={`block w-full text-left text-sm rounded-md px-2.5 py-1.5 transition-all ${
                        activeMonth === month
                          ? "bg-primary/15 text-primary font-semibold border-l-2 border-primary -ml-5 pl-3"
                          : "text-slate-400 hover:text-white hover:bg-slate-800/60 -ml-5 pl-3 border-l-2 border-transparent"
                      }`}
                      data-testid="timeline-month"
                    >
                      {month}
                    </button>
                  ))}
                </div>
              </nav>
            )}

            <div className="flex-1 min-w-0 space-y-12">
              {groupedPhotos.map(([month, monthPhotos], groupIndex) => {
                const year = month.split(" ")[1];
                const prevYear =
                  groupIndex > 0 ? groupedPhotos[groupIndex - 1][0].split(" ")[1] : null;
                return (
                  <div key={month}>
                    {year !== prevYear && (
                      <div className="flex items-center gap-4 mb-2" data-testid="timeline-year">
                        <span className="text-3xl font-black text-white/90 tracking-tight">
                          {year}
                        </span>
                        <div className="h-px flex-1 bg-gradient-to-r from-slate-600/60 to-transparent" />
                      </div>
                    )}
                    <div data-month-group={month} className="space-y-4 scroll-mt-28">
                      <div className="flex items-center gap-3 sticky top-0 py-3 bg-slate-950/85 backdrop-blur-xl z-10 -mx-6 px-6 border-b border-slate-800/40">
                        <div className="p-1.5 bg-primary/15 rounded-lg">
                          <Calendar className="h-5 w-5 text-primary" />
                        </div>
                        <h2 className="text-xl font-bold text-white tracking-tight">{month}</h2>
                        <div className="h-px flex-1 bg-gradient-to-r from-slate-700/50 to-transparent" />
                        <span className="text-sm text-slate-300 font-medium bg-slate-900/60 px-3 py-1 rounded-full border border-slate-700">
                          {monthPhotos.length} photos
                        </span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                        {monthPhotos.map((photo) => (
                          <div
                            key={photo.id}
                            onClick={() => setSelectedId(photo.id)}
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
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                            <div className="absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black/95 via-black/40 to-transparent translate-y-4 group-hover:translate-y-0 opacity-0 group-hover:opacity-100 transition-all duration-400 ease-out">
                              <p
                                className="text-xs text-white font-semibold truncate mb-1.5"
                                title={photo.original_filename}
                              >
                                {photo.original_filename}
                              </p>
                              <div className="flex items-center justify-between">
                                <span className="text-xs text-slate-200 font-medium">
                                  {new Date(photo.created_at).toLocaleDateString(undefined, {
                                    day: "numeric",
                                    month: "short",
                                  })}
                                </span>
                                {photo.smart_search_score && (
                                  <div className="bg-primary/30 backdrop-blur-md px-1.5 py-0.5 rounded-md text-[11px] text-primary font-black tracking-wider border border-primary/20">
                                    {Math.round(photo.smart_search_score * 100)}%
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Infinite scroll sentinel + fallback button */}
        {mode === "timeline" && !loading && hasMore && (
          <div ref={sentinelRef} className="flex items-center justify-center py-8">
            {loadingMore ? (
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            ) : (
              <button
                type="button"
                onClick={() => loadTimeline(false)}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium border border-slate-600/70 text-slate-200 hover:bg-slate-800/70 hover:text-white transition-all"
                data-testid="photos-load-more"
              >
                <ChevronDown className="h-4 w-4" />
                Load more
                {total > 0 ? ` (${total - photos.length} remaining)` : ""}
              </button>
            )}
          </div>
        )}

        {mode === "timeline" && !loading && !hasMore && photos.length > 0 && (
          <div className="text-center text-sm text-slate-400 py-6">
            End of timeline — all {total} photos loaded
          </div>
        )}
      </div>

      {selected && (
        <PhotoViewer
          photo={selected}
          hasNav={hasNav}
          onPrev={() => stepSelection(-1)}
          onNext={() => stepSelection(1)}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}
