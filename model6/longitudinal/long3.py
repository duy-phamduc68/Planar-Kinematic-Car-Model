# ─────────────────────────────────────────────────────────────────────────────
# Module: longitudinal.long3
# Path: model6/longitudinal/long3.py
# Purpose: Placeholder for Long.3 longitudinal engine implementation.
# ─────────────────────────────────────────────────────────────────────────────

from longitudinal.base import BaseLongitudinalEngine


class Long3Engine(BaseLongitudinalEngine):
    """Long.3 placeholder engine."""

    engine_id = 3
    label = "Long.3"

    def __init__(self):
        super().__init__()

    def reset(self):
        self.v = 0.0

    def update(self, dt, throttle, brake):
        # Placeholder behavior: keep current speed.
        return self.v
