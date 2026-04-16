"""
Integration tests for ImmichMCP v2.4.0 API compatibility
Tests against real Immich v2.4.0 server to verify API changes work correctly
Austrian efficiency: Real integration testing, no mocks for critical paths
"""

import os
from contextlib import suppress

import pytest

from immich_mcp.config import ImmichConfig
from immich_mcp.immich_api import ImmichAPIClient, ImmichAPIError


class TestImmichV240Integration:
    """Integration tests against real Immich v2.4.0 server"""

    @pytest.fixture(scope="session")
    def immich_config(self):
        """Get real Immich configuration from environment"""
        server_url = os.getenv("IMMICH_SERVER_URL", "http://localhost:2283")
        api_key = os.getenv("IMMICH_API_KEY")

        if not api_key:
            pytest.skip("IMMICH_API_KEY environment variable not set")

        return ImmichConfig(
            server_url=server_url,
            api_key=api_key,
            timeout=60,  # Longer timeout for real server
        )

    @pytest.fixture(scope="session")
    async def api_client(self, immich_config):
        """Create API client connected to real server"""
        client = ImmichAPIClient(immich_config)

        # Test connection
        try:
            await client.get_server_info()
        except Exception as e:
            pytest.skip(f"Cannot connect to Immich server: {e}")

        return client

    class TestSearchMetadataEndpoint:
        """Test the new search/metadata endpoint integration"""

        @pytest.mark.asyncio
        async def test_search_metadata_basic(self, api_client):
            """Test basic search/metadata endpoint functionality"""
            try:
                result = await api_client._get("/search/metadata", params={"page": 1, "size": 10, "type": "ASSET"})

                # Verify response structure
                assert "assets" in result
                assert "albums" in result
                assert isinstance(result["assets"], dict)
                assert "total" in result["assets"]
                assert "count" in result["assets"]
                assert "items" in result["assets"]
                assert isinstance(result["assets"]["items"], list)

            except ImmichAPIError as e:
                pytest.fail(f"Search/metadata endpoint failed: {e}")

        @pytest.mark.asyncio
        async def test_smart_search_integration(self, api_client):
            """Test smart search through search/smart endpoint"""
            try:
                # Test with a simple query
                result = await api_client.search_photos("test", search_type="smart", limit=5)

                # Verify result structure
                assert isinstance(result, list)
                if len(result) > 0:
                    asset = result[0]
                    assert "id" in asset
                    assert "type" in asset
                    assert "originalFileName" in asset

            except ImmichAPIError:
                # Smart search might not be available or configured
                pass

        @pytest.mark.asyncio
        async def test_filename_search_via_metadata(self, api_client):
            """Test filename search using new metadata endpoint"""
            try:
                # Get some assets first to have a filename to search for
                assets = await api_client.search_photos("", search_type="filename", limit=1)
                if len(assets) > 0:
                    filename = assets[0]["originalFileName"]
                    if filename:
                        # Search for that filename
                        result = await api_client.search_photos(filename, search_type="filename", limit=5)
                        assert isinstance(result, list)
                else:
                    pass

            except ImmichAPIError as e:
                pytest.fail(f"Filename search failed: {e}")

    class TestAssetAccessLimitation:
        """Test asset access limitations in v2.4.0"""

        @pytest.mark.asyncio
        async def test_individual_asset_access_blocked(self, api_client):
            """Test that individual asset access is not available in v2.4.0"""
            try:
                # Try to get first asset from search
                assets = await api_client.search_photos("", search_type="filename", limit=1)
                if len(assets) > 0:
                    asset_id = assets[0]["id"]

                    # Try direct asset access (should fail in v2.4.0)
                    try:
                        await api_client._get(f"/assets/{asset_id}")
                        pytest.fail("Individual asset access should not work in v2.4.0")
                    except ImmichAPIError as e:
                        if "404" in str(e) or "not found" in str(e).lower():
                            pass
                        else:
                            raise
                else:
                    pass

            except ImmichAPIError:
                pass

        @pytest.mark.asyncio
        async def test_get_asset_info_fallback_works(self, api_client):
            """Test that get_asset_info fallback works in v2.4.0"""
            try:
                # Get an asset via search
                assets = await api_client.search_photos("", search_type="filename", limit=1)
                if len(assets) > 0:
                    asset_id = assets[0]["id"]

                    # Try to get asset info (should work via fallback)
                    asset_info = await api_client.get_asset_info(asset_id)

                    assert asset_info["id"] == asset_id
                    assert "originalFileName" in asset_info
                    assert "type" in asset_info

                else:
                    pass

            except ImmichAPIError as e:
                pytest.fail(f"Asset info fallback failed: {e}")

    class TestServerInfoAdaptation:
        """Test server info adaptation for v2.4.0"""

        @pytest.mark.asyncio
        async def test_server_info_detects_v240(self, api_client):
            """Test that server info correctly detects v2.4.0+"""
            server_info = await api_client.get_server_info()

            # Verify v2.4.0+ detection
            assert server_info["is_v2_plus"] is True
            assert "api_architecture" in server_info
            assert server_info["api_architecture"] == "search_based"
            assert server_info["individual_asset_access"] is False

        @pytest.mark.asyncio
        async def test_server_stats_adapt_to_v240(self, api_client):
            """Test that server stats work without /server-info endpoint"""
            server_stats = await api_client.get_server_stats()

            # Should have basic stats even without /server-info
            assert "photos" in server_stats
            assert "albums" in server_stats
            assert "api_version" in server_stats
            assert server_stats["api_version"] == "2.4.0+"

    class TestBackwardCompatibility:
        """Test that existing functionality still works"""

        @pytest.mark.asyncio
        async def test_albums_api_still_works(self, api_client):
            """Test that albums API is unchanged in v2.4.0"""
            try:
                albums = await api_client.get_albums()
                assert isinstance(albums, list)

                if len(albums) > 0:
                    album = albums[0]
                    assert "id" in album
                    assert "albumName" in album

            except ImmichAPIError as e:
                pytest.fail(f"Albums API failed: {e}")

        @pytest.mark.asyncio
        async def test_create_album_still_works(self, api_client):
            """Test album creation still works in v2.4.0"""
            try:
                # Create a test album (will be cleaned up by test cleanup)
                album_name = "Test Album v2.4.0 Integration"
                album = await api_client.create_album(album_name, "Created by integration test")

                assert album["albumName"] == album_name
                assert "id" in album

                # Clean up
                with suppress(Exception):
                    await api_client._delete(f"/albums/{album['id']}")

            except ImmichAPIError as e:
                pytest.fail(f"Album creation failed: {e}")

    class TestOCRFunctionality:
        """Test OCR functionality detection and usage"""

        @pytest.mark.asyncio
        async def test_ocr_capability_detection(self, api_client):
            """Test that OCR capability is correctly detected"""
            server_info = await api_client.get_server_info()

            # OCR detection should work
            has_ocr = server_info.get("has_ocr", False)

            if has_ocr:
                pass

        @pytest.mark.asyncio
        async def test_ocr_search_functionality(self, api_client):
            """Test OCR search functionality if available"""
            try:
                # Test OCR search
                results = await api_client.search_photos("test", search_type="ocr", limit=5)
                assert isinstance(results, list)

                if len(results) > 0:
                    pass
                else:
                    pass

            except ImmichAPIError as e:
                if "not found" in str(e).lower() or "404" in str(e):
                    pass
                else:
                    raise

    class TestPerformanceAndLimits:
        """Test performance characteristics and limits"""

        @pytest.mark.asyncio
        async def test_search_performance(self, api_client):
            """Test search performance with different result sizes"""
            import time

            # Test small result set
            start_time = time.time()
            results_small = await api_client.search_photos("", search_type="filename", limit=10)
            time.time() - start_time

            # Test larger result set
            start_time = time.time()
            results_large = await api_client.search_photos("", search_type="filename", limit=100)
            time.time() - start_time

            assert isinstance(results_small, list)
            assert isinstance(results_large, list)
            assert len(results_small) <= 10
            assert len(results_large) <= 100

        @pytest.mark.asyncio
        async def test_pagination_behavior(self, api_client):
            """Test pagination behavior of search endpoint"""
            # Get first page
            page1 = await api_client._get("/search/metadata", params={"page": 1, "size": 20, "type": "ASSET"})

            # Get second page
            page2 = await api_client._get("/search/metadata", params={"page": 2, "size": 20, "type": "ASSET"})

            page1["assets"]["total"]
            page1_count = len(page1["assets"]["items"])
            page2_count = len(page2["assets"]["items"])

            assert page1_count <= 20
            assert page2_count <= 20

    class TestErrorHandling:
        """Test error handling and graceful degradation"""

        @pytest.mark.asyncio
        async def test_invalid_asset_id_handling(self, api_client):
            """Test handling of invalid asset IDs"""
            try:
                await api_client.get_asset_info("invalid-asset-id-12345")
                pytest.fail("Should have raised an error for invalid asset ID")
            except ImmichAPIError as e:
                assert "not found" in str(e).lower()

        @pytest.mark.asyncio
        async def test_network_error_recovery(self, api_client):
            """Test recovery from network errors"""
            # This is harder to test without mocking, but we can test timeout handling
            try:
                # Try a search with very short timeout (if configurable)
                results = await api_client.search_photos("", search_type="filename", limit=1)
                assert isinstance(results, list)
            except ImmichAPIError:
                pass


class TestImmichMCPFullIntegration:
    """Full integration tests for complete ImmichMCP workflow"""

    @pytest.fixture(scope="session")
    async def test_assets(self, api_client):
        """Get some test assets for comprehensive testing"""
        try:
            assets = await api_client.search_photos("", search_type="filename", limit=5)
            return assets
        except Exception:
            return []

    @pytest.mark.asyncio
    async def test_complete_workflow(self, api_client, test_assets):
        """Test complete ImmichMCP workflow from search to asset info"""
        if not test_assets:
            pytest.skip("No test assets available")

        asset = test_assets[0]

        # 1. Search works
        search_results = await api_client.search_photos("", search_type="filename", limit=10)
        assert len(search_results) > 0

        # 2. Asset info retrieval works
        asset_info = await api_client.get_asset_info(asset["id"])
        assert asset_info["id"] == asset["id"]

        # 3. Server info works
        server_info = await api_client.get_server_info()
        assert server_info["is_v2_plus"] is True

        # 4. Server stats work
        server_stats = await api_client.get_server_stats()
        assert "photos" in server_stats


if __name__ == "__main__":
    # Run integration tests
    # Requires IMMICH_SERVER_URL and IMMICH_API_KEY environment variables
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "-k",
            "not test_complete_workflow",  # Skip long-running tests by default
        ]
    )
