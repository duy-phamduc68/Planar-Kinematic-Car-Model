# ─────────────────────────────────────────────────────────────────────────────
# Module: longitudinal.base
# Path: model6/longitudinal/base.py
# Purpose: Base interface for longitudinal engine models.
# ─────────────────────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod


class BaseLongitudinalEngine(ABC):
    """Minimal contract for longitudinal models used by Vehicle2D."""

    def __init__(self):
        self.v = 0.0

    @abstractmethod
    def reset(self):
        """Reset internal state to initial values."""

    @abstractmethod
    def update(self, dt, throttle, brake):
        """Advance engine state and return current longitudinal speed."""
