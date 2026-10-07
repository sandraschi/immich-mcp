"""Tests for the library reconciliation engine (reconcile.py)."""

import base64
import hashlib
from pathlib import Path
from unittest.mock import AsyncMock

from PIL import Image

from immich_mcp import reconcile as rc


def _write(path: Path, data: bytes = b"fake-image-bytes") -> Path:
    path.write_bytes(data)
    return path


def _gradient(path: Path, direction: str) -> Path:
    im = Image.new("RGB", (32, 32))
    px = im.load()
    for x in range(32):
        v = x * 8 if direction == "up" else 255 - x * 8
        for y in range(32):
            px[x, y] = (v, v, v)
    im.save(path)
    return path


class TestHashAndPlaceholder:
    def test_hash_file_matches_immich_format(self, tmp_path):
        p = _write(tmp_path / "a.jpg")
        expected = base64.b64encode(hashlib.sha1(b"fake-image-bytes").digest()).decode()
        assert rc.hash_file(str(p)) == expected

    def test_hash_file_sha256(self, tmp_path):
        p = _write(tmp_path / "a.jpg")
        assert rc.digest_length(rc.hash_file(str(p), "sha256")) == 32

    def test_placeholder_detected_via_win_attributes(self, tmp_path, monkeypatch):
        p = _write(tmp_path / "stub.heic")
        monkeypatch.setattr(rc, "_win_file_attributes", lambda _path: 0x1000)  # OFFLINE
        assert rc.is_cloud_placeholder(str(p)) is True

    def test_regular_file_not_placeholder(self, tmp_path, monkeypatch):
        p = _write(tmp_path / "real.heic")
        monkeypatch.setattr(rc, "_win_file_attributes", lambda _path: 0x20)  # ARCHIVE
        assert rc.is_cloud_placeholder(str(p)) is False


class TestScanFolder:
    def test_scans_media_and_skips_non_media(self, tmp_path):
        _write(tmp_path / "IMG_1.HEIC")
        _write(tmp_path / "IMG_1.MOV")
        _write(tmp_path / "notes.txt")
        records, errors = rc.scan_folder(str(tmp_path))
        assert not errors
        assert len(records) == 2
        assert all(r.checksum for r in records)

    def test_live_photo_pairing(self, tmp_path):
        _write(tmp_path / "IMG_1.HEIC")
        _write(tmp_path / "IMG_1.MOV")
        _write(tmp_path / "IMG_2.HEIC")
        records, _ = rc.scan_folder(str(tmp_path))
        by_name = {r.name: r for r in records}
        assert by_name["IMG_1.HEIC"].live_pair == "IMG_1"
        assert by_name["IMG_1.MOV"].live_pair == "IMG_1"
        assert by_name["IMG_2.HEIC"].live_pair is None
        summary = rc.summarize(rc.classify_records(records, {}))
        assert summary["live_pairs"] == 1

    def test_placeholder_never_hashed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(rc, "_win_file_attributes", lambda _path: 0x1000)
        _write(tmp_path / "stub.heic")
        records, _ = rc.scan_folder(str(tmp_path))
        assert len(records) == 1
        assert records[0].is_placeholder is True
        assert records[0].checksum is None

    def test_max_depth(self, tmp_path):
        nested = tmp_path / "sub"
        nested.mkdir()
        _write(tmp_path / "top.jpg")
        _write(nested / "deep.jpg")
        records, _ = rc.scan_folder(str(tmp_path), max_depth=0)
        assert len(records) == 1

    def test_missing_folder(self, tmp_path):
        records, errors = rc.scan_folder(str(tmp_path / "nope"))
        assert records == []
        assert errors


class TestClassification:
    def test_classify_local_duplicates(self, tmp_path):
        _write(tmp_path / "new.jpg")
        _write(tmp_path / "dup1.jpg", b"same")
        _write(tmp_path / "dup2.jpg", b"same")
        records, _ = rc.scan_folder(str(tmp_path))
        items = rc.classify_records(records, {})
        assert {i["status"] for i in items} == {"new", "duplicate"}
        summary = rc.summarize(items)
        assert summary["duplicates"] == 1
        assert summary["new"] == 2

    def test_in_library_match(self, tmp_path):
        p = _write(tmp_path / "known.jpg")
        checksum = rc.hash_file(str(p))
        records, _ = rc.scan_folder(str(tmp_path))
        items = rc.classify_records(
            records, {checksum: {"id": "abc", "originalPath": "E:/x.jpg", "originalFileName": "x.jpg"}}
        )
        assert items[0]["status"] == "in_library"
        assert items[0]["asset_id"] == "abc"
        assert items[0]["library_path"] == "E:/x.jpg"


class TestDhash:
    def test_identical_images_same_hash(self, tmp_path):
        p1 = _gradient(tmp_path / "a.png", "up")
        p2 = _gradient(tmp_path / "b.png", "up")
        assert rc.dhash64(str(p1)) == rc.dhash64(str(p2))
        assert rc.hamming_distance(rc.dhash64(str(p1)), rc.dhash64(str(p2))) == 0

    def test_different_images_differ(self, tmp_path):
        p1 = _gradient(tmp_path / "a.png", "up")
        p2 = _gradient(tmp_path / "b.png", "down")
        assert rc.hamming_distance(rc.dhash64(str(p1)), rc.dhash64(str(p2))) > 10

    def test_find_similar_groups_near_duplicates(self, tmp_path):
        p1 = tmp_path / "a.png"
        p2 = tmp_path / "b.png"
        im = Image.new("RGB", (32, 32))
        px = im.load()
        for x in range(32):
            for y in range(32):
                px[x, y] = (x * 8, 40, 200)
        im.save(p1)
        px2 = im.load()
        for x in range(32):
            for y in range(32):
                px2[x, y] = (x * 8 + 1, 40, 200)  # nearly identical
        im.save(p2)
        records = [
            {"path": str(p1), "name": "a.png", "ext": ".png", "is_placeholder": False},
            {"path": str(p2), "name": "b.png", "ext": ".png", "is_placeholder": False},
        ]
        groups = rc.find_similar(records, threshold=8)
        assert len(groups) == 1
        assert groups[0]["size"] == 2


class TestLibraryIndex:
    async def test_probe_sha1(self):
        client = AsyncMock()
        csum = base64.b64encode(hashlib.sha1(b"x").digest()).decode()
        client.search_metadata = AsyncMock(return_value=([{"checksum": csum}], 1))
        assert await rc.probe_checksum_algorithm(client) == "sha1"

    async def test_probe_sha256(self):
        client = AsyncMock()
        csum = base64.b64encode(hashlib.sha256(b"x").digest()).decode()
        client.search_metadata = AsyncMock(return_value=([{"checksum": csum}], 1))
        assert await rc.probe_checksum_algorithm(client) == "sha256"

    async def test_build_index_pages_until_empty(self):
        client = AsyncMock()
        assets = [
            {"id": f"id{i}", "checksum": f"c{i}", "originalPath": f"/p/{i}", "originalFileName": f"{i}.jpg"}
            for i in range(2)
        ]
        client.search_metadata = AsyncMock(side_effect=[(assets, 2), ([], None)])
        index, algo = await rc.build_checksum_index(client, algorithm="sha1")
        assert len(index) == 2
        assert index["c0"]["id"] == "id0"
        assert algo == "sha1"


class TestOrchestration:
    async def test_run_compare_classifies_against_library(self, tmp_path):
        p = _write(tmp_path / "new.jpg")
        checksum = rc.hash_file(str(p))
        known = {"id": "known-1", "checksum": checksum, "originalPath": "E:/x.jpg", "originalFileName": "x.jpg"}
        client = AsyncMock()
        client.search_metadata = AsyncMock(side_effect=[([known], 1), ([known], 1), ([], None)])
        report = tmp_path / "report.json"
        result = await rc.run_compare(client, str(tmp_path), report_path=str(report))
        assert result["algorithm"] == "sha1"
        assert result["items"][0]["status"] == "in_library"
        assert result["summary"]["new"] == 0
        assert report.exists()

    async def test_run_import_pairs_live_photo(self, tmp_path):
        _write(tmp_path / "IMG_1.HEIC")
        _write(tmp_path / "IMG_1.MOV", b"fake-video-bytes")
        records, _ = rc.scan_folder(str(tmp_path))
        items = rc.classify_records(records, {})
        rc.set_last_state(items, rc.summarize(items), str(tmp_path), "sha1", None)

        client = AsyncMock()
        calls: list[tuple[str, str | None]] = []

        async def fake_upload(path, live_photo_asset_id=None, duration=None):
            calls.append((path, live_photo_asset_id))
            if path.endswith(".MOV"):
                return {"id": "mov-1"}
            return {"id": "heic-1"}

        client.upload_file = fake_upload
        client.create_album = AsyncMock(return_value={})
        result = await rc.run_import(client, album_name="Test Album")
        assert result["imported"] == 2
        assert calls[0][0].endswith(".MOV") and calls[0][1] is None
        assert calls[1][0].endswith(".HEIC") and calls[1][1] == "mov-1"
        client.create_album.assert_awaited_once_with("Test Album", asset_ids=["mov-1", "heic-1"])

    async def test_run_import_skips_placeholders(self, tmp_path, monkeypatch):
        monkeypatch.setattr(rc, "_win_file_attributes", lambda _path: 0x1000)
        _write(tmp_path / "stub.heic")
        records, _ = rc.scan_folder(str(tmp_path))
        items = rc.classify_records(records, {})
        rc.set_last_state(items, rc.summarize(items), str(tmp_path), "sha1", None)

        client = AsyncMock()
        calls: list[str] = []

        async def fake_upload(path, live_photo_asset_id=None, duration=None):
            calls.append(path)
            return {"id": "x"}

        client.upload_file = fake_upload
        result = await rc.run_import(client)
        assert result["targeted"] == 0
        assert calls == []

    async def test_run_import_requires_state(self):
        rc.set_last_state([], {}, "x", "sha1", None)
        client = AsyncMock()
        result = await rc.run_import(client)
        assert result["success"] is False
