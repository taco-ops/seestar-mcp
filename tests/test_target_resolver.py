"""Tests for TargetResolver astronomical target resolution."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from seestar_mcp.models import Coordinates, Target, TargetSearchResult
from seestar_mcp.target_resolver import TargetResolver, format_coordinates


class TestTargetResolver:
    """Test cases for TargetResolver."""

    @pytest.mark.asyncio
    async def test_resolve_target_cached(self):
        """Test resolving a cached target."""
        resolver = TargetResolver()

        # Add target to cache
        target = Target(
            name="M31",
            coordinates=Coordinates(ra=0.712, dec=41.269, epoch="J2000"),
            magnitude=3.4,
            object_type="galaxy",
        )
        resolver._cache["m31"] = target

        result = await resolver.resolve_target("M31")

        assert result.found is True
        assert result.target.name == "M31"
        assert result.search_query == "M31"

    @pytest.mark.asyncio
    async def test_resolve_target_not_found(self):
        """Test resolving a target that doesn't exist."""
        resolver = TargetResolver()

        # Mock both resolution methods to fail
        with (
            patch.object(resolver, "_resolve_with_astropy", return_value=None),
            patch.object(resolver, "_resolve_with_simbad", return_value=None),
            patch.object(
                resolver, "_find_alternatives", return_value=["M31", "Andromeda"]
            ),
        ):

            result = await resolver.resolve_target("NonExistentTarget")

            assert result.found is False
            assert result.alternatives == ["M31", "Andromeda"]
            assert result.search_query == "NonExistentTarget"

    @pytest.mark.asyncio
    async def test_resolve_with_astropy_success(self):
        """Test successful Astropy resolution."""
        resolver = TargetResolver()

        # Mock astropy coordinate resolution
        mock_coord = Mock()
        mock_coord.ra.hour = 0.712
        mock_coord.dec.degree = 41.269

        with (
            patch(
                "seestar_mcp.target_resolver.get_icrs_coordinates",
                return_value=mock_coord,
            ),
            patch("asyncio.get_event_loop") as mock_loop,
        ):

            mock_executor = AsyncMock()
            mock_executor.return_value = mock_coord
            mock_loop.return_value.run_in_executor = mock_executor

            target = await resolver._resolve_with_astropy("M31")

            assert target is not None
            assert target.name == "M31"
            assert target.coordinates.ra == 0.712
            assert target.coordinates.dec == 41.269

    @pytest.mark.asyncio
    async def test_resolve_with_astropy_failure(self):
        """Test Astropy resolution failure."""
        resolver = TargetResolver()

        with (
            patch(
                "seestar_mcp.target_resolver.get_icrs_coordinates",
                side_effect=Exception("Not found"),
            ),
            patch("asyncio.get_event_loop") as mock_loop,
        ):

            mock_executor = AsyncMock(side_effect=Exception("Not found"))
            mock_loop.return_value.run_in_executor = mock_executor

            target = await resolver._resolve_with_astropy("NonExistent")

            assert target is None

    @pytest.mark.asyncio
    async def test_resolve_with_simbad_success(self):
        """Test successful SIMBAD resolution."""
        resolver = TargetResolver()

        # Mock httpx client
        mock_session = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [["M31", 10.68, 41.269, "galaxy", 3.4]]  # RA in degrees
        }
        mock_session.get.return_value = mock_response
        resolver.session = mock_session

        target = await resolver._resolve_with_simbad("M31")

        assert target is not None
        assert target.name == "M31"
        assert target.coordinates.ra == pytest.approx(0.712, rel=1e-2)  # 10.68/15
        assert target.coordinates.dec == 41.269
        assert target.object_type == "galaxy"
        assert target.magnitude == 3.4

    @pytest.mark.asyncio
    async def test_resolve_with_simbad_not_found(self):
        """Test SIMBAD resolution when target not found."""
        resolver = TargetResolver()

        # Mock httpx client with empty result
        mock_session = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_session.get.return_value = mock_response
        resolver.session = mock_session

        target = await resolver._resolve_with_simbad("NonExistent")

        assert target is None

    @pytest.mark.asyncio
    async def test_resolve_with_simbad_error(self):
        """Test SIMBAD resolution with HTTP error."""
        resolver = TargetResolver()

        # Mock httpx client with error
        mock_session = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_session.get.return_value = mock_response
        resolver.session = mock_session

        target = await resolver._resolve_with_simbad("M31")

        assert target is None

    @pytest.mark.asyncio
    async def test_find_alternatives_messier(self):
        """Test finding alternatives for Messier objects."""
        resolver = TargetResolver()

        alternatives = await resolver._find_alternatives("M31")

        assert "Messier 31" in alternatives
        assert "NGC 224" in alternatives  # M31 = NGC 224

    @pytest.mark.asyncio
    async def test_find_alternatives_ngc(self):
        """Test finding alternatives for NGC objects."""
        resolver = TargetResolver()

        alternatives = await resolver._find_alternatives("NGC 224")

        assert "M31" in alternatives  # NGC 224 = M31

    @pytest.mark.asyncio
    async def test_find_alternatives_general(self):
        """Test finding alternatives for general objects (should return empty for non-catalog objects)."""
        resolver = TargetResolver()

        # Non-catalog objects should return empty alternatives
        alternatives = await resolver._find_alternatives("test object")
        assert alternatives == []

        # Test Messier alternatives
        alternatives = await resolver._find_alternatives("M31")
        assert any("Messier" in alt for alt in alternatives)

        # Test NGC alternatives
        alternatives = await resolver._find_alternatives("NGC 224")
        assert any("M" in alt for alt in alternatives)

    def test_messier_to_ngc(self):
        """Test Messier to NGC conversion."""
        resolver = TargetResolver()

        assert resolver._messier_to_ngc(31) == 224
        assert resolver._messier_to_ngc(42) == 1976
        assert resolver._messier_to_ngc(999) is None  # Non-existent

    def test_ngc_to_messier(self):
        """Test NGC to Messier conversion."""
        resolver = TargetResolver()

        assert resolver._ngc_to_messier(224) == 31
        assert resolver._ngc_to_messier(1976) == 42
        assert resolver._ngc_to_messier(999999) is None  # Non-existent

    def test_get_cached_targets(self):
        """Test getting cached target names."""
        resolver = TargetResolver()

        # Add some targets to cache
        target1 = Target(name="M31", coordinates=Coordinates(ra=0.712, dec=41.269))
        target2 = Target(name="M42", coordinates=Coordinates(ra=5.588, dec=-5.389))

        resolver._cache["m31"] = target1
        resolver._cache["m42"] = target2

        cached = resolver.get_cached_targets()

        assert "m31" in cached
        assert "m42" in cached
        assert len(cached) == 2

    def test_clear_cache(self):
        """Test clearing the target cache."""
        resolver = TargetResolver()

        # Add target to cache
        target = Target(name="M31", coordinates=Coordinates(ra=0.712, dec=41.269))
        resolver._cache["m31"] = target

        assert len(resolver._cache) == 1

        resolver.clear_cache()

        assert len(resolver._cache) == 0

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test using TargetResolver as async context manager."""
        async with TargetResolver() as resolver:
            assert resolver.session is not None

        # Session should be closed after exiting context

    @pytest.mark.asyncio
    async def test_resolve_solar_system_objects(self):
        """Test resolving solar system objects."""
        resolver = TargetResolver()

        # Mock astropy functions to return expected coordinates
        from astropy import units as u
        from astropy.coordinates import SkyCoord

        mock_sun_coord = SkyCoord(ra=150.0 * u.deg, dec=20.0 * u.deg)
        mock_moon_coord = SkyCoord(ra=180.0 * u.deg, dec=-10.0 * u.deg)

        with patch("seestar_mcp.target_resolver.get_sun", return_value=mock_sun_coord):
            result = await resolver.resolve_target("sun")

            assert result.found is True
            assert result.target is not None
            assert "Sun" in result.target.name
            assert "SOLAR OBSERVATION" in result.target.name
            assert result.target.object_type == "Star"
            assert result.target.magnitude == -26.7
            assert abs(result.target.coordinates.ra - 10.0) < 0.1  # 150°/15 = 10h
            assert abs(result.target.coordinates.dec - 20.0) < 0.1

        with patch(
            "seestar_mcp.target_resolver.get_body", return_value=mock_moon_coord
        ):
            result = await resolver.resolve_target("moon")

            assert result.found is True
            assert result.target is not None
            assert result.target.name == "Moon"
            assert result.target.object_type == "Satellite"
            assert result.target.magnitude == -12.9
            assert abs(result.target.coordinates.ra - 12.0) < 0.1  # 180°/15 = 12h
            assert abs(result.target.coordinates.dec - (-10.0)) < 0.1

    @pytest.mark.asyncio
    async def test_resolve_planets(self):
        """Test resolving planets."""
        resolver = TargetResolver()

        from astropy import units as u
        from astropy.coordinates import SkyCoord

        mock_mars_coord = SkyCoord(ra=30.0 * u.deg, dec=15.0 * u.deg)

        with patch(
            "seestar_mcp.target_resolver.get_body", return_value=mock_mars_coord
        ):
            result = await resolver.resolve_target("mars")

            assert result.found is True
            assert result.target is not None
            assert result.target.name == "Mars"
            assert result.target.object_type == "Planet"
            assert result.target.magnitude == -2.9
            assert abs(result.target.coordinates.ra - 2.0) < 0.1  # 30°/15 = 2h
            assert abs(result.target.coordinates.dec - 15.0) < 0.1

    @pytest.mark.asyncio
    async def test_solar_system_case_insensitive(self):
        """Test that solar system object resolution is case insensitive."""
        resolver = TargetResolver()

        from astropy import units as u
        from astropy.coordinates import SkyCoord

        mock_coord = SkyCoord(ra=45.0 * u.deg, dec=30.0 * u.deg)

        with patch("seestar_mcp.target_resolver.get_body", return_value=mock_coord):
            # Test different cases
            for name in ["jupiter", "JUPITER", "Jupiter", "JuPiTeR"]:
                result = await resolver.resolve_target(name)
                assert result.found is True
                assert result.target.name == "Jupiter"

    @pytest.mark.asyncio
    async def test_solar_system_object_not_cached(self):
        """Test that solar system objects are not cached (positions change)."""
        resolver = TargetResolver()

        from astropy import units as u
        from astropy.coordinates import SkyCoord

        mock_coord = SkyCoord(ra=60.0 * u.deg, dec=45.0 * u.deg)

        with patch("seestar_mcp.target_resolver.get_sun", return_value=mock_coord):
            # Resolve sun twice
            result1 = await resolver.resolve_target("sun")
            result2 = await resolver.resolve_target("sun")

            assert result1.found is True
            assert result2.found is True

            # Check that sun was not added to cache (solar system objects change position)
            cached_targets = resolver.get_cached_targets()
            assert "sun" not in cached_targets

    @pytest.mark.asyncio
    async def test_find_alternatives_solar_system(self):
        """Test that alternatives include solar system objects."""
        resolver = TargetResolver()

        alternatives = await resolver._find_alternatives(
            "su"
        )  # Partial match for "sun"
        assert "Sun" in alternatives

        alternatives = await resolver._find_alternatives(
            "moo"
        )  # Partial match for "moon"
        assert "Moon" in alternatives


class TestCoordinateUtilities:
    """Test coordinate utility functions."""

    def test_format_coordinates(self):
        """Test coordinate formatting."""
        coords = Coordinates(ra=12.5, dec=35.75, epoch="J2000")

        formatted = format_coordinates(coords)

        assert "12h 30m 00.00s" in formatted
        assert "+35° 45' 00.00\"" in formatted

    def test_format_coordinates_negative_dec(self):
        """Test formatting negative declination."""
        coords = Coordinates(ra=0.712, dec=-5.389, epoch="J2000")

        formatted = format_coordinates(coords)

        assert "00h 42m 43.20s" in formatted
        assert "-05° 23' 20.40\"" in formatted
