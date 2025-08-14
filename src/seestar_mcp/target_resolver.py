"""Target resolution utilities for astronomical objects."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
from astropy import units as u
from astropy.coordinates import AltAz, SkyCoord, get_body, get_icrs_coordinates, get_sun
from astropy.time import Time

from .location_manager import LocationManager
from .models import Coordinates, Target, TargetSearchResult

logger = logging.getLogger(__name__)


class TargetResolver:
    """Resolves target names to coordinates using various astronomical catalogs."""

    def __init__(self, location_manager: Optional[LocationManager] = None) -> None:
        """Initialize the target resolver."""
        self.session: Optional[httpx.AsyncClient] = None
        self._cache: Dict[str, Target] = {}
        self.location_manager = location_manager

    async def __aenter__(self) -> "TargetResolver":
        """Async context manager entry."""
        self.session = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(
        self, exc_type: type, exc_val: Exception, exc_tb: object
    ) -> None:
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    async def resolve_target(self, target_name: str) -> TargetSearchResult:
        """
        Resolve a target name to coordinates.

        Args:
            target_name: Name of the astronomical object

        Returns:
            TargetSearchResult with target information or alternatives
        """
        target_name = target_name.strip()
        logger.info(f"Resolving target: {target_name}")

        # Check cache first
        if target_name.lower() in self._cache:
            logger.debug(f"Found {target_name} in cache")
            return TargetSearchResult(
                found=True,
                target=self._cache[target_name.lower()],
                search_query=target_name,
            )

        # Try multiple resolution methods
        try:
            # Method 1: Solar system objects (Sun, Moon, planets)
            target = await self._resolve_solar_system_object(target_name)
            if target:
                # Don't cache solar system objects as their positions change rapidly
                return TargetSearchResult(
                    found=True, target=target, search_query=target_name
                )

        except Exception as e:
            logger.warning(f"Solar system resolution failed for {target_name}: {e}")

        try:
            # Method 2: Astropy name resolution (SIMBAD, NED)
            target = await self._resolve_with_astropy(target_name)
            if target:
                self._cache[target_name.lower()] = target
                return TargetSearchResult(
                    found=True, target=target, search_query=target_name
                )

        except Exception as e:
            logger.warning(f"Astropy resolution failed for {target_name}: {e}")

        try:
            # Method 3: SIMBAD direct query
            target = await self._resolve_with_simbad(target_name)
            if target:
                self._cache[target_name.lower()] = target
                return TargetSearchResult(
                    found=True, target=target, search_query=target_name
                )

        except Exception as e:
            logger.warning(f"SIMBAD resolution failed for {target_name}: {e}")

        # Method 4: Try common name variations
        alternatives = await self._find_alternatives(target_name)

        return TargetSearchResult(
            found=False,
            target=None,
            alternatives=alternatives,
            search_query=target_name,
        )

    async def _resolve_with_astropy(self, target_name: str) -> Optional[Target]:
        """Resolve target using Astropy's coordinate resolution."""
        try:
            # Run in thread to avoid blocking
            coord = await asyncio.get_event_loop().run_in_executor(
                None, lambda: get_icrs_coordinates(target_name)
            )

            if coord:
                ra_hours = coord.ra.hour
                dec_degrees = coord.dec.degree

                return Target(
                    name=target_name,
                    coordinates=Coordinates(
                        ra=ra_hours, dec=dec_degrees, epoch="J2000"
                    ),
                    magnitude=None,
                    object_type=None,
                )
            return None

        except Exception as e:
            logger.debug(f"Astropy resolution failed: {e}")
            return None

    async def _resolve_solar_system_object(self, target_name: str) -> Optional[Target]:
        """Resolve solar system objects (Sun, Moon, planets) using Astropy ephemeris."""
        target_lower = target_name.lower().strip()

        # Define solar system object mappings
        solar_system_objects = {
            "sun": "sun",
            "moon": "moon",
            "mercury": "mercury",
            "venus": "venus",
            "mars": "mars",
            "jupiter": "jupiter",
            "saturn": "saturn",
            "uranus": "uranus",
            "neptune": "neptune",
            "pluto": "pluto",
        }

        if target_lower not in solar_system_objects:
            return None

        try:
            # Get current time for coordinate calculation
            if self.location_manager and self.location_manager.is_configured():
                current_time = self.location_manager.get_local_time()
                astropy_time = self.location_manager.get_astropy_time(current_time)
            else:
                astropy_time = Time.now()

            # Run in thread to avoid blocking
            if target_lower == "sun":
                coord = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: get_sun(astropy_time)
                )
                object_type = "Star"
                magnitude = -26.7  # Apparent magnitude of Sun
            elif target_lower == "moon":
                coord = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: get_body("moon", astropy_time)
                )
                object_type = "Satellite"
                magnitude = -12.9  # Approximate full moon magnitude
            else:
                # For planets, use get_body
                body_name = solar_system_objects[target_lower]
                coord = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: get_body(body_name, astropy_time)
                )
                object_type = "Planet"
                # Approximate magnitudes for planets (varies with distance)
                planet_magnitudes = {
                    "mercury": -1.9,
                    "venus": -4.6,
                    "mars": -2.9,
                    "jupiter": -2.9,
                    "saturn": 0.7,
                    "uranus": 5.7,
                    "neptune": 7.8,
                    "pluto": 15.1,
                }
                magnitude = planet_magnitudes.get(target_lower)

            if coord:
                ra_hours = coord.ra.hour
                dec_degrees = coord.dec.degree

                # Add warning for Sun observations
                warning = ""
                if target_lower == "sun":
                    warning = " ⚠️  SOLAR OBSERVATION: Ensure proper solar filter is installed!"

                return Target(
                    name=f"{target_name.title()}{warning}",
                    coordinates=Coordinates(
                        ra=ra_hours, dec=dec_degrees, epoch="J2000"
                    ),
                    magnitude=magnitude,
                    object_type=object_type,
                )

            return None

        except Exception as e:
            logger.debug(f"Solar system object resolution failed: {e}")
            return None

    async def _resolve_with_simbad(self, target_name: str) -> Optional[Target]:
        """Resolve target using SIMBAD TAP service."""
        if not self.session:
            return None

        try:
            # SIMBAD TAP query
            query = f"""
            SELECT TOP 1
                main_id,
                ra, dec,
                otype_txt as object_type,
                flux as magnitude
            FROM basic
            WHERE main_id = '{target_name}'
               OR oid = '{target_name}'
            """

            params = {"query": query, "format": "json"}

            response = await self.session.get(
                "http://simbad.cds.unistra.fr/simbad/sim-tap/sync", params=params
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    row = data["data"][0]

                    # Convert from degrees to hours for RA
                    ra_hours = row[1] / 15.0  # RA in degrees to hours
                    dec_degrees = row[2]

                    return Target(
                        name=row[0],  # main_id
                        coordinates=Coordinates(
                            ra=ra_hours, dec=dec_degrees, epoch="J2000"
                        ),
                        object_type=row[3] if len(row) > 3 else None,
                        magnitude=row[4] if len(row) > 4 and row[4] else None,
                    )

            return None

        except Exception as e:
            logger.debug(f"SIMBAD query failed: {e}")
            return None

    async def _find_alternatives(self, target_name: str) -> List[str]:
        """Find alternative names or similar targets."""
        alternatives = []

        # Add solar system object suggestions for partial matches
        target_lower = target_name.lower().strip()
        solar_objects = [
            "sun",
            "moon",
            "mercury",
            "venus",
            "mars",
            "jupiter",
            "saturn",
            "uranus",
            "neptune",
            "pluto",
        ]

        for obj in solar_objects:
            if target_lower in obj or obj in target_lower:
                alternatives.append(obj.title())

        # Add Messier alternatives
        if target_name.upper().startswith("M"):
            try:
                num = int(target_name[1:])
                alternatives.append(f"Messier {num}")
                ngc_num = self._messier_to_ngc(num)
                if ngc_num:
                    alternatives.append(f"NGC {ngc_num}")
            except ValueError:
                pass

        # Add NGC alternatives
        if target_name.upper().startswith("NGC"):
            try:
                num = int(target_name[3:].strip())
                messier = self._ngc_to_messier(num)
                if messier:
                    alternatives.append(f"M{messier}")
            except ValueError:
                pass

        # Remove None values and duplicates
        alternatives = [
            alt for alt in alternatives if alt is not None and alt != target_name
        ]
        alternatives = list(set(alternatives))

        return alternatives[:5]  # Limit to 5 alternatives

    def _messier_to_ngc(self, messier_num: int) -> Optional[int]:
        """Convert Messier number to NGC number."""
        # Common Messier to NGC mappings
        messier_ngc_map = {
            1: 1952,  # M1 = NGC 1952 (Crab Nebula)
            31: 224,  # M31 = NGC 224 (Andromeda Galaxy)
            42: 1976,  # M42 = NGC 1976 (Orion Nebula)
            45: 1432,  # M45 = NGC 1432 (Pleiades)
            51: 5194,  # M51 = NGC 5194 (Whirlpool Galaxy)
            57: 6720,  # M57 = NGC 6720 (Ring Nebula)
            81: 3031,  # M81 = NGC 3031 (Bode's Galaxy)
            82: 3034,  # M82 = NGC 3034 (Cigar Galaxy)
            101: 5457,  # M101 = NGC 5457 (Pinwheel Galaxy)
            104: 4594,  # M104 = NGC 4594 (Sombrero Galaxy)
        }
        return messier_ngc_map.get(messier_num)

    def _ngc_to_messier(self, ngc_num: int) -> Optional[int]:
        """Convert NGC number to Messier number."""
        # Reverse lookup
        ngc_messier_map = {
            1952: 1,  # NGC 1952 = M1 (Crab Nebula)
            224: 31,  # NGC 224 = M31 (Andromeda Galaxy)
            1976: 42,  # NGC 1976 = M42 (Orion Nebula)
            1432: 45,  # NGC 1432 = M45 (Pleiades)
            5194: 51,  # NGC 5194 = M51 (Whirlpool Galaxy)
            6720: 57,  # NGC 6720 = M57 (Ring Nebula)
            3031: 81,  # NGC 3031 = M81 (Bode's Galaxy)
            3034: 82,  # NGC 3034 = M82 (Cigar Galaxy)
            5457: 101,  # NGC 5457 = M101 (Pinwheel Galaxy)
            4594: 104,  # NGC 4594 = M104 (Sombrero Galaxy)
        }
        return ngc_messier_map.get(ngc_num)

    def get_cached_targets(self) -> List[str]:
        """Get list of cached target names."""
        return list(self._cache.keys())

    def clear_cache(self) -> None:
        """Clear the target cache."""
        self._cache.clear()
        logger.info("Target cache cleared")

    def check_target_visibility(
        self, coordinates: Coordinates, time: Optional[datetime] = None
    ) -> Tuple[bool, float, str]:
        """
        Check if target is visible from telescope location.

        Args:
            coordinates: Target coordinates
            time: Time to check (default: current local time)

        Returns:
            Tuple of (is_visible, altitude_degrees, status_message)
        """
        if not self.location_manager or not self.location_manager.is_configured():
            # No location configured, assume visible
            logger.warning("No telescope location configured, cannot check visibility")
            return True, 0.0, "Location not configured - visibility unknown"

        try:
            # Get appropriate time
            if time is None:
                time = self.location_manager.get_local_time()
            astropy_time = self.location_manager.get_astropy_time(time)

            # Create SkyCoord object
            target_coord = SkyCoord(
                ra=coordinates.ra * u.hour, dec=coordinates.dec * u.degree, frame="icrs"
            )

            # Transform to local horizontal coordinates
            altaz_frame = AltAz(
                obstime=astropy_time, location=self.location_manager.earth_location
            )
            target_altaz = target_coord.transform_to(altaz_frame)

            altitude = target_altaz.alt.degree
            azimuth = target_altaz.az.degree

            # Consider target visible if altitude > 10 degrees (above horizon + atmospheric effects)
            min_altitude = 10.0
            is_visible = altitude > min_altitude

            if is_visible:
                status = f"Target is visible at {altitude:.1f}° altitude, {azimuth:.1f}° azimuth"
            else:
                status = f"Target is below horizon at {altitude:.1f}° altitude (minimum {min_altitude}°)"

            logger.info(f"Visibility check: {status}")
            return is_visible, altitude, status

        except Exception as e:
            logger.error(f"Error checking target visibility: {e}")
            return True, 0.0, f"Visibility check failed: {e}"


# Utility functions for coordinate conversion
def hours_to_hms(hours: float) -> Tuple[int, int, float]:
    """Convert decimal hours to hours, minutes, seconds."""
    h = int(hours)
    m = int((hours - h) * 60)
    s = ((hours - h) * 60 - m) * 60
    return h, m, s


def degrees_to_dms(degrees: float) -> Tuple[int, int, float]:
    """Convert decimal degrees to degrees, minutes, seconds."""
    sign = 1 if degrees >= 0 else -1
    degrees = abs(degrees)
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = ((degrees - d) * 60 - m) * 60
    return sign * d, m, s


def format_coordinates(coordinates: Coordinates) -> str:
    """Format coordinates as human-readable string."""
    ra_h, ra_m, ra_s = hours_to_hms(coordinates.ra)
    dec_d, dec_m, dec_s = degrees_to_dms(coordinates.dec)

    return (
        f"RA: {ra_h:02d}h {ra_m:02d}m {ra_s:05.2f}s, "
        f"DEC: {dec_d:+03d}° {dec_m:02d}' {dec_s:05.2f}\""
    )
