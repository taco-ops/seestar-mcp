"""Location and timezone management for SeestarS50 telescope."""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

import pytz
from astropy.coordinates import EarthLocation
from astropy.time import Time

logger = logging.getLogger(__name__)


class LocationManager:
    """Manages telescope location and timezone information."""

    def __init__(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        elevation: Optional[float] = None,
        timezone_name: Optional[str] = None,
    ) -> None:
        """
        Initialize location manager.

        Args:
            latitude: Telescope latitude in degrees (positive = North)
            longitude: Telescope longitude in degrees (positive = East)
            elevation: Telescope elevation in meters above sea level
            timezone_name: IANA timezone name (e.g., 'America/New_York')
        """
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation or 0.0
        self.timezone_name = timezone_name

        # Set up timezone
        if timezone_name:
            try:
                self.timezone = pytz.timezone(timezone_name)
            except pytz.UnknownTimeZoneError:
                logger.warning(f"Unknown timezone '{timezone_name}', using UTC")
                self.timezone = pytz.UTC
        else:
            # Try to guess timezone from coordinates
            self.timezone = (
                self._guess_timezone() if latitude and longitude else pytz.UTC
            )

        # Set up EarthLocation for astropy calculations
        self.earth_location = None
        if latitude is not None and longitude is not None:
            self.earth_location = EarthLocation(
                lat=latitude, lon=longitude, height=self.elevation
            )
            logger.info(
                f"Telescope location set to: {latitude:.4f}°, {longitude:.4f}°, {self.elevation}m"
            )
            logger.info(f"Timezone: {self.timezone}")

    def _guess_timezone(self) -> pytz.BaseTzInfo:
        """Guess timezone from coordinates."""
        if not self.latitude or not self.longitude:
            return pytz.UTC

        # Simple timezone guessing based on longitude
        # This is a rough approximation - real apps should use more sophisticated methods
        offset_hours = int(round(self.longitude / 15.0))

        # Clamp to valid range
        offset_hours = max(-12, min(12, offset_hours))

        try:
            # Try to find a common timezone at this offset
            if offset_hours == -8:
                return pytz.timezone("America/Los_Angeles")
            elif offset_hours == -7:
                return pytz.timezone("America/Denver")
            elif offset_hours == -6:
                return pytz.timezone("America/Chicago")
            elif offset_hours == -5:
                return pytz.timezone("America/New_York")
            elif offset_hours == 0:
                return pytz.timezone("Europe/London")
            elif offset_hours == 1:
                return pytz.timezone("Europe/Paris")
            elif offset_hours == 8:
                return pytz.timezone("Asia/Shanghai")
            elif offset_hours == 9:
                return pytz.timezone("Asia/Tokyo")
            else:
                # Fallback to a fixed offset
                return pytz.FixedOffset(offset_hours * 60)
        except pytz.UnknownTimeZoneError:
            return pytz.FixedOffset(offset_hours * 60)

    def get_local_time(self, utc_time: Optional[datetime] = None) -> datetime:
        """
        Convert UTC time to local telescope time.

        Args:
            utc_time: UTC time (default: current time)

        Returns:
            Local time at telescope location
        """
        if utc_time is None:
            utc_time = datetime.now(timezone.utc)
        elif utc_time.tzinfo is None:
            utc_time = utc_time.replace(tzinfo=timezone.utc)

        return utc_time.astimezone(self.timezone)

    def get_astropy_time(self, local_time: Optional[datetime] = None) -> Time:
        """
        Get astropy Time object for calculations.

        Args:
            local_time: Local time (default: current local time)

        Returns:
            Astropy Time object
        """
        if local_time is None:
            local_time = self.get_local_time()
        elif local_time.tzinfo is None:
            # Assume local timezone if no timezone info
            local_time = self.timezone.localize(local_time)

        return Time(local_time)

    def is_configured(self) -> bool:
        """Check if location is properly configured."""
        return (
            self.latitude is not None
            and self.longitude is not None
            and self.earth_location is not None
        )

    def get_location_info(self) -> dict:
        """Get location information as dictionary."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation": self.elevation,
            "timezone": str(self.timezone),
            "configured": self.is_configured(),
        }

    @classmethod
    def from_config(cls, config: dict) -> "LocationManager":
        """Create LocationManager from configuration dictionary."""
        return cls(
            latitude=config.get("latitude"),
            longitude=config.get("longitude"),
            elevation=config.get("elevation"),
            timezone_name=config.get("timezone"),
        )
