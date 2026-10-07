"""Library reconciliation engine for ImmichMCP.

Czkawka-grade comparator in pure Python (exact checksums + perceptual dHash),
plus iCloud/OneDrive cloud-placeholder detection and HEIC+MOV Live Photo pairing.

The engine is headless by design: no GUI tool dependency, HEIC-native via
pillow-heif, and safe for the PyInstaller native build. An optional
``czkawka_cli`` adapter is provided for environments that have the binary.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("immich_mcp.reconcile")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif", ".tiff", ".bmp", ".avif"}
VIDEO_EXTS = {".mov", ".mp4", ".m4v", ".avi", ".mkv", ".webm"}
MEDIA_EXTS = IMAGE_EXTS | VIDEO_EXTS
LIVE_STILL_EXTS = {".heic", ".heif"}
LIVE_MOV_EXTS = {".mov"}

# Windows cloud-file (iCloud/OneDrive placeholder) attributes
_FILE_ATTRIBUTE_OFFLINE = 0x1000
_FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x400000
_FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x40000
_PLACEHOLDER_FLAGS = _FILE_ATTRIBUTE_OFFLINE | _FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS | _FILE_ATTRIBUTE_RECALL_ON_OPEN


# ---------------------------------------------------------------------------
# Cloud placeholder detection (Windows)
# ---------------------------------------------------------------------------
def _win_file_attributes(path: str) -> int:
    """Return Win32 file attributes via GetFileAttributesW (-1 on error/non-Windows)."""
    if os.name != "nt":
        return -1
    import ctypes

    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        return int(attrs) if attrs != -1 else -1
    except Exception:
        return -1


def is_cloud_placeholder(path: str) -> bool:
    """True if the file is a cloud placeholder (dataless stub), not real bytes.

    Reading a placeholder triggers hydration (downloads the full file from
    iCloud/OneDrive), so scanners MUST check this before hashing.
    """
    attrs = _win_file_attributes(path)
    if attrs == -1:
        # Non-Windows or unreadable: fall back to the size heuristic.
        try:
            return Path(path).stat().st_size == 0
        except OSError:
            return False
    return bool(attrs & _PLACEHOLDER_FLAGS)


# ---------------------------------------------------------------------------
# Hashing (Immich-compatible checksums)
# ---------------------------------------------------------------------------
def hash_file(path: str, algorithm: str = "sha1") -> str:
    """Return the base64 digest of a file, matching Immich's asset checksum format.

    Immich stores checksums as base64-encoded digests (SHA-1 on v2.x; the
    algorithm is probed at compare time and passed in).
    """
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode("ascii")


def digest_length(checksum: str) -> int:
    """Return the decoded byte length of an Immich checksum (20=sha1, 32=sha256)."""
    try:
        return len(base64.b64decode(checksum))
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Folder scanning
# ---------------------------------------------------------------------------
@dataclass
class FileRecord:
    """One media file discovered by the scanner."""

    path: str
    name: str
    stem: str
    ext: str
    size_bytes: int
    mtime: float
    is_placeholder: bool
    checksum: str | None = None
    live_pair: str | None = None  # stem of the paired HEIC/MOV sibling


def scan_folder(
    root: str,
    *,
    extensions: set[str] | None = None,
    max_depth: int | None = None,
    hash_files: bool = True,
    algorithm: str = "sha1",
) -> tuple[list[FileRecord], list[str]]:
    """Walk a folder and produce FileRecords.

    Cloud placeholders are flagged and NEVER hashed (hashing hydrates them).
    Live Photo siblings (same stem, HEIC/HEIF + MOV) are linked via live_pair.
    Returns ``(records, errors)``.
    """
    exts = extensions or MEDIA_EXTS
    records: list[FileRecord] = []
    errors: list[str] = []
    root_path = Path(root)
    if not root_path.is_dir():
        return [], [f"Folder not found: {root}"]

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip hidden directories (e.g. iCloud's .photoslibrary internals)
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if max_depth is not None:
            depth = len(Path(dirpath).relative_to(root_path).parts)
            if depth >= max_depth:
                dirnames[:] = []
        for name in filenames:
            ext = Path(name).suffix.lower()
            if ext not in exts:
                continue
            full = os.path.join(dirpath, name)
            try:
                st = os.stat(full)
                placeholder = is_cloud_placeholder(full)
                rec = FileRecord(
                    path=full,
                    name=name,
                    stem=Path(name).stem,
                    ext=ext,
                    size_bytes=st.st_size,
                    mtime=st.st_mtime,
                    is_placeholder=placeholder,
                    checksum=None,
                )
                if not placeholder and hash_files:
                    rec.checksum = hash_file(full, algorithm)
                records.append(rec)
            except OSError as e:
                errors.append(f"{full}: {e}")

    # Link Live Photo pairs (HEIC still + MOV video, same stem)
    by_stem: dict[str, list[FileRecord]] = {}
    for rec in records:
        by_stem.setdefault(rec.stem, []).append(rec)
    for _stem, group in by_stem.items():
        if len(group) != 2:
            continue
        still = next((r for r in group if r.ext in LIVE_STILL_EXTS), None)
        movie = next((r for r in group if r.ext in LIVE_MOV_EXTS), None)
        if still and movie:
            still.live_pair = movie.stem
            movie.live_pair = still.stem
    return records, errors


# ---------------------------------------------------------------------------
# Library index (checksum -> asset) built from the Immich API
# ---------------------------------------------------------------------------
async def probe_checksum_algorithm(client) -> str:
    """Determine the checksum algorithm the connected Immich uses.

    Fetches one asset and inspects its checksum length: 20 bytes = SHA-1,
    32 bytes = SHA-256. Falls back to SHA-1 when nothing is inspectable.
    """
    try:
        items, _ = await client.search_metadata(page=1, size=1)
    except Exception:
        return "sha1"
    for item in items or []:
        c = item.get("checksum") or ""
        if c and digest_length(c) == 32:
            return "sha256"
    return "sha1"


async def build_checksum_index(client, *, algorithm: str | None = None) -> tuple[dict[str, dict], str]:
    """Page the whole library and return ``{checksum: {id, originalPath, originalFileName}}``.

    Also returns the verified algorithm name (probed from a live asset when
    ``algorithm`` is not provided).
    """
    algo = algorithm or await probe_checksum_algorithm(client)
    index: dict[str, dict] = {}
    page = 1
    while True:
        items, total = await client.search_metadata(page=page, size=1000)
        if not items:
            break
        for it in items:
            c = it.get("checksum")
            if c and c not in index:
                index[c] = {
                    "id": it.get("id", ""),
                    "originalPath": it.get("originalPath", ""),
                    "originalFileName": it.get("originalFileName", ""),
                }
        if total is not None and page * 1000 >= total:
            break
        if len(items) < 1000:
            break
        page += 1
    return index, algo


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------
def classify_records(records: list[FileRecord], index: dict[str, dict]) -> list[dict]:
    """Classify scanned records against the library index.

    Status per record: placeholder | in_library | duplicate (within folder) | new.
    """
    seen: set[str] = set()
    out: list[dict] = []
    for r in records:
        entry = {
            "path": r.path,
            "name": r.name,
            "stem": r.stem,
            "ext": r.ext,
            "size_bytes": r.size_bytes,
            "mtime": r.mtime,
            "is_placeholder": r.is_placeholder,
            "is_heic": r.ext in LIVE_STILL_EXTS,
            "is_mov": r.ext in LIVE_MOV_EXTS,
            "live_pair": r.live_pair,
            "checksum": r.checksum,
            "status": "new",
            "asset_id": "",
            "library_path": "",
        }
        if r.is_placeholder:
            entry["status"] = "placeholder"
        elif r.checksum and r.checksum in index:
            entry["status"] = "in_library"
            entry["asset_id"] = index[r.checksum].get("id", "")
            entry["library_path"] = index[r.checksum].get("originalPath", "")
        elif r.checksum and r.checksum in seen:
            entry["status"] = "duplicate"
        if r.checksum:
            seen.add(r.checksum)
        out.append(entry)
    return out


def summarize(records: list[dict]) -> dict:
    """Aggregate classification counts plus live-pair statistics."""
    counts = {"total": len(records), "placeholders": 0, "in_library": 0, "new": 0, "duplicates": 0}
    # classify_records uses singular statuses; summary keys are plural
    status_key = {"placeholder": "placeholders", "duplicate": "duplicates"}
    total_bytes = 0
    pair_stems: set[str] = set()
    for r in records:
        status = r.get("status", "new")
        key = status_key.get(status, status)
        if key in counts:
            counts[key] += 1
        else:
            counts["new"] += 1
        total_bytes += r.get("size_bytes", 0)
        live_pair = r.get("live_pair")
        if isinstance(live_pair, str) and live_pair:
            pair_stems.add(live_pair)
    counts["live_pairs"] = len(pair_stems)
    counts["total_size_bytes"] = total_bytes
    return counts


# ---------------------------------------------------------------------------
# Perceptual similarity (dHash - czkawka-compatible semantics)
# ---------------------------------------------------------------------------
def dhash64(path: str) -> str | None:
    """64-bit difference hash of an image as a 16-char hex string.

    HEIC/HEIF decode works when pillow-heif is installed (fleet dependency).
    Returns None for undecodable files.
    """
    try:
        from PIL import Image

        with Image.open(path) as im:
            im = im.convert("L").resize((9, 8))
            px = list(im.tobytes())
    except Exception:
        return None
    bits: list[str] = []
    for row in range(8):
        base = row * 9
        for col in range(8):
            bits.append("1" if px[base + col] > px[base + col + 1] else "0")
    return format(int("".join(bits), 2), "016x")


def hamming_distance(a: str, b: str) -> int:
    """Hamming distance between two hex dHash strings."""
    return (int(a, 16) ^ int(b, 16)).bit_count()


def find_similar(records: list[dict], *, threshold: int = 8, prefix_chars: int = 6, limit: int = 5000) -> list[dict]:
    """Group visually similar images (dHash within hamming ``threshold``).

    Buckets by the leading ``prefix_chars`` hex digits to keep pairwise
    comparisons tractable on large folders. Returns groups with member paths.
    """
    candidates = [r for r in records if not r.get("is_placeholder") and r.get("ext") in IMAGE_EXTS]
    candidates = candidates[:limit]
    hashed: list[tuple[dict, str]] = []
    for r in candidates:
        h = dhash64(r["path"])
        if h:
            hashed.append((r, h))

    buckets: dict[str, list[tuple[dict, str]]] = {}
    for r, h in hashed:
        buckets.setdefault(h[:prefix_chars], []).append((r, h))

    groups: list[list[dict]] = []
    for bucket in buckets.values():
        if len(bucket) > 100:
            # Split oversized buckets further (e.g. burst shots sharing prefix)
            sub: dict[str, list[tuple[dict, str]]] = {}
            for r, h in bucket:
                sub.setdefault(h[: prefix_chars + 2], []).append((r, h))
            buckets_to_scan = list(sub.values())
        else:
            buckets_to_scan = [bucket]
        for b in buckets_to_scan:
            for i in range(len(b)):
                for j in range(i + 1, len(b)):
                    if hamming_distance(b[i][1], b[j][1]) <= threshold:
                        merged = False
                        for g in groups:
                            if b[i][0] in g or b[j][0] in g:
                                if b[i][0] not in g:
                                    g.append(b[i][0])
                                if b[j][0] not in g:
                                    g.append(b[j][0])
                                merged = True
                                break
                        if not merged:
                            groups.append([b[i][0], b[j][0]])
    # Merge overlapping groups transitively
    merged_groups: list[list[dict]] = []
    for g in groups:
        members = {id(r) for r in g}
        for mg in merged_groups:
            if any(id(r) in members for r in mg):
                for r in g:
                    if r not in mg:
                        mg.append(r)
                break
        else:
            merged_groups.append(list(g))
    return [
        {"group": i + 1, "size": len(g), "members": [{"path": r["path"], "name": r["name"]} for r in g]}
        for i, g in enumerate(merged_groups)
    ]


# ---------------------------------------------------------------------------
# Optional czkawka_cli adapter (best-effort external engine)
# ---------------------------------------------------------------------------
def czkawka_available() -> bool:
    """True when a czkawka binary is on PATH."""
    return shutil.which("czkawka_cli") is not None or shutil.which("czkawka") is not None


def run_czkawka_duplicate(folder: str, timeout: int = 600) -> dict:
    """Run ``czkawka_cli duplicate`` on a folder (optional alternate engine).

    Returns raw output; the native comparator is the primary path and does not
    require this binary.
    """
    exe = shutil.which("czkawka_cli") or shutil.which("czkawka")
    if not exe:
        return {"success": False, "error": "czkawka_cli not found on PATH"}
    try:
        proc = subprocess.run(
            [exe, "duplicate", "--directories", folder],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": True,
            "exit_code": proc.returncode,
            "output": (proc.stdout or "")[-4000:],
            "stderr": (proc.stderr or "")[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"czkawka_cli timed out after {timeout}s"}
    except OSError as e:
        return {"success": False, "error": f"czkawka_cli failed: {e}"}


# ---------------------------------------------------------------------------
# Report persistence
# ---------------------------------------------------------------------------
def default_report_path(folder: str) -> str:
    """Return a timestamped report path under data/reconcile/."""
    import re

    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", Path(folder).name or "folder").strip("-") or "folder"
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = Path("data") / "reconcile" / f"{slug}-{ts}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def save_report(records: list[dict], summary: dict, report_path: str | None, folder: str) -> str | None:
    """Persist a reconciliation report; returns the path used or None."""
    if not report_path:
        return None
    payload = {
        "folder": folder,
        "created_at": datetime_utcnow(),
        "summary": summary,
        "records": records,
    }
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return report_path


def datetime_utcnow() -> str:
    """ISO-8601 UTC timestamp string."""
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Shared state + orchestration (used by both the MCP tool and the REST routes)
# ---------------------------------------------------------------------------
LAST_RECORDS: list[dict] = []
LAST_SUMMARY: dict = {}
LAST_FOLDER: str | None = None
LAST_ALGORITHM: str = "sha1"
LAST_REPORT_PATH: str | None = None


def set_last_state(
    records: list[dict],
    summary: dict,
    folder: str,
    algorithm: str,
    report_path: str | None,
) -> None:
    """Persist the latest reconciliation state for follow-up operations."""
    global LAST_RECORDS, LAST_SUMMARY, LAST_FOLDER, LAST_ALGORITHM, LAST_REPORT_PATH
    LAST_RECORDS = records
    LAST_SUMMARY = summary
    LAST_FOLDER = folder
    LAST_ALGORITHM = algorithm
    LAST_REPORT_PATH = report_path


def run_scan(folder: str, *, extensions: set[str] | None = None) -> dict:
    """Scan a folder and classify locally (placeholders / duplicate / new)."""
    records, errors = scan_folder(folder, extensions=extensions)
    items = classify_records(records, {})
    summary = summarize(items)
    set_last_state(items, summary, folder, "sha1", None)
    return {"items": items, "summary": summary, "errors": errors, "algorithm": "sha1"}


async def run_compare(
    client,
    folder: str,
    *,
    extensions: set[str] | None = None,
    report_path: str | None = None,
) -> dict:
    """Full compare pipeline: probe algorithm, scan, index library, classify, persist."""
    algo = await probe_checksum_algorithm(client)
    records, errors = scan_folder(folder, extensions=extensions, algorithm=algo)
    index, algo = await build_checksum_index(client, algorithm=algo)
    items = classify_records(records, index)
    summary = summarize(items)
    path = save_report(items, summary, report_path or default_report_path(folder), folder)
    set_last_state(items, summary, folder, algo, path)
    return {
        "items": items,
        "summary": summary,
        "errors": errors,
        "algorithm": algo,
        "indexed_assets": len(index),
        "report_path": path,
    }


def run_similar(*, threshold: int = 8, limit: int = 5000, folder: str | None = None) -> dict:
    """Perceptual similar-image clustering over the last scan (or a fresh folder scan)."""
    records = LAST_RECORDS
    if not records and folder:
        records, _ = scan_folder(folder)
        records = classify_records(records, {})
    groups = find_similar(records, threshold=threshold, limit=limit)
    LAST_SUMMARY["similar_groups"] = len(groups)
    return {"groups": groups, "group_count": len(groups)}


async def run_import(
    client,
    *,
    album_name: str | None = None,
    force: bool = False,
    statuses: list[str] | None = None,
) -> dict:
    """Import the classified-new records, preserving Live Photo pairs.

    Skips cloud placeholders (hashing/uploading them would hydrate the cloud
    file). Uploads each HEIC+MOV pair as a linked Live Photo: MOV first, then
    the HEIC still with ``livePhotoAssetId`` set.
    """
    records = LAST_RECORDS
    if not records:
        return {
            "success": False,
            "error": "No reconciliation state - run compare first.",
            "imported": 0,
            "duplicates": 0,
            "errors": [],
        }
    statuses = statuses or ["new"]
    targets = [r for r in records if r["status"] in statuses and (force or not r["is_placeholder"])]

    imported = 0
    duplicates = 0
    errors: list[str] = []
    uploaded_ids: list[str] = []
    pair_ids: dict[str, str] = {}

    by_key: dict[str, list[dict]] = {}
    for r in targets:
        by_key.setdefault(r.get("live_pair") or r["path"], []).append(r)

    for unit in by_key.values():
        mov = next((x for x in unit if x.get("is_mov")), None)
        still = next((x for x in unit if not x.get("is_mov")), None)
        files = [mov, still] if mov and still else unit
        for f in files:
            lp_id = pair_ids.get(f["stem"]) if f.get("is_heic") else None
            try:
                res = await client.upload_file(f["path"], live_photo_asset_id=lp_id)
            except Exception as e:
                errors.append(f"{f['name']}: {e}")
                continue
            if res.get("error"):
                errors.append(f"{f['name']}: {res['error']}")
            elif res.get("duplicate"):
                duplicates += 1
            else:
                imported += 1
                if res.get("id"):
                    uploaded_ids.append(res["id"])
                    if f.get("is_mov"):
                        pair_ids[f["stem"]] = res["id"]

    album_result: dict | None = None
    if album_name and uploaded_ids:
        try:
            album_result = await client.create_album(album_name, asset_ids=uploaded_ids)
        except Exception as e:
            errors.append(f"Album creation failed: {e}")

    return {
        "success": True,
        "targeted": len(targets),
        "imported": imported,
        "duplicates": duplicates,
        "uploaded_asset_ids": uploaded_ids,
        "errors": errors,
        "album": album_name,
        "album_result": album_result,
    }
