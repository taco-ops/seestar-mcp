"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock

import pytest

from seestar_mcp.models import (
    CalibrationState,
    CalibrationStatus,
    Coordinates,
    ImagingState,
    ImagingStatus,
    Target,
    TelescopeInfo,
    TelescopeState,
    TelescopeStatus,
)
from seestar_mcp.target_resolver import TargetResolver
from seestar_mcp.telescope_client import SeestarClient


@pytest.fixture
def mock_telescope_info():
    """Mock telescope device information."""
    return TelescopeInfo(
        device_name="SeestarS50",
        firmware_version="1.0.0",
        hardware_version="2.0",
        serial_number="SS50-12345",
        mount_type="alt-az",
    )


@pytest.fixture
def mock_telescope_state():
    """Mock telescope state."""
    return TelescopeState(
        status=TelescopeStatus.IDLE,
        connected=True,
        ra=12.5,
        dec=35.7,
        az=180.0,
        alt=45.0,
        is_tracking=False,
        is_parked=False,
        current_target=None,
    )


@pytest.fixture
def mock_imaging_state():
    """Mock imaging state."""
    return ImagingState(
        status=ImagingStatus.STOPPED,
        progress=0,
        current_image=0,
        total_images=0,
        exposure_time=None,
        time_remaining=None,
        last_image_path=None,
    )


@pytest.fixture
def mock_calibration_state():
    """Mock calibration state."""
    return CalibrationState(
        status=CalibrationStatus.NOT_STARTED,
        progress=0,
        current_step=None,
        steps_completed=0,
        total_steps=0,
        error_message=None,
    )


@pytest.fixture
def mock_target():
    """Mock astronomical target."""
    return Target(
        name="M31",
        coordinates=Coordinates(ra=0.712, dec=41.269, epoch="J2000"),
        magnitude=3.4,
        object_type="galaxy",
    )


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient."""
    client = AsyncMock()

    # Mock successful connection response
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "device_name": "SeestarS50",
        "firmware_version": "1.0.0",
        "hardware_version": "2.0",
        "serial_number": "SS50-12345",
        "mount_type": "alt-az",
    }

    client.request.return_value = response
    client.get.return_value = response
    client.post.return_value = response

    return client


@pytest.fixture
async def mock_telescope_client(
    mock_httpx_client, mock_telescope_info, mock_telescope_state
):
    """Mock SeestarClient."""
    client = SeestarClient("192.168.1.100", 4700, 30.0)
    client.session = mock_httpx_client
    client._connected = True
    client.socket = Mock()  # Mock the socket to make is_connected work
    client._telescope_info = mock_telescope_info

    # Mock methods
    client.connect = AsyncMock(return_value=True)
    client.disconnect = AsyncMock()
    client.get_device_info = AsyncMock(return_value=mock_telescope_info)
    client.get_status = AsyncMock(return_value=mock_telescope_state)
    client.goto_coordinates = AsyncMock(return_value=True)
    client.start_imaging = AsyncMock(return_value=True)
    client.stop_imaging = AsyncMock(return_value=True)
    client.get_imaging_status = AsyncMock(return_value=None)
    client.start_calibration = AsyncMock(return_value=True)
    client.get_calibration_status = AsyncMock(return_value=None)
    client.park_telescope = AsyncMock(return_value=True)
    client.unpark_telescope = AsyncMock(return_value=True)
    client.emergency_stop = AsyncMock(return_value=True)

    return client


@pytest.fixture
async def mock_target_resolver(mock_target):
    """Mock TargetResolver."""
    resolver = TargetResolver()

    # Mock the resolution methods
    async def mock_resolve_target(target_name):
        from seestar_mcp.models import TargetSearchResult

        if target_name.lower() in ["m31", "andromeda galaxy", "andromeda"]:
            return TargetSearchResult(
                found=True, target=mock_target, search_query=target_name
            )
        else:
            return TargetSearchResult(
                found=False,
                alternatives=["M31", "Andromeda Galaxy"],
                search_query=target_name,
            )

    resolver.resolve_target = mock_resolve_target
    return resolver


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_context():
    """Mock FastMCP Context."""
    context = AsyncMock()
    context.info = AsyncMock()
    context.warning = AsyncMock()
    context.error = AsyncMock()
    context.debug = AsyncMock()
    context.report_progress = AsyncMock()
    return context
