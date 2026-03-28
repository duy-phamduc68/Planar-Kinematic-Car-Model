# ─────────────────────────────────────────────────────────────────────────────
# Module: longitudinal.long5
# Path: model6/longitudinal/long5.py
# Purpose: Placeholder for Long.5 longitudinal engine implementation.
# ─────────────────────────────────────────────────────────────────────────────

from longitudinal.base import BaseLongitudinalEngine


class Long5Engine(BaseLongitudinalEngine):
    """Long.5 placeholder engine."""

    engine_id = 5
    label = "Long.5"

    def __init__(self):
        super().__init__()

    def reset(self):
        self.v = 0.0

    def update(self, dt, throttle, brake):
        # Placeholder behavior: keep current speed.
        return self.v
