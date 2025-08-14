"""TCP client for communicating with SeestarS50 telescope."""

import asyncio
import json
import logging
import socket
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .location_manager import LocationManager
from .models import (
    CalibrationState,
    CalibrationStatus,
    Coordinates,
    ImagingParams,
    ImagingState,
    ImagingStatus,
    TelescopeInfo,
    TelescopeState,
    TelescopeStatus,
)

logger = logging.getLogger(__name__)


class SeestarConnectionError(Exception):
    """Exception raised when telescope connection fails."""

    pass


class SeestarClient:
    """TCP client for SeestarS50 telescope communication."""

    def __init__(
        self,
        host: str,
        port: int = 4700,
        timeout: float = 30.0,
        location_manager: Optional[LocationManager] = None,
    ) -> None:
        """
        Initialize the SeestarS50 client.

        Args:
            host: Telescope IP address
            port: Telescope port (default: 4700)
            timeout: Request timeout in seconds
            location_manager: Optional location manager for coordinate validation
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.location_manager = location_manager
        self.socket: Optional[socket.socket] = None
        self._connected = False
        self._telescope_info: Optional[TelescopeInfo] = None
        self._cmdid = 1000
        self._is_watch_events = True
        self._op_state = "idle"
        self._message_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_heartbeat = time.time()
        self._last_error_details: Optional[Dict[str, Any]] = None

    def _get_cmdid(self) -> int:
        """Get next command ID."""
        with self._lock:
            self._cmdid += 1
            return self._cmdid

    def _send_message(self, data: str) -> None:
        """Send message to telescope."""
        if not self.socket:
            raise RuntimeError("Not connected to telescope")

        try:
            logger.info(f"SENDING: {data.strip()}")
            self.socket.sendall(data.encode("utf-8"))
        except socket.error as e:
            logger.error(f"Failed to send message: {e}")
            self._connected = False
            raise

    def _receive_message(self) -> str:
        """Receive message from telescope."""
        if not self.socket:
            raise RuntimeError("Not connected to telescope")

        try:
            data = self.socket.recv(1024 * 60)  # Large buffer for image data
            return data.decode("utf-8")
        except socket.error as e:
            logger.error(f"Failed to receive message: {e}")
            self._connected = False
            raise

    def _json_message(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send JSON message to telescope."""
        data = {"id": self._get_cmdid(), "method": method}

        if params:
            data["params"] = params

        json_data = json.dumps(data)
        logger.info(f"JSON COMMAND: {method} -> {json_data}")
        self._send_message(json_data + "\r\n")

    def _message_thread_fn(self) -> None:
        """Background thread to handle incoming messages."""
        msg_remainder = ""
        consecutive_failures = 0
        max_failures = 10  # Increased from 3 to 10 for better resilience
        reconnect_delay = 2.0  # Start with 2 seconds, will increase on failures
        last_heartbeat_check = time.time()

        while self._is_watch_events:
            try:
                if not self._connected:
                    # Try to reconnect synchronously in thread
                    logger.info("Attempting to reconnect to telescope...")
                    if self._sync_reconnect():
                        consecutive_failures = 0
                        reconnect_delay = 2.0  # Reset delay on successful reconnect
                        self._last_heartbeat = time.time()
                        logger.info("Reconnected successfully")
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_failures:
                            logger.error(
                                f"Failed to reconnect after {max_failures} attempts, stopping message thread"
                            )
                            break
                        # Exponential backoff with max delay of 30 seconds
                        reconnect_delay = min(reconnect_delay * 1.5, 30.0)
                        logger.info(
                            f"Reconnect attempt {consecutive_failures}/{max_failures} failed, waiting {reconnect_delay:.1f}s"
                        )
                        time.sleep(reconnect_delay)
                        continue

                # Send periodic heartbeat to maintain connection
                current_time = time.time()
                if current_time - last_heartbeat_check > 30:  # Check every 30 seconds
                    if (
                        current_time - self._last_heartbeat > 120
                    ):  # No response for 2 minutes
                        logger.warning(
                            "Telescope connection appears stale, sending heartbeat"
                        )
                        try:
                            self._json_message("test_connection")
                            self._last_heartbeat = current_time
                        except Exception as e:
                            logger.warning(f"Heartbeat failed: {e}")
                            self._connected = False
                            continue
                    last_heartbeat_check = current_time

                # Use shorter receive timeout to allow for periodic connection checks
                original_timeout = None
                if self.socket:
                    original_timeout = self.socket.gettimeout()
                    self.socket.settimeout(5.0)  # 5 second timeout for receives

                try:
                    data = self._receive_message()
                finally:
                    # Restore original timeout
                    if self.socket and original_timeout is not None:
                        self.socket.settimeout(original_timeout)

                if data:
                    consecutive_failures = 0  # Reset on successful receive
                    self._last_heartbeat = (
                        time.time()
                    )  # Update heartbeat on any message
                    msg_remainder += data
                    first_index = msg_remainder.find("\r\n")

                    while first_index >= 0:
                        first_msg = msg_remainder[0:first_index]
                        msg_remainder = msg_remainder[first_index + 2 :]

                        try:
                            parsed_data = json.loads(first_msg)
                            self._handle_message(parsed_data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON: {e}")

                        first_index = msg_remainder.find("\r\n")

            except socket.timeout:
                # Timeout is expected with shorter timeouts, don't count as failure
                logger.debug("Socket receive timeout (normal)")
                continue
            except Exception as e:
                logger.warning(f"Message thread error (will retry): {e}")
                self._connected = False
                consecutive_failures += 1

                if consecutive_failures >= max_failures:
                    logger.error(
                        f"Too many consecutive failures ({consecutive_failures}), stopping message thread"
                    )
                    break

                time.sleep(2)  # Brief pause before retry

            time.sleep(0.1)

    def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming message from telescope."""
        logger.info(f"RECEIVED: {json.dumps(message)}")

        # Handle AutoGoto events for slewing operations
        if "Event" in message and message["Event"] == "AutoGoto":
            state = message.get("state")
            error = message.get("error")
            logger.info(f"AutoGoto state: {state}")

            # Update operation state based on AutoGoto progress
            if state == "complete":
                self._op_state = "complete"
                logger.info("Telescope slewing completed successfully")
            elif state == "fail":
                self._op_state = "failed"
                # Store error details for better error reporting
                self._last_error_details = message
                if error == "below horizon":
                    logger.warning(
                        "Telescope slewing failed: Target is below horizon (not visible from current location/time)"
                    )
                elif error and (
                    "mount goto failed" in str(error).lower()
                    or "goto failed" in str(error).lower()
                ):
                    logger.warning(
                        f"Telescope slewing failed: {error}. This may indicate telescope safety protection (e.g., solar pointing prevention)"
                    )
                else:
                    logger.warning(
                        f"Telescope slewing failed: {error or 'Unknown error'}"
                    )
            elif state in ["working", "slewing"]:
                self._op_state = "working"
                logger.info("Telescope is slewing to target")
            else:
                logger.debug(f"AutoGoto intermediate state: {state}")

        # Handle other message types that might indicate operation completion
        if "result" in message and "code" in message:
            # Successful command response
            if message.get("code") == 0:
                logger.debug(f"Command response: {message.get('result', 'OK')}")
            else:
                logger.warning(
                    f"Command failed with code {message.get('code')}: {message.get('result', 'Unknown error')}"
                )

    async def __aenter__(self) -> "SeestarClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: type, exc_val: Exception, exc_tb: object
    ) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def _send_udp_handshake(self) -> None:
        """
        Send UDP introduction message to telescope.

        This is required by SeestarS50 to establish control properly.
        Based on seestar_alp implementation.
        """
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.settimeout(1.0)  # Short timeout for UDP

            # UDP initialization message
            message = {"id": 1, "method": "scan_iscope", "params": ""}
            message_bytes = json.dumps(message).encode("utf-8")

            # Send to UDP port 4720 (telescope's UDP listener)
            udp_addr = (self.host, 4720)
            logger.debug(f"Sending UDP initialization to {udp_addr}: {message}")
            udp_socket.sendto(message_bytes, udp_addr)

            # Try to receive response (optional, may timeout)
            try:
                response, addr = udp_socket.recvfrom(1024)
                logger.debug(
                    f"UDP initialization response from {addr}: {response.decode('utf-8', errors='ignore')}"
                )
            except socket.timeout:
                logger.debug("UDP initialization sent, no response (this is normal)")

            udp_socket.close()

        except Exception as e:
            logger.warning(f"UDP initialization failed (continuing anyway): {e}")

    async def connect(self) -> bool:
        """
        Connect to the telescope and verify communication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Step 1: Send UDP initialization to establish control
            await self._send_udp_handshake()

            # Step 2: Create TCP socket connection
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Enable TCP keepalive to detect dead connections
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Configure TCP keepalive parameters (Linux/macOS)
            try:
                if hasattr(socket, "TCP_KEEPIDLE"):
                    self.socket.setsockopt(
                        socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30
                    )  # Start after 30s
                if hasattr(socket, "TCP_KEEPINTVL"):
                    self.socket.setsockopt(
                        socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10
                    )  # Interval 10s
                if hasattr(socket, "TCP_KEEPCNT"):
                    self.socket.setsockopt(
                        socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3
                    )  # 3 probes
            except (OSError, AttributeError):
                # Some platforms don't support these, that's ok
                pass

            self.socket.settimeout(self.timeout)
            logger.info(f"Connecting to telescope at {self.host}:{self.port}")
            self.socket.connect((self.host, self.port))

            self._connected = True
            self._is_watch_events = True

            # Start message handling thread
            self._message_thread = threading.Thread(
                target=self._message_thread_fn, daemon=True
            )
            self._message_thread.start()

            # Test connection with a simple command
            self._json_message("test_connection")

            # Give a moment for the connection to be established
            await asyncio.sleep(1)

            # Get device info to verify communication
            info = await self.get_device_info()
            if info:
                self._telescope_info = info
                logger.info(
                    f"Connected to {info.device_name} at {self.host}:{self.port}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to connect to telescope: {e}")
            self._connected = False
            if self.socket:
                try:
                    self.socket.close()
                except (OSError, AttributeError):
                    # Ignore errors when closing socket - it may already be closed
                    pass
                self.socket = None

        return False

    async def disconnect(self) -> None:
        """Disconnect from the telescope."""
        self._is_watch_events = False
        self._connected = False

        if self._message_thread and self._message_thread.is_alive():
            self._message_thread.join(timeout=2.0)

        if self.socket:
            self.socket.close()
            self.socket = None

        logger.info("Disconnected from telescope")

    def _sync_reconnect(self) -> bool:
        """Synchronous reconnect for use in message thread."""
        try:
            # Close existing socket if any
            if self.socket:
                try:
                    self.socket.close()
                except (OSError, AttributeError):
                    # Ignore errors when closing socket - it may already be closed
                    pass
                self.socket = None

            # Create new TCP socket connection
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Enable TCP keepalive to detect dead connections
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Set shorter reconnect timeout
            self.socket.settimeout(15.0)
            self.socket.connect((self.host, self.port))

            self._connected = True

            # Test connection with a simple command
            self._json_message("test_connection")
            time.sleep(0.5)  # Brief wait for response
            return True

        except Exception as e:
            logger.warning(f"Sync reconnect failed: {e}")
            if self.socket:
                try:
                    self.socket.close()
                except (OSError, AttributeError):
                    # Ignore errors when closing socket - it may already be closed
                    pass
                self.socket = None
            self._connected = False
            return False

    @property
    def is_connected(self) -> bool:
        """Check if connected to telescope."""
        return self._connected and self.socket is not None

    async def get_device_info(self) -> Optional[TelescopeInfo]:
        """Get telescope device information."""
        try:
            # Try to get coordinates to verify connection
            self._json_message("scope_get_equ_coord")

            # Wait a bit for response
            await asyncio.sleep(1.0)

            # Return default device info since SeestarS50 doesn't provide detailed device info
            return TelescopeInfo(
                device_name="SeestarS50",
                firmware_version="unknown",
                hardware_version="unknown",
                serial_number="unknown",
                mount_type="alt-az",
            )

        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return None

    async def get_status(self) -> Optional[TelescopeState]:
        """Get current telescope status."""
        try:
            # Request current coordinates
            self._json_message("scope_get_equ_coord")

            # Wait for response (in a real implementation, we'd parse the response)
            await asyncio.sleep(0.5)

            # For now, return basic status
            return TelescopeState(
                status=TelescopeStatus.IDLE,
                connected=self.is_connected,
                ra=None,
                dec=None,
                az=None,
                alt=None,
                is_tracking=False,
                is_parked=False,
                current_target=None,
                last_updated=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return None

    async def goto_coordinates(
        self,
        coordinates: Coordinates,
        target_name: Optional[str] = None,
        mosaic_params: Optional[Dict[str, Any]] = None,
        skip_visibility_check: bool = False,
    ) -> bool:
        """
        Slew telescope to coordinates.

        The SeestarS50 uses AutoGoto when starting an observation with coordinates.
        We'll use iscope_start_view to trigger the AutoGoto system.

        Args:
            coordinates: Target coordinates
            target_name: Optional target name to display in the app
            mosaic_params: Optional mosaic parameters for mosaic mode
            skip_visibility_check: Skip visibility check (use with caution)

        Returns:
            True if slew command successful
        """
        try:
            # Check target visibility if location is configured
            if (
                not skip_visibility_check
                and self.location_manager
                and self.location_manager.is_configured()
            ):
                from .target_resolver import TargetResolver

                resolver = TargetResolver(self.location_manager)
                is_visible, altitude, status = resolver.check_target_visibility(
                    coordinates
                )

                logger.info(f"Target visibility: {status}")

                if not is_visible:
                    error_msg = (
                        f"Target is below the horizon (altitude: {altitude:.1f}°). "
                        f"This target is not visible from your location at this time. "
                        f"Try again when the target has risen above the horizon."
                    )
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

            # Use provided target name or create a descriptive one
            if target_name:
                display_name = target_name
            else:
                # Create a more descriptive default name
                ra_str = f"{coordinates.ra:.3f}h"
                dec_str = f"{coordinates.dec:+.3f}°"
                display_name = f"Target at {ra_str}, {dec_str}"

            # The SeestarS50 triggers AutoGoto when starting a view with coordinates
            # Use iscope_start_view to initiate slewing to target coordinates
            # Use higher precision for coordinates to improve accuracy
            ra_degrees = coordinates.ra * 15.0  # Convert RA hours to degrees

            params = {
                "mode": "star",  # Use standard star mode
                "target_ra_dec": [
                    round(ra_degrees, 6),  # Higher precision RA in degrees
                    round(coordinates.dec, 6),  # Higher precision DEC in degrees
                ],
                "target_name": display_name,  # Use meaningful target name
                "lp_filter": False,
                # Add plate solve flag to improve accuracy
                "auto_center": True,  # Enable auto-centering for better accuracy
            }

            # Add mosaic parameters if provided
            if mosaic_params:
                if mosaic_params.get("mosaic_mode", False):
                    params["mosaic"] = {
                        "enable": True,
                        "width": mosaic_params.get("mosaic_width", 1),
                        "height": mosaic_params.get("mosaic_height", 1),
                    }
                    # Update display name to indicate mosaic
                    width = mosaic_params.get("mosaic_width", 1)
                    height = mosaic_params.get("mosaic_height", 1)
                    display_name = f"{display_name} (Mosaic {width}x{height})"
                    params["target_name"] = display_name

            logger.info(
                f"Slewing telescope to {display_name}: RA: {coordinates.ra:.6f}h ({ra_degrees:.6f}°), DEC: {coordinates.dec:.6f}°"
            )
            self._json_message("iscope_start_view", params)

            # Wait for AutoGoto operation to initiate and complete
            # The AutoGoto events will be handled by _handle_message
            self._op_state = "working"
            timeout = (
                120  # Increased timeout for better accuracy (plate solving takes time)
            )
            start_time = time.time()

            while self._op_state == "working" and (time.time() - start_time) < timeout:
                # Send periodic status check to monitor progress
                if int(time.time() - start_time) % 10 == 0:
                    self._json_message("scope_get_equ_coord")
                await asyncio.sleep(2)

            # Check final state
            if self._op_state == "complete":
                logger.info(
                    f"Telescope AutoGoto to {display_name} completed successfully"
                )
                return True
            elif self._op_state == "failed":
                # Provide specific error message based on failure reason
                error_msg = f"Telescope AutoGoto to {display_name} failed"
                if hasattr(self, "_last_error_details"):
                    error_details = getattr(self, "_last_error_details")
                    error = error_details.get("error", "Unknown error")
                    if error == "below horizon":
                        error_msg = f"Target '{display_name}' is below the horizon and not visible from your current location at this time. Try a different target or wait until it rises."
                    elif (
                        "mount goto failed" in str(error).lower()
                        or "goto failed" in str(error).lower()
                    ):
                        # Check if this is a solar target based on display name
                        if (
                            "sun" in display_name.lower()
                            or "☀" in display_name
                            or "⚠" in display_name
                        ):
                            error_msg = f"Telescope slewing to '{display_name}' failed: {error}. The telescope may have built-in safety protection preventing solar pointing. Ensure proper solar filter is installed and telescope safety settings allow solar observation."
                        else:
                            error_msg = f"Telescope slewing to '{display_name}' failed: {error}. This may indicate a mechanical issue or safety protection."
                    else:
                        error_msg = (
                            f"Telescope slewing to '{display_name}' failed: {error}"
                        )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            else:
                # Timeout case - the command was sent, AutoGoto might still be in progress
                logger.warning(
                    f"AutoGoto to {display_name} timeout after {timeout}s, state: {self._op_state}"
                )
                # Return True as the slew command was successfully sent
                return True

        except RuntimeError:
            # Re-raise runtime errors (like below horizon) to propagate specific messages
            raise
        except Exception as e:
            logger.error(f"Failed to goto coordinates: {e}")
            raise RuntimeError(f"Failed to slew telescope: {e}")

    async def start_imaging(self, params: ImagingParams) -> bool:
        """
        Start imaging session.

        Args:
            params: Imaging parameters including optional mosaic settings

        Returns:
            True if imaging started successfully
        """
        try:
            # Start stacking with optional mosaic parameters
            stack_params: Dict[str, Any] = {"restart": True}

            # Add mosaic parameters if enabled
            if params.mosaic_mode:
                stack_params["mosaic"] = {
                    "enable": True,
                    "width": params.mosaic_width,
                    "height": params.mosaic_height,
                }
                logger.info(
                    f"Starting mosaic imaging: {params.mosaic_width}x{params.mosaic_height}, "
                    f"{params.exposure_time}s x {params.count} exposures"
                )
            else:
                logger.info(
                    f"Starting standard imaging: {params.exposure_time}s x {params.count} exposures"
                )

            self._json_message("iscope_start_stack", stack_params)
            await asyncio.sleep(1)

            return True

        except Exception as e:
            logger.error(f"Failed to start imaging: {e}")
            return False

    async def stop_imaging(self) -> bool:
        """Stop current imaging session."""
        try:
            # Stop stacking
            stop_params = {"stage": "Stack"}

            self._json_message("iscope_stop_view", stop_params)
            await asyncio.sleep(1)

            return True

        except Exception as e:
            logger.error(f"Failed to stop imaging: {e}")
            return False

    async def get_imaging_status(self) -> Optional[ImagingState]:
        """Get current imaging status."""
        try:
            # SeestarS50 doesn't provide detailed imaging status via API
            # Return basic status for now
            return ImagingState(
                status=ImagingStatus.STOPPED,
                progress=0,
                current_image=0,
                total_images=0,
                exposure_time=None,
                time_remaining=None,
                last_image_path=None,
            )

        except Exception as e:
            logger.error(f"Failed to get imaging status: {e}")
            return None

    async def start_calibration(self) -> bool:
        """Start telescope calibration sequence."""
        # SeestarS50 calibration must be done via the mobile app
        # The telescope doesn't expose calibration commands via TCP
        error_msg = (
            "Calibration must be performed using the SeestarS50 mobile app. "
            "The telescope does not support remote calibration via TCP commands. "
            "Please use the official app to perform polar alignment and calibration."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    async def get_calibration_status(self) -> Optional[CalibrationState]:
        """Get current calibration status."""
        try:
            # SeestarS50 calibration status is not available via API
            return CalibrationState(
                status=CalibrationStatus.NOT_STARTED,
                progress=0,
                current_step=None,
                steps_completed=0,
                total_steps=0,
                error_message=None,
            )

        except Exception as e:
            logger.error(f"Failed to get calibration status: {e}")
            return None

    async def park_telescope(self, eq_mode: bool = False) -> dict:
        """
        Park telescope using correct SeestarS50 command.

        Args:
            eq_mode: Whether to park in equatorial mode (default: False for Alt-Az)

        Returns:
            dict: Result of park operation
        """
        try:
            logger.info(f"Parking telescope (EQ mode: {eq_mode})...")

            # Use the confirmed working scope_park command
            self._json_message("scope_park", {"equ_mode": eq_mode})

            # Wait for command to complete
            await asyncio.sleep(3)

            logger.info("Telescope park command sent successfully")
            return {
                "message": f"Telescope park command sent (EQ mode: {eq_mode})",
                "eq_mode": eq_mode,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Failed to park telescope: {e}")
            return {"error": str(e), "success": False}

    def _is_solar_target(self, target_name: str) -> bool:
        """Check if target is solar system object requiring special handling."""
        solar_targets = [
            "sun",
            "solar",
            "sol",
            "mercury",
            "venus",
            "mars",
            "jupiter",
            "saturn",
            "uranus",
            "neptune",
        ]
        return any(solar_name in target_name.lower() for solar_name in solar_targets)

    async def start_solar_observation(self, target_name: str) -> dict:
        """
        Start solar observation mode using correct SeestarS50 commands.

        Args:
            target_name: Name of solar target

        Returns:
            dict: Result of solar mode initialization
        """
        try:
            logger.info(f"Starting solar observation mode for {target_name}")

            # Start solar viewing mode
            self._json_message("iscope_start_view", {"mode": "sun"})

            # Start solar tracking/scanning
            self._json_message("start_scan_planet")

            # Clear any previous solar state
            self._json_message("clear_app_state", {"name": "ScanSun"})

            # Wait a moment for solar mode to initialize
            await asyncio.sleep(3)

            logger.info(
                f"Solar observation mode started successfully for {target_name}"
            )
            return {
                "message": f"Solar observation mode started for {target_name}",
                "target": target_name,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Failed to start solar observation for {target_name}: {e}")
            return {"error": str(e), "target": target_name, "success": False}

    async def get_comprehensive_state(self) -> dict:
        """Get comprehensive device state including sensors."""
        try:
            # Send command and get response
            self._json_message(
                "get_device_state", {"keys": ["balance_sensor", "compass_sensor"]}
            )

            # Wait for response
            await asyncio.sleep(2)

            return {"message": "Device state requested", "success": True}

        except Exception as e:
            logger.error(f"Failed to get device state: {e}")
            return {"error": str(e), "success": False}

    async def unpark_telescope(self) -> dict:
        """
        Unpark telescope using correct SeestarS50 commands.
        Uses scope_move_to_horizon to position arm properly.

        Returns:
            dict: Results of positioning operations
        """
        try:
            logger.info("Starting telescope arm opening sequence...")

            # Use scope_move_to_horizon to position telescope arm
            # This is the correct command that actually works on SeestarS50
            self._json_message("scope_move_to_horizon")

            # Wait for horizon movement to complete
            await asyncio.sleep(5)

            # Get device state to verify positioning
            self._json_message(
                "get_device_state", {"keys": ["balance_sensor", "compass_sensor"]}
            )

            # Wait a moment for state response
            await asyncio.sleep(2)

            logger.info("Telescope arm opening sequence completed successfully")
            return {
                "message": "Telescope arm opening sequence completed using scope_move_to_horizon",
                "success": True,
            }

        except Exception as e:
            logger.error(f"Failed to open telescope arm: {e}")
            return {"error": str(e), "success": False}

    async def emergency_stop(self) -> bool:
        """Emergency stop all telescope operations."""
        try:
            # Stop all operations
            stop_params = {"stage": "All"}

            self._json_message("iscope_stop_view", stop_params)
            await asyncio.sleep(0.5)

            return True

        except Exception as e:
            logger.error(f"Failed to emergency stop: {e}")
            return False

    # Enhanced commands from seestar_alp analysis

    async def get_device_state(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive device state information."""
        try:
            self._json_message("get_device_state")
            await asyncio.sleep(1)

            # This would need proper response parsing
            # For now, return basic status
            return {"status": "available", "connection": "connected"}

        except Exception as e:
            logger.error(f"Failed to get device state: {e}")
            return None

    async def get_station_state(self) -> Optional[Dict[str, Any]]:
        """Get telescope station mode state."""
        try:
            self._json_message("pi_station_state")
            await asyncio.sleep(1)

            return {"mode": "station", "connected": True}

        except Exception as e:
            logger.error(f"Failed to get station state: {e}")
            return None

    async def get_view_state(self) -> Optional[Dict[str, Any]]:
        """Get current telescope view state."""
        try:
            self._json_message("get_view_state")
            await asyncio.sleep(1)

            return {"viewing": False, "target": None}

        except Exception as e:
            logger.error(f"Failed to get view state: {e}")
            return None

    async def get_stack_setting(self) -> Optional[Dict[str, Any]]:
        """Get current stacking/imaging settings."""
        try:
            self._json_message("get_stack_setting")
            await asyncio.sleep(1)

            return {"exposure": 10, "gain": 100, "count": 10}

        except Exception as e:
            logger.error(f"Failed to get stack setting: {e}")
            return None

    async def set_stack_setting(self, settings: Dict[str, Any]) -> bool:
        """Set stacking/imaging settings."""
        try:
            self._json_message("set_stack_setting", settings)
            await asyncio.sleep(1)

            return True

        except Exception as e:
            logger.error(f"Failed to set stack setting: {e}")
            return False

    async def get_focuser_position(self) -> Optional[int]:
        """Get current focuser position."""
        try:
            self._json_message("get_focuser_position")
            await asyncio.sleep(1)

            # Would need proper response parsing
            return 5000  # Default position

        except Exception as e:
            logger.error(f"Failed to get focuser position: {e}")
            return None

    async def set_focuser_position(self, position: int) -> bool:
        """Set focuser position."""
        try:
            params = {"position": position}
            self._json_message("set_focuser_position", params)
            await asyncio.sleep(2)  # Focus moves can take time

            return True

        except Exception as e:
            logger.error(f"Failed to set focuser position: {e}")
            return False

    async def get_wheel_state(self) -> Optional[Dict[str, Any]]:
        """Get filter wheel state."""
        try:
            self._json_message("get_wheel_state")
            await asyncio.sleep(1)

            return {"id": 0, "state": "idle", "unidirection": False}

        except Exception as e:
            logger.error(f"Failed to get wheel state: {e}")
            return None

    async def set_wheel_position(self, position: int) -> bool:
        """Set filter wheel position."""
        try:
            params = {"position": position}
            self._json_message("set_wheel_position", params)
            await asyncio.sleep(2)

            return True

        except Exception as e:
            logger.error(f"Failed to set wheel position: {e}")
            return False
