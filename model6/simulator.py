"""
Car Physics Simulator - Model 6 (Top-Down Kinematics)
=======================================================
Combines Model 1 (Linear Acceleration) with Model 6 (Bicycle Kinematics).
"""

import os
import pygame
from constants import (
    THROTTLE_RAMP_DEFAULT,
    BRAKE_RAMP_DEFAULT,
    STEER_RAMP_DEFAULT,
    GRID_SIZE,
    TIMESTEP_OPTIONS,
    FPS_OPTIONS,
)
from physics import Vehicle2D
from controls import load_xinput, get_xinput_state, XINPUT_BUTTON_START, XINPUT_BUTTON_BACK, XINPUT_BUTTON_DPAD_UP, XINPUT_BUTTON_DPAD_DOWN
from renderer import draw_skidpad, draw_car_topdown, draw_trajectory, draw_hud_planar
from ui import OptionsMenu, CheckBox


def _parse_scalar(val):
    try:
        return float(val.strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _parse_bool(val):
    if val is None:
        return None
    txt = str(val).strip().lower()
    if txt in ("true", "1", "yes", "on"):
        return True
    if txt in ("false", "0", "no", "off"):
        return False
    return None


def _load_global_settings():
    """Read startup settings from global config with safe fallbacks."""
    dt_default = 0.01
    fps_default = 60
    traj_default = True
    true_form_default = False
    cfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))

    cfg_dt = None
    cfg_fps = None
    cfg_traj = None
    cfg_true_form = None
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.split("#", 1)[0].strip()
                if not line or ":" not in line:
                    continue
                key, val = line.split(":", 1)
                key = key.strip().lower()
                if key == "timestep":
                    parsed = _parse_scalar(val)
                    if parsed is None:
                        continue
                    cfg_dt = parsed
                elif key == "fps":
                    parsed = _parse_scalar(val)
                    if parsed is None:
                        continue
                    cfg_fps = parsed
                elif key == "trajectory":
                    cfg_traj = _parse_bool(val)
                elif key == "true_form":
                    cfg_true_form = _parse_bool(val)
    except OSError:
        pass

    dt_options = [dt for dt, _label in TIMESTEP_OPTIONS]
    fps_options = list(FPS_OPTIONS)

    if cfg_dt is None or cfg_dt <= 0:
        dt = dt_default
    else:
        dt = min(dt_options, key=lambda opt: abs(opt - cfg_dt))

    if cfg_fps is None or cfg_fps <= 0:
        fps = fps_default
    else:
        fps = int(min(fps_options, key=lambda opt: abs(opt - cfg_fps)))

    trajectory = traj_default if cfg_traj is None else cfg_traj
    true_form = true_form_default if cfg_true_form is None else cfg_true_form
    return dt, fps, trajectory, true_form

class Simulator:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Car Physics Simulator - Model 6")
        self.screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
        self.screen_w, self.screen_h = self.screen.get_size()

        self.font_sm = pygame.font.SysFont("Consolas", 13)
        self.font_md = pygame.font.SysFont("Consolas", 17, bold=True)
        self.font_lg = pygame.font.SysFont("Consolas", 26, bold=True)

        self.dt, self.target_fps, cfg_trajectory, cfg_true_form = _load_global_settings()
        self.grid_size = GRID_SIZE
        self.throttle_ramp = THROTTLE_RAMP_DEFAULT
        self.steer_ramp = STEER_RAMP_DEFAULT
        self.input_mode = "keyboard"
        
        # Physics Wrapper
        self.car = Vehicle2D(engine_id=1)
        self.sim_time = 0.0
        
        # Camera
        self.zoom = 1.0

        # Analog Inputs
        self.throttle, self.brake, self.steering = 0.0, 0.0, 0.0
        self._w_held, self._s_held, self._a_held, self._d_held = False, False, False, False

        # Input state
        self._xinput_ok = load_xinput()
        self._btns_prev = 0
        self._last_keyboard_input_t = 0.0
        self._last_controller_input_t = 0.0

        # UI Elements
        self._menu_btn = pygame.Rect(8, 8, 110, 30)
        self._true_form_cb = CheckBox(130, 14, "True Form", checked=cfg_true_form)
        self._traj_cb      = CheckBox(260, 14, "Trajectory", checked=cfg_trajectory)
        self.options = OptionsMenu(self)

        self._clock = pygame.time.Clock()
        self._fps_display, self._fps_acc, self._fps_frames = 0.0, 0.0, 0
        self._layout()

    def _layout(self):
        self.scene_rect = pygame.Rect(0, 0, self.screen_w, int(self.screen_h * 0.66))
        self.hud_rect = pygame.Rect(0, self.scene_rect.height, self.screen_w, self.screen_h - self.scene_rect.height)

    def reset_scenario(self):
        self.car.reset()
        self.sim_time, self.throttle, self.brake, self.steering = 0.0, 0.0, 0.0, 0.0

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.VIDEORESIZE:
                self.screen_w, self.screen_h = event.w, event.h
                self._layout()
                self.options._build()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.options.editing_active:
                self.options.toggle(); continue

            # Top UI Overlays
            if event.type == pygame.MOUSEMOTION:
                self._true_form_cb.handle_event(event)
                self._traj_cb.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.options.visible:
                if self._true_form_cb.handle_event(event): continue
                if self._traj_cb.handle_event(event): continue
                if self._menu_btn.collidepoint(event.pos): self.options.toggle(); continue

            if self.options.handle_event(event): continue

            # Keyboard Input
            if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                now = pygame.time.get_ticks() * 0.001
                is_down = (event.type == pygame.KEYDOWN)
                if event.key in (pygame.K_w, pygame.K_UP):
                    self._w_held = is_down
                    if is_down:
                        self._last_keyboard_input_t = now
                if event.key in (pygame.K_SPACE, pygame.K_DOWN, pygame.K_b):
                    self._s_held = is_down
                    if is_down:
                        self._last_keyboard_input_t = now
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self._a_held = is_down
                    if is_down:
                        self._last_keyboard_input_t = now
                if event.key in (pygame.K_d, pygame.K_RIGHT):
                    self._d_held = is_down
                    if is_down:
                        self._last_keyboard_input_t = now

                if is_down:
                    if event.key == pygame.K_2:
                        self.zoom = min(3.0, self.zoom + 0.2)
                        self._last_keyboard_input_t = now
                    if event.key == pygame.K_3:
                        self.zoom = max(0.2, self.zoom - 0.2)
                        self._last_keyboard_input_t = now
                    if event.key == pygame.K_r:
                        self.reset_scenario()
                        self._last_keyboard_input_t = now
        return True

    def _update_input(self, dt):
        now = pygame.time.get_ticks() * 0.001
        xi = get_xinput_state(0)
        rt = lt = steer = 0.0
        btns = 0
        controller_active = False
        if xi is not None:
            rt, lt, steer, btns = xi
            controller_active = (rt > 0.05 or lt > 0.05 or abs(steer) > 0.05 or btns != 0)
            if controller_active:
                self._last_controller_input_t = now

        keyboard_active = (self._w_held or self._s_held or self._a_held or self._d_held)
        if keyboard_active:
            self._last_keyboard_input_t = now

        recent_window = 0.35
        kb_recent = (now - self._last_keyboard_input_t) <= recent_window
        ctrl_recent = (xi is not None) and ((now - self._last_controller_input_t) <= recent_window)

        if kb_recent and not ctrl_recent:
            self.input_mode = "keyboard"
        elif ctrl_recent and not kb_recent:
            self.input_mode = "controller"
        elif kb_recent and ctrl_recent:
            self.input_mode = (
                "keyboard"
                if self._last_keyboard_input_t >= self._last_controller_input_t
                else "controller"
            )
        elif xi is None:
            self.input_mode = "keyboard"

        if xi is not None:
            # Controller buttons (edge detect)
            if (btns & XINPUT_BUTTON_START) and not (self._btns_prev & XINPUT_BUTTON_START):
                if not self.options.editing_active:
                    self.options.toggle()
            if (btns & XINPUT_BUTTON_BACK) and not (self._btns_prev & XINPUT_BUTTON_BACK):
                self.reset_scenario()
            if (btns & XINPUT_BUTTON_DPAD_UP) and not (self._btns_prev & XINPUT_BUTTON_DPAD_UP):
                self.zoom = min(3.0, self.zoom + 0.2)
            if (btns & XINPUT_BUTTON_DPAD_DOWN) and not (self._btns_prev & XINPUT_BUTTON_DPAD_DOWN):
                self.zoom = max(0.2, self.zoom - 0.2)
            self._btns_prev = btns
        else:
            self._btns_prev = 0

        if self.input_mode == "keyboard" or xi is None:
            # Analog Ramps for Keyboard
            tr = 1.0 / max(1e-6, self.throttle_ramp)
            br = 1.0 / BRAKE_RAMP_DEFAULT
            sr = 1.0 / max(1e-6, self.steer_ramp)

            self.throttle = min(1.0, self.throttle + tr*dt) if self._w_held else max(0.0, self.throttle - tr*dt)
            self.brake = min(1.0, self.brake + br*dt) if self._s_held else max(0.0, self.brake - br*dt)

            if self._a_held: self.steering = max(-1.0, self.steering - sr*dt)
            elif self._d_held: self.steering = min(1.0, self.steering + sr*dt)
            else:
                if self.steering > 0: self.steering = max(0.0, self.steering - sr*dt)
                if self.steering < 0: self.steering = min(0.0, self.steering + sr*dt)
        else:
            self.throttle = rt
            self.brake = lt
            self.steering = max(-1.0, min(1.0, steer))

    def run(self):
        running = True
        accumulator = 0.0
        while running:
            frame_dt = min(self._clock.tick(self.target_fps) / 1000.0, 0.1)
            
            self._fps_acc += frame_dt
            self._fps_frames += 1
            if self._fps_acc >= 0.5:
                self._fps_display, self._fps_acc, self._fps_frames = self._fps_frames / self._fps_acc, 0.0, 0

            if (self.screen.get_size() != (self.screen_w, self.screen_h)):
                self.screen_w, self.screen_h = self.screen.get_size(); self._layout()

            running = self._handle_events()
            
            if not self.options.visible:
                self._update_input(frame_dt)
                accumulator += frame_dt
                while accumulator >= self.dt:
                    self.car.update(self.dt, self.throttle, self.brake, self.steering)
                    self.sim_time += self.dt
                    accumulator -= self.dt

            # Drawing Pipeline
            draw_skidpad(self.screen, self.car.x, self.car.y, self.zoom, self.screen_w, self.scene_rect.height, self.grid_size)
            if self._traj_cb.checked: draw_trajectory(self.screen, self.car, self.car.x, self.car.y, self.zoom, self.screen_w, self.scene_rect.height)
            draw_car_topdown(self.screen, self.car, self.car.x, self.car.y, self.zoom, self.screen_w, self.scene_rect.height, self._true_form_cb.checked)
            draw_hud_planar(self.screen, self.hud_rect, self.font_sm, self.font_lg, self.car, self.throttle, self.brake, self.steering, self._fps_display, self.sim_time)
            
            # Top Overlays
            # Menu Btn
            pygame.draw.rect(self.screen, (65, 72, 96) if self._menu_btn.collidepoint(pygame.mouse.get_pos()) else (45, 50, 68), self._menu_btn, border_radius=5)
            pygame.draw.rect(self.screen, (80, 170, 255), self._menu_btn, 1, border_radius=5)
            self.screen.blit(self.font_sm.render("Options", True, (230, 235, 255)), (25, 15))
            # Checkboxes
            self._true_form_cb.draw(self.screen, self.font_sm)
            self._traj_cb.draw(self.screen, self.font_sm)
            # Top-Right Text
            input_src = "Pad" if self.input_mode == "controller" else "KB"
            txt = self.font_sm.render(
                f"FPS: {self._fps_display:.0f} | dt: {self.dt} | Zoom: {self.zoom:.2f}x | Grid: {self.grid_size:.0f}m | Input: {input_src} | Mode: Long.{self.car.engine_id}",
                True,
                (230, 235, 255),
            )
            self.screen.blit(txt, (self.screen_w - txt.get_width() - 10, 10))
            # Top-Center Text
            txt = self.font_sm.render(f"t = {self.sim_time:.1f}s", True, (255, 255, 255))
            self.screen.blit(txt, (self.screen_w//2 - 30, 10))

            self.options.draw(self.screen, self.font_sm, self.font_md)
            pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    Simulator().run()