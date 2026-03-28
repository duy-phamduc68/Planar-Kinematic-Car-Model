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
    placeholder = False

    def __init__(self):
        super().__init__()
        self.M = M
        self.F_ENGINE_MAX = F_ENGINE_MAX
        self.C_RR = C_RR
        self.C_DRAG = C_DRAG
        self.C_BRAKING = C_BRAKING
        self.last_a = 0.0
        self.last_f_engine = 0.0
        self.last_f_rr = 0.0
        self.last_f_drag = 0.0
        self.last_f_brake = 0.0
        self.last_f_net = 0.0

    def reset(self):
        self.v = 0.0
        self.last_a = 0.0
        self.last_f_engine = 0.0
        self.last_f_rr = 0.0
        self.last_f_drag = 0.0
        self.last_f_brake = 0.0
        self.last_f_net = 0.0

    def update(self, dt, throttle, brake):
        f_engine = throttle * self.F_ENGINE_MAX
        f_rr = self.C_RR * self.v
        f_drag = self.C_DRAG * self.v * abs(self.v)
        f_brake = self.C_BRAKING * brake if self.v > 0 else 0

        f_net = f_engine - f_rr - f_drag - f_brake
        a = f_net / self.M
        self.v = max(0.0, self.v + dt * a)

        self.last_a = a
        self.last_f_engine = f_engine
        self.last_f_rr = f_rr
        self.last_f_drag = f_drag
        self.last_f_brake = f_brake
        self.last_f_net = f_net
        return self.v

    def get_hud_data(self):
        return {
            "mode_label": self.label,
            "gear": "N/A",
            "rpm": "N/A",
            "shift": "AUTO",
            "slip": "N/A",
            "traction": "N/A",
            "placeholder": self.placeholder,
            "ax": f"{self.last_a:.2f}",
            "ay": "N/A",
            "f_traction": f"{self.last_f_engine:.1f}",
            "f_drag": f"{self.last_f_drag:.1f}",
            "f_rr": f"{self.last_f_rr:.1f}",
            "f_net": f"{self.last_f_net:.1f}",
            "slip_ratio": "N/A",
            "wheel_omega": "N/A",
            "wheel_alpha": "N/A",
            "t_drive": "N/A",
            "t_brake": f"{self.last_f_brake:.1f}",
            "t_traction": "N/A",
            "t_net": "N/A",
            "engine_torque": "N/A",
            "wheel_torque": "N/A",
            "fz_front": "N/A",
            "fz_rear": "N/A",
        }
