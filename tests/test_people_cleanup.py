"""People triage: enriched counts, bulk delete, single-photo cleanup.

Mocked unit tests (no live Immich needed). Flat structure, precise mocks.
"""

from unittest.mock import AsyncMock, patch

import pytest

from immich_mcp.config import ImmichConfig
from immich_mcp.immich_api import ImmichAPIClient, ImmichAPIError


@pytest.fixture
def config():
    return ImmichConfig(server_url="http://localhost:2283", api_key="test_api_key_12345", timeout=30)


@pytest.fixture
def api_client(config):
    return ImmichAPIClient(config)


def _person(pid, name="", updated="2026-01-01T00:00:00.000Z", hidden=False):
    return {
        "id": pid,
        "name": name,
        "birthDate": None,
        "isHidden": hidden,
        "thumbnailPath": f"/thumb/{pid}",
        "updatedAt": updated,
    }


class TestPeopleWithCounts:
    @pytest.mark.asyncio
    async def test_enriches_counts_concurrently(self, api_client):
        people = [_person("p1", "Sandra"), _person("p2"), _person("p3", hidden=True)]
        counts = {"p1": [{"id": "a1"}, {"id": "a2"}], "p2": [], "p3": [{"id": "a9"}]}

        async def fake_search_metadata(*, size=10, person_ids=None, **kwargs):
            pid = (person_ids or [""])[0]
            return counts.get(pid, []), None

        with (
            patch.object(api_client, "get_all_people", new_callable=AsyncMock) as mock_people,
            patch.object(api_client, "search_metadata", side_effect=fake_search_metadata),
        ):
            mock_people.return_value = people
            result = await api_client.get_all_people_with_counts()

        by_id = {p["id"]: p for p in result}
        assert by_id["p1"]["asset_count"] == 2
        assert by_id["p1"]["has_more_photos"] is False
        assert by_id["p2"]["asset_count"] == 0
        assert by_id["p3"]["isHidden"] is True
        assert by_id["p3"]["asset_count"] == 1

    @pytest.mark.asyncio
    async def test_count_sample_cap_flags_has_more(self, api_client):
        people = [_person("big", "Prolific")]
        big_list = [{"id": f"a{i}"} for i in range(5)]

        async def fake_search_metadata(*, size=10, person_ids=None, **kwargs):
            return big_list[:size], None

        with (
            patch.object(api_client, "get_all_people", new_callable=AsyncMock) as mock_people,
            patch.object(api_client, "search_metadata", side_effect=fake_search_metadata),
        ):
            mock_people.return_value = people
            result = await api_client.get_all_people_with_counts(count_sample_size=5)

        assert result[0]["asset_count"] == 5
        assert result[0]["has_more_photos"] is True

    @pytest.mark.asyncio
    async def test_count_failure_keeps_person_with_error(self, api_client):
        async def boom(*, size=10, person_ids=None, **kwargs):
            raise RuntimeError("network down")

        with (
            patch.object(api_client, "get_all_people", new_callable=AsyncMock, return_value=[_person("p1")]),
            patch.object(api_client, "search_metadata", side_effect=boom),
        ):
            result = await api_client.get_all_people_with_counts()

        assert result[0]["asset_count"] == 0
        assert "count_error" in result[0]


class TestBulkDelete:
    @pytest.mark.asyncio
    async def test_deletes_many_reports_per_id_errors(self, api_client):
        async def fake_delete(pid):
            if pid == "bad":
                raise RuntimeError("gone")
            return {"success": True}

        with patch.object(api_client, "delete_person", side_effect=fake_delete):
            result = await api_client.bulk_delete_people(["a", "bad", "c"])

        assert result["requested"] == 3
        assert result["deleted_count"] == 2
        assert result["error_count"] == 1
        assert set(result["deleted_ids"]) == {"a", "c"}
        assert any("bad" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_rejects_empty(self, api_client):
        with pytest.raises(ImmichAPIError):
            await api_client.bulk_delete_people([])


class TestCleanupLowPhoto:
    @pytest.mark.asyncio
    async def test_dry_run_reports_without_deleting(self, api_client):
        enriched = [
            {"id": "real", "name": "Sandra", "asset_count": 40, "has_more_photos": True},
            {"id": "crap1", "name": "", "asset_count": 1, "has_more_photos": False},
            {"id": "crap2", "name": "", "asset_count": 0, "has_more_photos": False},
        ]
        with (
            patch.object(
                api_client,
                "get_all_people_with_counts",
                new_callable=AsyncMock,
                return_value=enriched,
            ),
            patch.object(api_client, "bulk_delete_people", new_callable=AsyncMock) as mock_bulk,
        ):
            result = await api_client.cleanup_low_photo_people(threshold=1, dry_run=True)

        assert result["dry_run"] is True
        assert result["candidate_count"] == 2
        assert result["deleted_count"] == 0
        mock_bulk.assert_not_called()

    @pytest.mark.asyncio
    async def test_real_run_deletes_candidates(self, api_client):
        enriched = [
            {"id": "crap1", "name": "", "asset_count": 1, "has_more_photos": False},
        ]
        with (
            patch.object(
                api_client,
                "get_all_people_with_counts",
                new_callable=AsyncMock,
                return_value=enriched,
            ),
            patch.object(
                api_client,
                "bulk_delete_people",
                new_callable=AsyncMock,
                return_value={
                    "requested": 1,
                    "deleted_count": 1,
                    "error_count": 0,
                    "deleted_ids": ["crap1"],
                    "errors": [],
                },
            ) as mock_bulk,
        ):
            result = await api_client.cleanup_low_photo_people(threshold=1, dry_run=False)

        assert result["deleted_count"] == 1
        mock_bulk.assert_awaited_once_with(["crap1"])


class TestServerPeopleTools:
    @pytest.mark.asyncio
    async def test_bulk_delete_requires_confirm(self):
        from immich_mcp import server

        result = await server.bulk_delete_people(["a", "b"], confirm=False)
        assert result["deleted_count"] == 0
        assert any("confirm" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_bulk_delete_caps_at_500(self):
        from immich_mcp import server

        result = await server.bulk_delete_people([f"p{i}" for i in range(501)], confirm=True)
        assert result["deleted_count"] == 0
        assert result["error_count"] == 1

    @pytest.mark.asyncio
    async def test_list_people_sorts_and_filters(self):
        from immich_mcp import server

        enriched = [
            {"id": "b", "name": "Zed", "asset_count": 3, "isHidden": False, "updatedAt": "2026-01-02"},
            {"id": "a", "name": "Amy", "asset_count": 30, "isHidden": False, "updatedAt": "2026-01-01"},
            {"id": "h", "name": "Ghost", "asset_count": 99, "isHidden": True, "updatedAt": "2026-01-03"},
        ]
        with patch("immich_mcp.server.get_api_client", new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value.get_all_people_with_counts = AsyncMock(return_value=enriched)
            by_photos = await server.list_people_with_counts(sort_by="asset_count", order="desc")
            assert [p["id"] for p in by_photos] == ["a", "b"]  # hidden excluded
            by_name = await server.list_people_with_counts(sort_by="name", order="asc")
            assert [p["id"] for p in by_name] == ["a", "b"]
            filtered = await server.list_people_with_counts(sort_by="name", order="asc", name_filter="am")
            assert [p["id"] for p in filtered] == ["a"]
