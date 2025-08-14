"""Tests for Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from seestar_mcp.models import (
    CalibrationState,
    CalibrationStatus,
    ConnectionParams,
    Coordinates,
    ImagingParams,
    ImagingState,
    ImagingStatus,
    Response,
    SystemInfo,
    Target,
    TargetSearchResult,
    TelescopeResponse,
    TelescopeState,
    TelescopeStatus,
)


class TestModels:
    """Test cases for Pydantic models."""

    def test_coordinates_valid(self):
        """Test valid coordinates creation."""
        coords = Coordinates(ra=12.5, dec=35.7, epoch="J2000")

        assert coords.ra == 12.5
        assert coords.dec == 35.7
        assert coords.epoch == "J2000"

    def test_coordinates_default_epoch(self):
        """Test coordinates with default epoch."""
        coords = Coordinates(ra=12.5, dec=35.7)

        assert coords.epoch == "J2000"

    def test_target_valid(self):
        """Test valid target creation."""
        coords = Coordinates(ra=0.712, dec=41.269)
        target = Target(
            name="M31", coordinates=coords, magnitude=3.4, object_type="galaxy"
        )

        assert target.name == "M31"
        assert target.coordinates.ra == 0.712
        assert target.magnitude == 3.4
        assert target.object_type == "galaxy"

    def test_target_minimal(self):
        """Test target with minimal required fields."""
        coords = Coordinates(ra=0.712, dec=41.269)
        target = Target(name="M31", coordinates=coords)

        assert target.name == "M31"
        assert target.magnitude is None
        assert target.object_type is None

    def test_telescope_state_valid(self):
        """Test valid telescope state."""
        state = TelescopeState(
            status=TelescopeStatus.IDLE,
            connected=True,
            ra=12.5,
            dec=35.7,
            is_tracking=False,
            is_parked=False,
        )

        assert state.status == TelescopeStatus.IDLE
        assert state.connected is True
        assert state.ra == 12.5
        assert state.last_updated is not None

    def test_imaging_params_valid(self):
        """Test valid imaging parameters."""
        params = ImagingParams(
            exposure_time=120.0, count=10, gain=100, binning=2, filter_name="Ha"
        )

        assert params.exposure_time == 120.0
        assert params.count == 10
        assert params.gain == 100
        assert params.binning == 2
        assert params.filter_name == "Ha"

    def test_imaging_params_validation(self):
        """Test imaging parameters validation."""
        # Test exposure_time > 0
        with pytest.raises(ValidationError):
            ImagingParams(exposure_time=0, count=10)

        # Test count > 0
        with pytest.raises(ValidationError):
            ImagingParams(exposure_time=120.0, count=0)

        # Test gain range
        with pytest.raises(ValidationError):
            ImagingParams(exposure_time=120.0, count=10, gain=400)

        # Test binning range
        with pytest.raises(ValidationError):
            ImagingParams(exposure_time=120.0, count=10, binning=5)

    def test_imaging_state_valid(self):
        """Test valid imaging state."""
        state = ImagingState(
            status=ImagingStatus.RUNNING,
            progress=50,
            current_image=5,
            total_images=10,
            exposure_time=120.0,
            time_remaining=600.0,
        )

        assert state.status == ImagingStatus.RUNNING
        assert state.progress == 50
        assert state.current_image == 5
        assert state.total_images == 10

    def test_imaging_state_validation(self):
        """Test imaging state validation."""
        # Test progress range
        with pytest.raises(ValidationError):
            ImagingState(status=ImagingStatus.RUNNING, progress=150)  # > 100

        # Test current_image >= 0
        with pytest.raises(ValidationError):
            ImagingState(status=ImagingStatus.RUNNING, current_image=-1)

    def test_calibration_state_valid(self):
        """Test valid calibration state."""
        state = CalibrationState(
            status=CalibrationStatus.RUNNING,
            progress=75,
            current_step="polar_alignment",
            steps_completed=3,
            total_steps=4,
        )

        assert state.status == CalibrationStatus.RUNNING
        assert state.progress == 75
        assert state.current_step == "polar_alignment"
        assert state.steps_completed == 3
        assert state.total_steps == 4

    def test_connection_params_valid(self):
        """Test valid connection parameters."""
        params = ConnectionParams(host="192.168.1.100", port=4700, timeout=30.0)

        assert params.host == "192.168.1.100"
        assert params.port == 4700
        assert params.timeout == 30.0

    def test_connection_params_defaults(self):
        """Test connection parameters with defaults."""
        params = ConnectionParams(host="192.168.1.100")

        assert params.port == 4700
        assert params.timeout == 30.0

    def test_connection_params_validation(self):
        """Test connection parameters validation."""
        # Test port range
        with pytest.raises(ValidationError):
            ConnectionParams(host="192.168.1.100", port=0)

        with pytest.raises(ValidationError):
            ConnectionParams(host="192.168.1.100", port=70000)

        # Test timeout > 0
        with pytest.raises(ValidationError):
            ConnectionParams(host="192.168.1.100", timeout=0)

    def test_response_valid(self):
        """Test valid response."""
        response = Response(
            success=True,
            message="Operation successful",
            data={"key": "value"},
            error=None,
        )

        assert response.success is True
        assert response.message == "Operation successful"
        assert response.data == {"key": "value"}
        assert response.timestamp is not None

    def test_telescope_response_valid(self):
        """Test valid telescope response."""
        state = TelescopeState(status=TelescopeStatus.IDLE, connected=True)

        response = TelescopeResponse(
            success=True, message="Status retrieved", telescope_state=state
        )

        assert response.success is True
        assert response.telescope_state.status == TelescopeStatus.IDLE

    def test_target_search_result_found(self):
        """Test target search result when found."""
        coords = Coordinates(ra=0.712, dec=41.269)
        target = Target(name="M31", coordinates=coords)

        result = TargetSearchResult(found=True, target=target, search_query="M31")

        assert result.found is True
        assert result.target.name == "M31"
        assert result.search_query == "M31"
        assert result.alternatives == []

    def test_target_search_result_not_found(self):
        """Test target search result when not found."""
        result = TargetSearchResult(
            found=False,
            alternatives=["M31", "Andromeda Galaxy"],
            search_query="Unknown Target",
        )

        assert result.found is False
        assert result.target is None
        assert len(result.alternatives) == 2
        assert result.search_query == "Unknown Target"

    def test_system_info_valid(self):
        """Test valid system info."""
        info = SystemInfo(
            mcp_server_version="0.1.0",
            connection_status=True,
            uptime=3600.0,
            last_command="get_status",
            last_command_time=datetime.now(),
        )

        assert info.mcp_server_version == "0.1.0"
        assert info.connection_status is True
        assert info.uptime == 3600.0
        assert info.last_command == "get_status"

    def test_enum_values(self):
        """Test enum value assignments."""
        assert TelescopeStatus.IDLE == "idle"
        assert TelescopeStatus.SLEWING == "slewing"
        assert TelescopeStatus.TRACKING == "tracking"

        assert ImagingStatus.STOPPED == "stopped"
        assert ImagingStatus.RUNNING == "running"
        assert ImagingStatus.COMPLETED == "completed"

        assert CalibrationStatus.NOT_STARTED == "not_started"
        assert CalibrationStatus.RUNNING == "running"
        assert CalibrationStatus.COMPLETED == "completed"
