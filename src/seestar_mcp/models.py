"""Pydantic models for SeestarS50 MCP server."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TelescopeStatus(str, Enum):
    """Telescope status enumeration."""

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    IDLE = "idle"
    SLEWING = "slewing"
    TRACKING = "tracking"
    IMAGING = "imaging"
    CALIBRATING = "calibrating"
    PARKED = "parked"
    ERROR = "error"


class ImagingStatus(str, Enum):
    """Imaging status enumeration."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class CalibrationStatus(str, Enum):
    """Calibration status enumeration."""

    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Coordinates(BaseModel):
    """Celestial coordinates."""

    ra: float = Field(..., description="Right ascension in hours")
    dec: float = Field(..., description="Declination in degrees")
    epoch: str = Field(default="J2000", description="Coordinate epoch")


class Target(BaseModel):
    """Target object information."""

    name: str = Field(..., description="Target name")
    coordinates: Coordinates = Field(..., description="Target coordinates")
    magnitude: Optional[float] = Field(None, description="Target magnitude")
    object_type: Optional[str] = Field(
        None, description="Object type (galaxy, nebula, etc.)"
    )


class TelescopeInfo(BaseModel):
    """Telescope device information."""

    device_name: str = Field(..., description="Device name")
    firmware_version: str = Field(..., description="Firmware version")
    hardware_version: str = Field(..., description="Hardware version")
    serial_number: str = Field(..., description="Serial number")
    mount_type: str = Field(..., description="Mount type")


class TelescopeState(BaseModel):
    """Current telescope state."""

    status: TelescopeStatus = Field(..., description="Current telescope status")
    connected: bool = Field(..., description="Connection status")
    ra: Optional[float] = Field(None, description="Current RA position in hours")
    dec: Optional[float] = Field(None, description="Current DEC position in degrees")
    az: Optional[float] = Field(None, description="Current azimuth in degrees")
    alt: Optional[float] = Field(None, description="Current altitude in degrees")
    is_tracking: bool = Field(default=False, description="Tracking status")
    is_parked: bool = Field(default=False, description="Park status")
    current_target: Optional[str] = Field(None, description="Current target name")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )


class ImagingParams(BaseModel):
    """Imaging parameters."""

    exposure_time: float = Field(..., gt=0, description="Exposure time in seconds")
    count: int = Field(..., gt=0, description="Number of images to capture")
    gain: Optional[int] = Field(None, ge=0, le=300, description="Gain setting")
    binning: Optional[int] = Field(1, ge=1, le=4, description="Binning factor")
    filter_name: Optional[str] = Field(None, description="Filter name")
    mosaic_mode: bool = Field(False, description="Enable mosaic mode")
    mosaic_width: int = Field(1, ge=1, le=2, description="Mosaic width (1-2)")
    mosaic_height: int = Field(1, ge=1, le=2, description="Mosaic height (1-2)")


class ImagingState(BaseModel):
    """Current imaging state."""

    status: ImagingStatus = Field(..., description="Imaging status")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    current_image: int = Field(default=0, ge=0, description="Current image number")
    total_images: int = Field(default=0, ge=0, description="Total images to capture")
    exposure_time: Optional[float] = Field(None, description="Current exposure time")
    time_remaining: Optional[float] = Field(
        None, description="Estimated time remaining in seconds"
    )
    last_image_path: Optional[str] = Field(
        None, description="Path to last captured image"
    )


class CalibrationState(BaseModel):
    """Current calibration state."""

    status: CalibrationStatus = Field(..., description="Calibration status")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    current_step: Optional[str] = Field(None, description="Current calibration step")
    steps_completed: int = Field(default=0, ge=0, description="Steps completed")
    total_steps: int = Field(default=0, ge=0, description="Total steps")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ConnectionParams(BaseModel):
    """Telescope connection parameters."""

    host: str = Field(..., description="Telescope IP address")
    port: int = Field(default=4700, ge=1, le=65535, description="Telescope port")
    timeout: float = Field(
        default=30.0, gt=0, description="Connection timeout in seconds"
    )


class Response(BaseModel):
    """Generic API response."""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )


class TelescopeResponse(Response):
    """Telescope-specific response with state."""

    telescope_state: Optional[TelescopeState] = Field(
        None, description="Current telescope state"
    )


class ImagingResponse(Response):
    """Imaging-specific response with state."""

    imaging_state: Optional[ImagingState] = Field(
        None, description="Current imaging state"
    )


class CalibrationResponse(Response):
    """Calibration-specific response with state."""

    calibration_state: Optional[CalibrationState] = Field(
        None, description="Current calibration state"
    )


class TargetSearchResult(BaseModel):
    """Target search result."""

    found: bool = Field(..., description="Whether target was found")
    target: Optional[Target] = Field(None, description="Target information if found")
    alternatives: List[str] = Field(
        default_factory=list, description="Alternative target names"
    )
    search_query: str = Field(..., description="Original search query")


class SystemInfo(BaseModel):
    """System information."""

    mcp_server_version: str = Field(..., description="MCP server version")
    telescope_info: Optional[TelescopeInfo] = Field(
        None, description="Telescope information"
    )
    connection_status: bool = Field(..., description="Connection status")
    uptime: float = Field(..., description="Server uptime in seconds")
    last_command: Optional[str] = Field(None, description="Last executed command")
    last_command_time: Optional[datetime] = Field(
        None, description="Last command execution time"
    )
