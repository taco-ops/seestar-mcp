"""FastMCP server for SeestarS50 telescope control."""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from types import FrameType
from typing import Annotated, Optional

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .models import (
    CalibrationResponse,
    ImagingParams,
    ImagingResponse,
    Response,
    SystemInfo,
    TargetSearchResult,
    TelescopeResponse,
)
from .target_resolver import TargetResolver, format_coordinates
from .telescope_client import SeestarClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global state
_telescope_client: Optional[SeestarClient] = None
_target_resolver: Optional[TargetResolver] = None
_server_start_time = datetime.now()
_last_command: Optional[str] = None
_last_command_time: Optional[datetime] = None


def create_server() -> FastMCP:
    """Create and configure the FastMCP server."""

    mcp: FastMCP = FastMCP(
        name="seestar-mcp",
    )

    @mcp.tool(
        name="connect_telescope",
        description="Connect to the SeestarS50 telescope",
        annotations={
            "title": "Connect Telescope",
            "readOnlyHint": False,
            "destructiveHint": False,
        },
    )
    async def connect_telescope(
        host: Annotated[str, Field(description="Telescope IP address")],
        port: Annotated[
            int, Field(description="Telescope port", ge=1, le=65535)
        ] = 4700,
        timeout: Annotated[
            float, Field(description="Connection timeout in seconds", gt=0)
        ] = 30.0,
        ctx: Optional[Context] = None,
    ) -> TelescopeResponse:
        """Connect to the SeestarS50 telescope."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "connect_telescope"
        _last_command_time = datetime.now()

        if ctx:
            await ctx.info(f"Connecting to telescope at {host}:{port}")

        try:
            # Close existing connection if any
            if _telescope_client:
                await _telescope_client.disconnect()

            # Create new client and connect
            _telescope_client = SeestarClient(host, port, timeout)
            success = await _telescope_client.connect()

            if success:
                state = await _telescope_client.get_status()
                message = f"Successfully connected to telescope at {host}:{port}"
                if ctx:
                    await ctx.info(message)

                return TelescopeResponse(
                    success=True, message=message, telescope_state=state
                )
            else:
                error_msg = f"Failed to connect to telescope at {host}:{port}"
                if ctx:
                    await ctx.error(error_msg)
                raise ToolError(error_msg)

        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="disconnect_telescope",
        description="Disconnect from the telescope",
        annotations={
            "title": "Disconnect Telescope",
            "readOnlyHint": False,
            "destructiveHint": False,
        },
    )
    async def disconnect_telescope(ctx: Optional[Context] = None) -> Response:
        """Disconnect from the telescope."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "disconnect_telescope"
        _last_command_time = datetime.now()

        try:
            if _telescope_client:
                await _telescope_client.disconnect()
                _telescope_client = None
                message = "Disconnected from telescope"
                if ctx:
                    await ctx.info(message)
                return Response(success=True, message=message)
            else:
                message = "No telescope connection to disconnect"
                return Response(success=True, message=message)

        except Exception as e:
            error_msg = f"Disconnect failed: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="get_telescope_status",
        description="Get current telescope status and position",
        annotations={
            "title": "Get Telescope Status",
            "readOnlyHint": True,
            "destructiveHint": False,
        },
    )
    async def get_telescope_status(ctx: Optional[Context] = None) -> TelescopeResponse:
        """Get current telescope status."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "get_telescope_status"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        try:
            state = await _telescope_client.get_status()
            if state:
                return TelescopeResponse(
                    success=True,
                    message="Telescope status retrieved successfully",
                    telescope_state=state,
                )
            else:
                raise ToolError("Failed to get telescope status")

        except Exception as e:
            error_msg = f"Failed to get status: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="goto_target",
        description="Slew telescope to a named astronomical target",
        annotations={
            "title": "Goto Target",
            "readOnlyHint": False,
            "destructiveHint": False,
        },
    )
    async def goto_target(
        target_name: Annotated[
            str,
            Field(
                description="Name of astronomical target "
                "(e.g., 'M31', 'Andromeda Galaxy')"
            ),
        ],
        ctx: Optional[Context] = None,
    ) -> TelescopeResponse:
        """Slew telescope to a named target."""
        global _telescope_client, _target_resolver, _last_command, _last_command_time

        _last_command = "goto_target"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        if ctx:
            await ctx.info(f"Resolving target: {target_name}")
            await ctx.report_progress(10, 100)

        try:
            # Initialize target resolver if needed
            if not _target_resolver:
                _target_resolver = TargetResolver()

            # Resolve target name to coordinates
            result = await _target_resolver.resolve_target(target_name)

            if ctx:
                await ctx.report_progress(40, 100)

            if not result.found:
                alternatives_text = ""
                if result.alternatives:
                    alternatives_text = f" Try: {', '.join(result.alternatives)}"
                raise ToolError(f"Target '{target_name}' not found.{alternatives_text}")

            target = result.target
            if target is None:
                alternatives_text = ""
                if result.alternatives:
                    alternatives_text = f" Try: {', '.join(result.alternatives)}"
                raise ToolError(f"Target '{target_name}' not found.{alternatives_text}")

            if ctx:
                coord_str = format_coordinates(target.coordinates)
                await ctx.info(f"Target found: {target.name} at {coord_str}")
                await ctx.report_progress(60, 100)

            # Slew to target
            try:
                # Check if this is a solar target - use special solar observation mode
                target_name_lower = target.name.lower()
                is_solar_target = (
                    "sun" in target_name_lower
                    or target_name_lower == "sol"
                    or "☉" in target_name_lower
                )

                if is_solar_target:
                    if ctx:
                        await ctx.info(
                            f"⚠️  SOLAR OBSERVATION: Using specialized solar mode for {target.name}"
                        )
                        await ctx.info(
                            "Ensure proper solar filter is installed before observation!"
                        )

                    # Use solar observation mode instead of coordinate slewing
                    result = await _telescope_client.start_solar_observation(
                        target.name
                    )
                    success = result.get("success", False)

                    if not success and "error" in result:
                        raise RuntimeError(result["error"])

                else:
                    # Regular coordinate slewing for non-solar targets
                    mosaic_params = None
                    success = await _telescope_client.goto_coordinates(
                        target.coordinates, target.name, mosaic_params
                    )

            except RuntimeError as e:
                # Handle specific slewing errors (like below horizon)
                error_msg = str(e)
                if ctx:
                    await ctx.error(error_msg)
                raise ToolError(error_msg)

            if ctx:
                await ctx.report_progress(80, 100)

            if success:
                # Get updated status
                state = await _telescope_client.get_status()
                if state:
                    state.current_target = target.name

                if ctx:
                    await ctx.report_progress(100, 100)

                    if is_solar_target:
                        await ctx.info(
                            f"Successfully started solar observation mode for {target.name}"
                        )
                        await ctx.info(
                            "⚠️  Telescope should now be pointing to Sun - verify solar filter is installed!"
                        )
                    else:
                        await ctx.info(f"Successfully slewing to {target.name}")

                # Different message for solar vs regular targets
                message = (
                    f"Solar observation mode started for {target.name}"
                    if is_solar_target
                    else f"Slewing to {target.name}"
                )

                return TelescopeResponse(
                    success=True,
                    message=message,
                    data={"target": target.model_dump()},
                    telescope_state=state,
                )
            else:
                raise ToolError(f"Failed to slew to {target.name}")

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to goto target: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="start_imaging",
        description="Start an imaging session with specified parameters",
        annotations={
            "title": "Start Imaging",
            "readOnlyHint": False,
            "destructiveHint": False,
        },
    )
    async def start_imaging(
        exposure_time: Annotated[
            float, Field(description="Exposure time in seconds", gt=0)
        ],
        count: Annotated[int, Field(description="Number of images to capture", gt=0)],
        gain: Annotated[
            Optional[int], Field(description="Gain setting (0-300)", ge=0, le=300)
        ] = None,
        binning: Annotated[
            Optional[int], Field(description="Binning factor (1-4)", ge=1, le=4)
        ] = 1,
        filter_name: Annotated[Optional[str], Field(description="Filter name")] = None,
        ctx: Optional[Context] = None,
    ) -> ImagingResponse:
        """Start imaging session."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "start_imaging"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        if ctx:
            await ctx.info(f"Starting imaging: {count} images x {exposure_time}s")

        try:
            params = ImagingParams(
                exposure_time=exposure_time,
                count=count,
                gain=gain,
                binning=binning,
                filter_name=filter_name,
                mosaic_mode=False,
                mosaic_width=1,
                mosaic_height=1,
            )

            success = await _telescope_client.start_imaging(params)

            if success:
                # Get imaging status
                state = await _telescope_client.get_imaging_status()

                message = f"Started imaging: {count} images x {exposure_time}s"
                if ctx:
                    await ctx.info(message)

                return ImagingResponse(
                    success=True,
                    message=message,
                    data={"params": params.model_dump()},
                    imaging_state=state,
                )
            else:
                raise ToolError("Failed to start imaging session")

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to start imaging: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="stop_imaging",
        description="Stop the current imaging session",
        annotations={
            "title": "Stop Imaging",
            "readOnlyHint": False,
            "destructiveHint": True,
        },
    )
    async def stop_imaging(ctx: Optional[Context] = None) -> ImagingResponse:
        """Stop current imaging session."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "stop_imaging"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        try:
            success = await _telescope_client.stop_imaging()

            if success:
                state = await _telescope_client.get_imaging_status()
                message = "Imaging session stopped"
                if ctx:
                    await ctx.info(message)

                return ImagingResponse(
                    success=True, message=message, imaging_state=state
                )
            else:
                raise ToolError("Failed to stop imaging session")

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to stop imaging: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="get_imaging_status",
        description="Get current imaging session status and progress",
        annotations={
            "title": "Get Imaging Status",
            "readOnlyHint": True,
            "destructiveHint": False,
        },
    )
    async def get_imaging_status(ctx: Optional[Context] = None) -> ImagingResponse:
        """Get current imaging status."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "get_imaging_status"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        try:
            state = await _telescope_client.get_imaging_status()

            if state:
                return ImagingResponse(
                    success=True,
                    message="Imaging status retrieved successfully",
                    imaging_state=state,
                )
            else:
                raise ToolError("Failed to get imaging status")

        except Exception as e:
            error_msg = f"Failed to get imaging status: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="start_mosaic_imaging",
        description="Start a mosaic imaging session to capture a wider field of view",
        annotations={
            "title": "Start Mosaic Imaging",
            "readOnlyHint": False,
            "destructiveHint": False,
        },
    )
    async def start_mosaic_imaging(
        target_name: Annotated[
            str,
            Field(
                description="Name of astronomical target "
                "(e.g., 'M31', 'Andromeda Galaxy')"
            ),
        ],
        exposure_time: Annotated[
            float, Field(description="Exposure time in seconds", gt=0)
        ],
        count: Annotated[int, Field(description="Number of images to capture", gt=0)],
        mosaic_width: Annotated[
            int, Field(description="Mosaic width (1-2)", ge=1, le=2)
        ] = 2,
        mosaic_height: Annotated[
            int, Field(description="Mosaic height (1-2)", ge=1, le=2)
        ] = 2,
        gain: Annotated[
            Optional[int], Field(description="Gain setting (0-300)", ge=0, le=300)
        ] = None,
        binning: Annotated[
            Optional[int], Field(description="Binning factor (1-4)", ge=1, le=4)
        ] = 1,
        filter_name: Annotated[Optional[str], Field(description="Filter name")] = None,
        ctx: Optional[Context] = None,
    ) -> TelescopeResponse:
        """Start mosaic imaging session of a target."""
        global _telescope_client, _target_resolver, _last_command, _last_command_time

        _last_command = "start_mosaic_imaging"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        if ctx:
            await ctx.info(
                f"Starting mosaic imaging of {target_name} ({mosaic_width}x{mosaic_height})"
            )
            await ctx.report_progress(20, 100)

        try:
            # Initialize target resolver if needed
            if not _target_resolver:
                _target_resolver = TargetResolver()

            # Resolve target name to coordinates
            result = await _target_resolver.resolve_target(target_name)

            if ctx:
                await ctx.report_progress(40, 100)

            if not result.found:
                alternatives_text = ""
                if result.alternatives:
                    alternatives_text = f" Try: {', '.join(result.alternatives)}"
                raise ToolError(f"Target '{target_name}' not found.{alternatives_text}")

            target = result.target
            if target is None:
                alternatives_text = ""
                if result.alternatives:
                    alternatives_text = f" Try: {', '.join(result.alternatives)}"
                raise ToolError(f"Target '{target_name}' not found.{alternatives_text}")

            if ctx:
                coord_str = format_coordinates(target.coordinates)
                await ctx.info(f"Target found: {target.name} at {coord_str}")
                await ctx.report_progress(60, 100)

            # Prepare mosaic parameters
            mosaic_params = {
                "mosaic_mode": True,
                "mosaic_width": mosaic_width,
                "mosaic_height": mosaic_height,
            }

            # Slew to target with mosaic mode
            try:
                success = await _telescope_client.goto_coordinates(
                    target.coordinates, target.name, mosaic_params
                )
            except RuntimeError as e:
                # Handle specific slewing errors (like below horizon)
                error_msg = str(e)
                if ctx:
                    await ctx.error(error_msg)
                raise ToolError(error_msg)

            if ctx:
                await ctx.report_progress(80, 100)

            if success:
                # Start mosaic imaging
                params = ImagingParams(
                    exposure_time=exposure_time,
                    count=count,
                    gain=gain,
                    binning=binning,
                    filter_name=filter_name,
                    mosaic_mode=True,
                    mosaic_width=mosaic_width,
                    mosaic_height=mosaic_height,
                )

                imaging_success = await _telescope_client.start_imaging(params)

                if imaging_success:
                    # Get updated status
                    state = await _telescope_client.get_status()
                    if state:
                        state.current_target = (
                            f"{target.name} (Mosaic {mosaic_width}x{mosaic_height})"
                        )

                    if ctx:
                        await ctx.report_progress(100, 100)
                        await ctx.info(f"Started mosaic imaging of {target.name}")

                    return TelescopeResponse(
                        success=True,
                        message=f"Started mosaic imaging of {target.name} ({mosaic_width}x{mosaic_height})",
                        data={
                            "target": target.dict(),
                            "mosaic": {"width": mosaic_width, "height": mosaic_height},
                        },
                        telescope_state=state,
                    )
                else:
                    raise ToolError(f"Failed to start mosaic imaging of {target.name}")
            else:
                raise ToolError(f"Failed to slew to {target.name}")

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to start mosaic imaging: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="start_calibration",
        description="Start telescope calibration sequence",
        annotations={
            "title": "Start Calibration",
            "readOnlyHint": False,
            "destructiveHint": False,
        },
    )
    async def start_calibration(ctx: Optional[Context] = None) -> CalibrationResponse:
        """Start telescope calibration."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "start_calibration"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        if ctx:
            await ctx.info("Starting telescope calibration sequence")

        try:
            success = await _telescope_client.start_calibration()

            if success:
                state = await _telescope_client.get_calibration_status()
                message = "Calibration sequence started"
                if ctx:
                    await ctx.info(message)

                return CalibrationResponse(
                    success=True, message=message, calibration_state=state
                )
            else:
                raise ToolError("Failed to start calibration sequence")

        except RuntimeError as e:
            # Handle calibration not supported error gracefully
            error_msg = str(e)
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)
        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to start calibration: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="get_calibration_status",
        description="Get current calibration status and progress",
        annotations={
            "title": "Get Calibration Status",
            "readOnlyHint": True,
            "destructiveHint": False,
        },
    )
    async def get_calibration_status(
        ctx: Optional[Context] = None,
    ) -> CalibrationResponse:
        """Get calibration status."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "get_calibration_status"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        try:
            state = await _telescope_client.get_calibration_status()

            if state:
                return CalibrationResponse(
                    success=True,
                    message="Calibration status retrieved successfully",
                    calibration_state=state,
                )
            else:
                raise ToolError("Failed to get calibration status")

        except Exception as e:
            error_msg = f"Failed to get calibration status: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="park_telescope",
        description="Park the telescope to its home position",
        annotations={
            "title": "Park Telescope",
            "readOnlyHint": False,
            "destructiveHint": False,
        },
    )
    async def park_telescope(ctx: Optional[Context] = None) -> TelescopeResponse:
        """Park the telescope."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "park_telescope"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        if ctx:
            await ctx.info("Parking telescope")

        try:
            success = await _telescope_client.park_telescope()

            if success:
                state = await _telescope_client.get_status()
                message = "Telescope parked successfully"
                if ctx:
                    await ctx.info(message)

                return TelescopeResponse(
                    success=True, message=message, telescope_state=state
                )
            else:
                raise ToolError("Failed to park telescope")

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to park telescope: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="unpark_telescope",
        description="Unpark the telescope from its home position",
        annotations={
            "title": "Unpark Telescope",
            "readOnlyHint": False,
            "destructiveHint": False,
        },
    )
    async def unpark_telescope(ctx: Optional[Context] = None) -> TelescopeResponse:
        """Unpark the telescope."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "unpark_telescope"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        if ctx:
            await ctx.info("Unparking telescope")

        try:
            success = await _telescope_client.unpark_telescope()

            if success:
                state = await _telescope_client.get_status()
                message = "Telescope unparked successfully"
                if ctx:
                    await ctx.info(message)

                return TelescopeResponse(
                    success=True, message=message, telescope_state=state
                )
            else:
                raise ToolError("Failed to unpark telescope")

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to unpark telescope: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="open_telescope_arm",
        description="Open the telescope arm (similar to unpark but more explicit)",
        annotations={
            "title": "Open Telescope Arm",
            "readOnlyHint": False,
            "destructiveHint": False,
        },
    )
    async def open_telescope_arm(ctx: Optional[Context] = None) -> TelescopeResponse:
        """Open the telescope arm using correct SeestarS50 commands."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "open_telescope_arm"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        try:
            if ctx:
                await ctx.info("Opening telescope arm using scope_move_to_horizon...")

            # Use the corrected unpark method with scope_move_to_horizon
            result = await _telescope_client.unpark_telescope()

            if result.get("success"):
                state = await _telescope_client.get_status()
                message = "Telescope arm opened successfully using horizon positioning"
                if ctx:
                    await ctx.info(message)

                return TelescopeResponse(
                    success=True, message=message, telescope_state=state, data=result
                )
            else:
                error = result.get("error", "Unknown error")
                raise ToolError(f"Failed to open telescope arm: {error}")

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to open telescope arm: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to open telescope arm: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="close_telescope_arm",
        description="Close the telescope arm (similar to park but more explicit)",
        annotations={
            "title": "Close Telescope Arm",
            "readOnlyHint": False,
            "destructiveHint": False,
        },
    )
    async def close_telescope_arm(ctx: Optional[Context] = None) -> TelescopeResponse:
        """Close the telescope arm using correct SeestarS50 commands."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "close_telescope_arm"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        try:
            if ctx:
                await ctx.info("Closing telescope arm...")

            # Use the corrected park method with proper parameters
            result = await _telescope_client.park_telescope(eq_mode=False)

            if result.get("success"):
                state = await _telescope_client.get_status()
                message = "Telescope arm closed successfully (parked in Alt-Az mode)"
                if ctx:
                    await ctx.info(message)

                return TelescopeResponse(
                    success=True, message=message, telescope_state=state, data=result
                )
            else:
                error = result.get("error", "Unknown error")
                raise ToolError(f"Failed to close telescope arm: {error}")

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to close telescope arm: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Failed to close telescope arm: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="check_solar_safety",
        description="Check if solar observation is safe and provide detailed visibility information",
        annotations={
            "title": "Check Solar Safety",
            "readOnlyHint": True,
            "destructiveHint": False,
        },
    )
    async def check_solar_safety(ctx: Optional[Context] = None) -> TelescopeResponse:
        """Check solar safety conditions and visibility."""
        global _target_resolver, _last_command, _last_command_time

        _last_command = "check_solar_safety"
        _last_command_time = datetime.now()

        try:
            if ctx:
                await ctx.info("Checking solar observation safety...")

            # Initialize target resolver if needed
            if not _target_resolver:
                _target_resolver = TargetResolver()

            # Resolve sun coordinates
            result = await _target_resolver.resolve_target("sun")

            if not result.found or not result.target:
                raise ToolError("Failed to resolve sun coordinates")

            target = result.target

            # Check visibility
            is_visible, altitude, status = _target_resolver.check_target_visibility(
                target.coordinates
            )

            # Create detailed safety report
            safety_info = {
                "sun_coordinates": {
                    "ra": target.coordinates.ra,
                    "dec": target.coordinates.dec,
                    "epoch": target.coordinates.epoch,
                },
                "visibility": {
                    "is_visible": is_visible,
                    "altitude_degrees": altitude,
                    "status": status,
                },
                "safety_warnings": [
                    "⚠️ CRITICAL: Ensure proper solar filter is installed before any solar observation",
                    "⚠️ Never look directly at the sun through the telescope without proper filtration",
                    "⚠️ Some telescopes have built-in safety mechanisms that prevent solar pointing",
                    "⚠️ If slewing fails with 'mount goto failed', the telescope may be protecting against solar observation",
                ],
                "recommendations": [],
            }

            if is_visible:
                safety_info["recommendations"].extend(
                    [
                        "✅ Sun is above horizon and visible",
                        "🔍 Verify solar filter is properly installed",
                        "🧪 Try slewing to sun - failure may indicate telescope safety protection",
                    ]
                )
            else:
                safety_info["recommendations"].extend(
                    [
                        "❌ Sun is below horizon - not visible for observation",
                        "⏰ Wait until sun rises above horizon for solar observation",
                    ]
                )

            if ctx:
                await ctx.info(f"Solar safety check complete: {status}")
                if is_visible:
                    await ctx.warning(
                        "Solar filter verification required before observation!"
                    )

            return TelescopeResponse(
                success=True, message=f"Solar safety check: {status}", data=safety_info
            )

        except Exception as e:
            error_msg = f"Solar safety check failed: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="search_target",
        description="Search for an astronomical target by name",
        annotations={
            "title": "Search Target",
            "readOnlyHint": True,
            "destructiveHint": False,
        },
    )
    async def search_target(
        target_name: Annotated[
            str, Field(description="Name of astronomical target to search for")
        ],
        ctx: Optional[Context] = None,
    ) -> TargetSearchResult:
        """Search for a target by name."""
        global _target_resolver, _last_command, _last_command_time

        _last_command = "search_target"
        _last_command_time = datetime.now()

        if ctx:
            await ctx.info(f"Searching for target: {target_name}")

        try:
            # Initialize target resolver if needed
            if not _target_resolver:
                _target_resolver = TargetResolver()

            result = await _target_resolver.resolve_target(target_name)

            if result.found and result.target is not None and ctx:
                coord_str = format_coordinates(result.target.coordinates)
                await ctx.info(f"Found: {result.target.name} at {coord_str}")
            elif not result.found and ctx:
                await ctx.warning(f"Target '{target_name}' not found")

            return result

        except Exception as e:
            error_msg = f"Target search failed: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="get_system_info",
        description="Get MCP server and telescope system information",
        annotations={
            "title": "Get System Info",
            "readOnlyHint": True,
            "destructiveHint": False,
        },
    )
    async def get_system_info(ctx: Optional[Context] = None) -> SystemInfo:
        """Get system information."""
        global _telescope_client, _server_start_time, _last_command, _last_command_time

        try:
            from . import __version__

            telescope_info = None
            connection_status = False

            if _telescope_client and _telescope_client.is_connected:
                connection_status = True
                telescope_info = _telescope_client._telescope_info

            uptime = (datetime.now() - _server_start_time).total_seconds()

            return SystemInfo(
                mcp_server_version=__version__,
                telescope_info=telescope_info,
                connection_status=connection_status,
                uptime=uptime,
                last_command=_last_command,
                last_command_time=_last_command_time,
            )

        except Exception as e:
            error_msg = f"Failed to get system info: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    @mcp.tool(
        name="emergency_stop",
        description="Emergency stop all telescope operations",
        annotations={
            "title": "Emergency Stop",
            "readOnlyHint": False,
            "destructiveHint": True,
        },
    )
    async def emergency_stop(ctx: Optional[Context] = None) -> Response:
        """Emergency stop all operations."""
        global _telescope_client, _last_command, _last_command_time

        _last_command = "emergency_stop"
        _last_command_time = datetime.now()

        if not _telescope_client or not _telescope_client.is_connected:
            raise ToolError("Not connected to telescope. Use connect_telescope first.")

        if ctx:
            await ctx.warning("EMERGENCY STOP - Halting all telescope operations")

        try:
            success = await _telescope_client.emergency_stop()

            if success:
                message = "Emergency stop executed - all operations halted"
                if ctx:
                    await ctx.warning(message)

                return Response(success=True, message=message)
            else:
                raise ToolError("Emergency stop command failed")

        except ToolError:
            raise
        except Exception as e:
            error_msg = f"Emergency stop failed: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ToolError(error_msg)

    return mcp


def main() -> None:
    """Main entry point for the MCP server."""
    import signal
    import sys

    # Set up signal handlers
    def signal_handler(sig: int, frame: Optional[FrameType]) -> None:
        logger.info("Shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Parse arguments
    parser = argparse.ArgumentParser(description="SeestarS50 MCP Server")
    parser.add_argument(
        "--host",
        default=os.getenv("SEESTAR_HOST"),
        help="Telescope IP address (or set SEESTAR_HOST env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("SEESTAR_PORT", "4700")),
        help="Telescope port (default: 4700)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("SEESTAR_TIMEOUT", "30.0")),
        help="Connection timeout in seconds (default: 30.0)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create server
    mcp = create_server()

    # Auto-connect if host provided (run in background)
    if args.host:
        logger.info(f"Auto-connecting to telescope at {args.host}:{args.port}")

        def auto_connect_background() -> None:
            import asyncio
            import threading

            async def connect() -> None:
                global _telescope_client
                try:
                    _telescope_client = SeestarClient(
                        args.host, args.port, args.timeout
                    )
                    success = await _telescope_client.connect()
                    if success:
                        logger.info("Auto-connection successful")
                    else:
                        logger.warning("Auto-connection failed")
                except Exception as e:
                    logger.warning(f"Auto-connection error: {e}")

            # Run connection in a separate thread
            def run_connect() -> None:
                try:
                    asyncio.run(connect())
                except Exception as e:
                    logger.warning(f"Background connection error: {e}")

            thread = threading.Thread(target=run_connect, daemon=True)
            thread.start()

        auto_connect_background()

    # Start the MCP server
    logger.info("🚧 SeestarS50 MCP Server - PUBLIC BETA VERSION")
    logger.info(
        "⚠️  This software is in beta testing. Report issues at: https://github.com/taco-ops/seestar-mcp/issues"
    )
    logger.info("Starting SeestarS50 MCP server...")
    try:
        # Let FastMCP handle everything
        mcp.run()
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
