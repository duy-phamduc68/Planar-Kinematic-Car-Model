# ─────────────────────────────────────────────────────────────────────────────
# Module: longitudinal.long3
# Path: model6/longitudinal/long3.py
# Purpose: Long.3 drivetrain + load transfer longitudinal model.
# ─────────────────────────────────────────────────────────────────────────────

import math

from constants import M, C_RR, C_DRAG, C_BRAKING
from longitudinal.base import BaseLongitudinalEngine


def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


class Long3Engine(BaseLongitudinalEngine):
    """Long.3: geared drivetrain with torque curve and longitudinal load transfer."""

    engine_id = 3
    label = "Long.3"
    placeholder = False

    def __init__(self):
        super().__init__()

        # Core resistive/vehicle parameters (kept compatible with model6 sync hooks)
        self.M = M
        self.C_RR = C_RR
        self.C_DRAG = C_DRAG
        self.C_BRAKING = C_BRAKING
        self.g = 9.81

        # Wheelbase is synchronized by Vehicle2D; b/c are kept as fixed CG ratios of L.
        self.L = 2.8
        self.h = 0.5
        self._b_ratio = 1.7 / 2.8  # CG -> front axle as a fraction of wheelbase
        self._c_ratio = 1.1 / 2.8  # CG -> rear axle as a fraction of wheelbase
        self.b = self.L * self._b_ratio
        self.c = self.L * self._c_ratio

        # Drivetrain / engine map (model3 reference defaults)
        self.R_W = 0.33
        self.FINAL_DRIVE = 3.42
        self.ETA = 0.7
        self.GEAR_RATIOS = {
            -1: 3.166,
            0: 0.0,
            1: 2.97,
            2: 2.07,
            3: 1.43,
            4: 1.00,
            5: 0.84,
        }
        self.RPM_IDLE = 800.0
        self.RPM_REDLINE = 6000.0
        self.TORQUE_CURVE = [
            (800.0, 200.0),
            (1000.0, 250.0),
            (2000.0, 320.0),
            (3000.0, 380.0),
            (4000.0, 400.0),
            (5000.0, 380.0),
            (6000.0, 300.0),
        ]
        self.upshift_rpm = 5200.0
        self.downshift_rpm = 2200.0
        self.enable_auto_shift = True
        self.rev_limiter_active = False
        self.rev_limiter_release_delta = 180.0

        self.gear = 1
        self.rpm = self.RPM_IDLE
        self.wheel_omega = 0.0
        self.wheel_angle = 0.0

        # Derived load-transfer state
        self.W = 0.0
        self.dW = 0.0
        self.Wf_static = 0.0
        self.Wr_static = 0.0
        self.Wf = 0.0
        self.Wr = 0.0

        # Last-step telemetry values
        self.last_a = 0.0
        self.last_f_engine = 0.0
        self.last_f_rr = 0.0
        self.last_f_drag = 0.0
        self.last_f_brake = 0.0
        self.last_t_engine = 0.0
        self.last_t_wheel = 0.0

        # Display stabilizers to avoid rapid telemetry flicker.
        self._rpm_display = self.RPM_IDLE
        self._wheel_omega_display = 0.0

        self._update_force_hint()
        self._update_load_state(0.0)

    def _sync_cg_geometry(self):
        self.L = max(0.5, float(self.L))
        self.b = self.L * self._b_ratio
        self.c = self.L * self._c_ratio

    def _update_force_hint(self):
        peak_torque = max((tq for _rpm, tq in self.TORQUE_CURVE), default=0.0)
        first = abs(float(self.GEAR_RATIOS.get(1, 0.0)))
        self.F_ENGINE_MAX = (peak_torque * first * self.FINAL_DRIVE * self.ETA) / max(self.R_W, 1e-6)

    def _torque_at_rpm(self, rpm):
        curve = sorted((float(r), float(t)) for r, t in self.TORQUE_CURVE)
        if not curve:
            return 0.0
        if rpm <= curve[0][0]:
            return curve[0][1]
        if rpm >= curve[-1][0]:
            return curve[-1][1]
        for i in range(len(curve) - 1):
            r1, t1 = curve[i]
            r2, t2 = curve[i + 1]
            if r1 <= rpm <= r2:
                k = (rpm - r1) / max(1e-9, (r2 - r1))
                return t1 + k * (t2 - t1)
        return 0.0

    def _apply_auto_shift_hysteresis(self):
        if not self.enable_auto_shift:
            return

        if self.gear < 1:
            return

        up = float(self.upshift_rpm)
        down = float(self.downshift_rpm)
        if down >= up:
            down = up - 200.0

        max_fwd_gear = max((g for g in self.GEAR_RATIOS.keys() if g > 0), default=5)
        if self.rpm > up and self.gear < max_fwd_gear:
            self.gear += 1
        elif self.rpm < down and self.gear > 1:
            self.gear -= 1

    def _update_load_state(self, a):
        self._sync_cg_geometry()
        self.W = self.M * self.g
        self.dW = (self.h / max(self.L, 1e-6)) * self.M * a
        self.Wf_static = (self.c / max(self.L, 1e-6)) * self.W
        self.Wr_static = (self.b / max(self.L, 1e-6)) * self.W
        self.Wf = self.Wf_static - self.dW
        self.Wr = self.Wr_static + self.dW

    def _update_rev_limiter(self):
        release_rpm = self.RPM_REDLINE - max(10.0, float(self.rev_limiter_release_delta))
        if self.rev_limiter_active:
            if self.rpm <= release_rpm:
                self.rev_limiter_active = False
            return
        if self.rpm >= self.RPM_REDLINE:
            self.rev_limiter_active = True

    @staticmethod
    def _smooth(prev, target, alpha):
        alpha = _clamp(float(alpha), 0.0, 1.0)
        return prev + alpha * (target - prev)

    def reset(self):
        self.v = 0.0
        self.gear = 1
        self.rpm = self.RPM_IDLE
        self.wheel_omega = 0.0
        self.wheel_angle = 0.0
        self.last_a = 0.0
        self.last_f_engine = 0.0
        self.last_f_rr = 0.0
        self.last_f_drag = 0.0
        self.last_f_brake = 0.0
        self.last_t_engine = 0.0
        self.last_t_wheel = 0.0
        self.rev_limiter_active = False
        self._rpm_display = self.RPM_IDLE
        self._wheel_omega_display = 0.0
        self._update_load_state(0.0)

    def update(self, dt, throttle, brake):
        throttle = _clamp(float(throttle), 0.0, 1.0)
        brake = _clamp(float(brake), 0.0, 1.0)

        self._sync_cg_geometry()
        self._apply_auto_shift_hysteresis()

        v_prev = self.v
        omega_wheel = v_prev / max(self.R_W, 1e-6)
        gear_ratio = float(self.GEAR_RATIOS.get(self.gear, 0.0))

        if self.gear == 0:
            rpm = self.RPM_IDLE
        else:
            rpm = abs(omega_wheel * gear_ratio * self.FINAL_DRIVE * 60.0 / (2.0 * math.pi))
            rpm = max(rpm, self.RPM_IDLE)
        self.rpm = rpm
        self._update_rev_limiter()

        if self.rev_limiter_active:
            t_engine = 0.0
        else:
            t_engine = throttle * self._torque_at_rpm(self.rpm)

        t_wheel = t_engine * gear_ratio * self.FINAL_DRIVE * self.ETA
        f_engine = t_wheel / max(self.R_W, 1e-6)

        if self.gear < 0:
            f_engine = -f_engine
        if self.gear > 0 and v_prev < -0.1:
            f_engine = 0.0
        if self.gear < 0 and v_prev > 0.1:
            f_engine = 0.0

        f_rr = self.C_RR * v_prev
        f_drag = self.C_DRAG * v_prev * abs(v_prev)

        if abs(v_prev) > 1e-6:
            f_brake = self.C_BRAKING * brake * math.copysign(1.0, v_prev)
        else:
            f_brake = 0.0

        f_net = f_engine - f_rr - f_drag - f_brake
        a = f_net / max(self.M, 1e-6)

        self.v = v_prev + dt * a
        if brake > 0.0 and v_prev * self.v < 0.0:
            self.v = 0.0
        if abs(self.v) < 0.03 and abs(throttle) < 0.03:
            self.v = 0.0
        if abs(self.v) < 0.15 and brake > 0.05 and abs(throttle) < 0.08:
            self.v = 0.0

        self.wheel_omega = self.v / max(self.R_W, 1e-6)
        self.wheel_angle = (self.wheel_angle + self.wheel_omega * dt) % (2.0 * math.pi)

        self.last_a = a
        self.last_f_engine = f_engine
        self.last_f_rr = f_rr
        self.last_f_drag = f_drag
        self.last_f_brake = f_brake
        self.last_t_engine = t_engine
        self.last_t_wheel = t_wheel

        self._rpm_display = self._smooth(self._rpm_display, self.rpm, 0.25)
        self._wheel_omega_display = self._smooth(self._wheel_omega_display, self.wheel_omega, 0.30)

        self._update_load_state(a)
        return self.v

    def _gear_text(self):
        if self.gear < 0:
            return "R"
        if self.gear == 0:
            return "N"
        return str(self.gear)

    def _slip_text(self):
        speed = abs(self.v)
        if speed < 0.5:
            return "N/A"
        wheel_v = abs(self.wheel_omega * self.R_W)
        slip = 100.0 * (wheel_v - speed) / max(speed, 1e-6)
        return f"{slip:+.1f}%"

    def _traction_text(self):
        if abs(self.v) < 0.2:
            return "N/A"
        # Reference-style placeholder estimate: used force vs. rear normal load.
        ratio = 100.0 * abs(self.last_f_engine) / max(abs(self.Wr), 1e-6)
        return f"{ratio:.1f}%"

    def get_hud_data(self):
        slip_txt = self._slip_text()
        brake_torque = self.last_f_brake * self.R_W
        return {
            "mode_label": self.label,
            "gear": self._gear_text(),
            "rpm": f"{self._rpm_display:.0f}",
            "rpm_idle": self.RPM_IDLE,
            "rpm_redline": self.RPM_REDLINE,
            "shift": "AUTO" if self.enable_auto_shift else "MANUAL",
            "slip": slip_txt,
            "traction": self._traction_text(),
            "placeholder": self.placeholder,
            # Extended telemetry payload for model6 HUD placeholders
            "ax": f"{self.last_a:.2f}",
            "ay": "N/A",
            "slip_fl": "N/A",
            "slip_fr": "N/A",
            "slip_rl": "N/A",
            "slip_rr": "N/A",
            "engine_torque": f"{self.last_t_engine:.1f}",
            "wheel_torque": f"{self.last_t_wheel:.1f}",
            "fz_front": f"{self.Wf:.0f}",
            "fz_rear": f"{self.Wr:.0f}",
            "wheel_omega": self._wheel_omega_display,
            "wheel_radius_m": self.R_W,
            "wheel_angle": self.wheel_angle,
            "f_traction": f"{self.last_f_engine:.1f}",
            "f_drag": f"{self.last_f_drag:.1f}",
            "f_rr": f"{self.last_f_rr:.1f}",
            "f_net": f"{(self.last_f_engine - self.last_f_rr - self.last_f_drag - self.last_f_brake):.1f}",
            "slip_ratio": "N/A",
            "wheel_alpha": "N/A",
            "t_drive": f"{self.last_t_wheel:.1f}",
            "t_brake": f"{brake_torque:.1f}",
            "t_traction": "N/A",
            "t_net": f"{(self.last_t_wheel - brake_torque):.1f}",
        }
