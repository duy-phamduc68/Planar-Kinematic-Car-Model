# ─────────────────────────────────────────────────────────────────────────────
# Module: longitudinal.long1
# Path: model6/longitudinal/long1.py
# Purpose: Long.1 linear longitudinal engine implementation.
# ─────────────────────────────────────────────────────────────────────────────

from constants import M, F_ENGINE_MAX, C_RR, C_DRAG, C_BRAKING
from longitudinal.base import BaseLongitudinalEngine


class Long1Engine(BaseLongitudinalEngine):
    """Long.1: linear force, no gears, no wheelspin."""

    engine_id = 1
    label = "Long.1"

    def __init__(self):
        super().__init__()
        self.M = M
        self.F_ENGINE_MAX = F_ENGINE_MAX
        self.C_RR = C_RR
        self.C_DRAG = C_DRAG
        self.C_BRAKING = C_BRAKING

    def reset(self):
        self.v = 0.0

    def update(self, dt, throttle, brake):
        f_engine = throttle * self.F_ENGINE_MAX
        f_rr = self.C_RR * self.v
        f_drag = self.C_DRAG * self.v * abs(self.v)
        f_brake = self.C_BRAKING * brake if self.v > 0 else 0

        f_net = f_engine - f_rr - f_drag - f_brake
        a = f_net / self.M
        self.v = max(0.0, self.v + dt * a)
        return self.v
