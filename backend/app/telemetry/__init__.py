"""Telemetry module for local event collection."""

from app.telemetry.client import TelemetryClient, get_telemetry_client, init_telemetry

__all__ = ["TelemetryClient", "get_telemetry_client", "init_telemetry"]

