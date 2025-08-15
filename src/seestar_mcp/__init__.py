"""SeestarS50 MCP Server package."""

__version__ = "0.2.0-beta.0"
__author__ = "David Perez"
__email__ = "david.perez@tacoops.io"
__description__ = "MCP server for controlling SeestarS50 telescope"

from .server import create_server, main

__all__ = ["create_server", "main"]
