"""Tests for MCP server tools and functi            # Get the disconnect_telescope tool
tools = await server._list_tools()
disconnect_tool = next(
    tool for tool in tools if tool.name == "disconnect_telescope"
)ty."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from seestar_mcp.models import (
    CalibrationStatus,
    Coordinates,
    ImagingStatus,
    Target,
    TelescopeStatus,
)
from seestar_mcp.server import create_server


class TestMCPServer:
    """Test cases for MCP server tools."""

    def test_create_server(self):
        """Test server creation."""
        server = create_server()

        assert server is not None
        assert server.name == "seestar-mcp"

    @pytest.mark.asyncio
    async def test_connect_telescope_success(self, mock_telescope_client, mock_context):
        """Test successful telescope connection."""
        server = create_server()

        # Mock global telescope client
        with (
            patch("seestar_mcp.server._telescope_client", None),
            patch(
                "seestar_mcp.server.SeestarClient", return_value=mock_telescope_client
            ),
        ):

            # Get the connect_telescope tool
            tools = await server._list_tools()
            connect_tool = next(
                tool for tool in tools if tool.name == "connect_telescope"
            )

            # Call the tool
            result = await connect_tool.fn(
                host="192.168.1.100", port=4700, timeout=30.0, ctx=mock_context
            )

            assert result.success is True
            assert "Successfully connected" in result.message
            mock_telescope_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_telescope_failure(self, mock_context):
        """Test telescope connection failure."""
        server = create_server()

        # Mock failed connection
        mock_client = AsyncMock()
        mock_client.connect.return_value = False

        with (
            patch("seestar_mcp.server._telescope_client", None),
            patch("seestar_mcp.server.SeestarClient", return_value=mock_client),
        ):

            tools = await server._list_tools()
            connect_tool = next(
                tool for tool in tools if tool.name == "connect_telescope"
            )

            # Should raise ToolError
            with pytest.raises(Exception):  # ToolError
                await connect_tool.fn(
                    host="192.168.1.999", port=4700, timeout=30.0, ctx=mock_context
                )

    @pytest.mark.asyncio
    async def test_disconnect_telescope(self, mock_telescope_client, mock_context):
        """Test telescope disconnection."""
        server = create_server()

        with patch("seestar_mcp.server._telescope_client", mock_telescope_client):

            tools = await server._list_tools()
            disconnect_tool = next(
                tool for tool in tools if tool.name == "disconnect_telescope"
            )

            result = await disconnect_tool.fn(ctx=mock_context)

            assert result.success is True
            assert "Disconnected" in result.message
            mock_telescope_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_telescope_status(
        self, mock_telescope_client, mock_telescope_state, mock_context
    ):
        """Test getting telescope status."""
        server = create_server()

        mock_telescope_client.get_status.return_value = mock_telescope_state

        with patch("seestar_mcp.server._telescope_client", mock_telescope_client):

            tools = await server._list_tools()
            status_tool = next(
                tool for tool in tools if tool.name == "get_telescope_status"
            )

            result = await status_tool.fn(ctx=mock_context)

            assert result.success is True
            assert result.telescope_state is not None
            assert result.telescope_state.status == TelescopeStatus.IDLE

    @pytest.mark.asyncio
    async def test_get_telescope_status_not_connected(self, mock_context):
        """Test getting status when not connected."""
        server = create_server()

        with patch("seestar_mcp.server._telescope_client", None):

            tools = await server._list_tools()
            status_tool = next(
                tool for tool in tools if tool.name == "get_telescope_status"
            )

            with pytest.raises(Exception):  # ToolError
                await status_tool.fn(ctx=mock_context)

    @pytest.mark.asyncio
    async def test_goto_target_success(
        self,
        mock_telescope_client,
        mock_target_resolver,
        mock_target,
        mock_telescope_state,
        mock_context,
    ):
        """Test successful goto target."""
        server = create_server()

        mock_telescope_client.goto_coordinates.return_value = True
        mock_telescope_client.get_status.return_value = mock_telescope_state

        with (
            patch("seestar_mcp.server._telescope_client", mock_telescope_client),
            patch("seestar_mcp.server._target_resolver", mock_target_resolver),
        ):

            tools = await server._list_tools()
            goto_tool = next(tool for tool in tools if tool.name == "goto_target")

            result = await goto_tool.fn(target_name="M31", ctx=mock_context)

            assert result.success is True
            assert "Slewing to" in result.message
            assert result.data["target"]["name"] == "M31"
            mock_telescope_client.goto_coordinates.assert_called_once()

    @pytest.mark.asyncio
    async def test_goto_target_not_found(self, mock_telescope_client, mock_context):
        """Test goto target when target not found."""
        server = create_server()

        # Mock target resolver that doesn't find target
        mock_resolver = AsyncMock()
        from seestar_mcp.models import TargetSearchResult

        mock_resolver.resolve_target.return_value = TargetSearchResult(
            found=False, alternatives=["M31", "M42"], search_query="NonExistent"
        )

        with (
            patch("seestar_mcp.server._telescope_client", mock_telescope_client),
            patch("seestar_mcp.server._target_resolver", mock_resolver),
        ):

            tools = await server._list_tools()
            goto_tool = next(tool for tool in tools if tool.name == "goto_target")

            with pytest.raises(Exception):  # ToolError
                await goto_tool.fn(target_name="NonExistent", ctx=mock_context)

    @pytest.mark.asyncio
    async def test_start_imaging(
        self, mock_telescope_client, mock_imaging_state, mock_context
    ):
        """Test starting imaging session."""
        server = create_server()

        mock_telescope_client.start_imaging.return_value = True
        mock_telescope_client.get_imaging_status.return_value = mock_imaging_state

        with patch("seestar_mcp.server._telescope_client", mock_telescope_client):

            tools = await server._list_tools()
            imaging_tool = next(tool for tool in tools if tool.name == "start_imaging")

            result = await imaging_tool.fn(
                exposure_time=120.0, count=10, gain=100, binning=1, ctx=mock_context
            )

            assert result.success is True
            assert "Started imaging" in result.message
            mock_telescope_client.start_imaging.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_imaging(
        self, mock_telescope_client, mock_imaging_state, mock_context
    ):
        """Test stopping imaging session."""
        server = create_server()

        mock_telescope_client.stop_imaging.return_value = True
        mock_telescope_client.get_imaging_status.return_value = mock_imaging_state

        with patch("seestar_mcp.server._telescope_client", mock_telescope_client):

            tools = await server._list_tools()
            stop_tool = next(tool for tool in tools if tool.name == "stop_imaging")

            result = await stop_tool.fn(ctx=mock_context)

            assert result.success is True
            assert "stopped" in result.message
            mock_telescope_client.stop_imaging.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_imaging_status(
        self, mock_telescope_client, mock_imaging_state, mock_context
    ):
        """Test getting imaging status."""
        server = create_server()

        mock_imaging_state.status = ImagingStatus.RUNNING
        mock_imaging_state.progress = 50
        mock_telescope_client.get_imaging_status.return_value = mock_imaging_state

        with patch("seestar_mcp.server._telescope_client", mock_telescope_client):

            tools = await server._list_tools()
            status_tool = next(
                tool for tool in tools if tool.name == "get_imaging_status"
            )

            result = await status_tool.fn(ctx=mock_context)

            assert result.success is True
            assert result.imaging_state.status == ImagingStatus.RUNNING
            assert result.imaging_state.progress == 50

    @pytest.mark.asyncio
    async def test_start_calibration(
        self, mock_telescope_client, mock_calibration_state, mock_context
    ):
        """Test starting calibration."""
        server = create_server()

        mock_telescope_client.start_calibration.return_value = True
        mock_telescope_client.get_calibration_status.return_value = (
            mock_calibration_state
        )

        with patch("seestar_mcp.server._telescope_client", mock_telescope_client):

            tools = await server._list_tools()
            cal_tool = next(tool for tool in tools if tool.name == "start_calibration")

            result = await cal_tool.fn(ctx=mock_context)

            assert result.success is True
            assert "Calibration sequence started" in result.message
            mock_telescope_client.start_calibration.assert_called_once()

    @pytest.mark.asyncio
    async def test_park_telescope(
        self, mock_telescope_client, mock_telescope_state, mock_context
    ):
        """Test parking telescope."""
        server = create_server()

        mock_telescope_client.park_telescope.return_value = True
        mock_telescope_client.get_status.return_value = mock_telescope_state

        with patch("seestar_mcp.server._telescope_client", mock_telescope_client):

            tools = await server._list_tools()
            park_tool = next(tool for tool in tools if tool.name == "park_telescope")

            result = await park_tool.fn(ctx=mock_context)

            assert result.success is True
            assert "parked successfully" in result.message
            mock_telescope_client.park_telescope.assert_called_once()

    @pytest.mark.asyncio
    async def test_unpark_telescope(
        self, mock_telescope_client, mock_telescope_state, mock_context
    ):
        """Test unparking telescope."""
        server = create_server()

        mock_telescope_client.unpark_telescope.return_value = True
        mock_telescope_client.get_status.return_value = mock_telescope_state

        with patch("seestar_mcp.server._telescope_client", mock_telescope_client):

            tools = await server._list_tools()
            unpark_tool = next(
                tool for tool in tools if tool.name == "unpark_telescope"
            )

            result = await unpark_tool.fn(ctx=mock_context)

            assert result.success is True
            assert "unparked successfully" in result.message
            mock_telescope_client.unpark_telescope.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_target(self, mock_target_resolver, mock_target, mock_context):
        """Test target search."""
        server = create_server()

        with patch("seestar_mcp.server._target_resolver", mock_target_resolver):

            tools = await server._list_tools()
            search_tool = next(tool for tool in tools if tool.name == "search_target")

            result = await search_tool.fn(target_name="M31", ctx=mock_context)

            assert result.found is True
            assert result.target.name == "M31"

    @pytest.mark.asyncio
    async def test_get_system_info(
        self, mock_telescope_client, mock_telescope_info, mock_context
    ):
        """Test getting system info."""
        server = create_server()

        mock_telescope_client._telescope_info = mock_telescope_info

        with patch("seestar_mcp.server._telescope_client", mock_telescope_client):

            tools = await server._list_tools()
            info_tool = next(tool for tool in tools if tool.name == "get_system_info")

            result = await info_tool.fn(ctx=mock_context)

            assert result.mcp_server_version is not None
            assert result.connection_status is True
            assert result.telescope_info == mock_telescope_info

    @pytest.mark.asyncio
    async def test_emergency_stop(self, mock_telescope_client, mock_context):
        """Test emergency stop."""
        server = create_server()

        mock_telescope_client.emergency_stop.return_value = True

        with patch("seestar_mcp.server._telescope_client", mock_telescope_client):

            tools = await server._list_tools()
            stop_tool = next(tool for tool in tools if tool.name == "emergency_stop")

            result = await stop_tool.fn(ctx=mock_context)

            assert result.success is True
            assert "Emergency stop executed" in result.message
            mock_telescope_client.emergency_stop.assert_called_once()
