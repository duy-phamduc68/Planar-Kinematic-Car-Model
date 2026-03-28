# ─────────────────────────────────────────────────────────────────────────────
# renderer.py — Top-Down 2D Renderer and Simcade HUD
# ─────────────────────────────────────────────────────────────────────────────

import math
import pygame
from constants import (ROAD_COLOR, ROAD_LINE, CAR_BODY, CAR_WHEEL, GRAPH_BG, GRAPH_GRID, 
                       PANEL_BG, TEXT_BRIGHT, TEXT_DIM, TEXT_DISABLED, ACCENT, PIXELS_PER_METER)

def _transform(wx, wy, cx, cy, zoom, sw, sh):
    """World coordinates to screen pixels."""
    ppm = PIXELS_PER_METER * zoom
    sx = int((wx - cx) * ppm + sw / 2)
    sy = int(-(wy - cy) * ppm + sh / 2) # Y is inverted in Pygame
    return sx, sy

def draw_skidpad(surface, cx, cy, zoom, sw, sh, grid_size_m):
    surface.fill(ROAD_COLOR)
    ppm = PIXELS_PER_METER * zoom
    grid_px = max(1.0, grid_size_m * ppm)
    
    offset_x = (cx * ppm - sw/2) % grid_px
    offset_y = (-cy * ppm - sh/2) % grid_px

    for x in range(int(-offset_x), sw, int(grid_px)):
        pygame.draw.line(surface, ROAD_LINE, (x, 0), (x, sh), 1)
    for y in range(int(-offset_y), sh, int(grid_px)):
        pygame.draw.line(surface, ROAD_LINE, (0, y), (sw, y), 1)

def draw_trajectory(surface, car, cx, cy, zoom, sw, sh):
    """Draws the predicted kinematic path for the next 3 seconds."""
    pts = []
    sim_x, sim_y, sim_h = car.x, car.y, car.heading
    v, delta, L = car.v, car.steering_angle, car.L
    approx_car_len = max(0.1, L * 1.75)
    max_path_len = 3.0 * approx_car_len
    traced_len = 0.0
    
    dt = 0.1
    for _ in range(30):
        prev_x, prev_y = sim_x, sim_y
        yaw_rate = (v * math.sin(delta)) / L if abs(delta) > 0.001 else 0.0
        sim_h += yaw_rate * dt
        sim_x += v * math.cos(sim_h) * dt
        sim_y += v * math.sin(sim_h) * dt

        step_len = math.hypot(sim_x - prev_x, sim_y - prev_y)
        if traced_len + step_len > max_path_len and step_len > 1e-9:
            t = (max_path_len - traced_len) / step_len
            sim_x = prev_x + (sim_x - prev_x) * t
            sim_y = prev_y + (sim_y - prev_y) * t
            sx, sy = _transform(sim_x, sim_y, cx, cy, zoom, sw, sh)
            pts.append((sx, sy))
            break

        traced_len += step_len
        sx, sy = _transform(sim_x, sim_y, cx, cy, zoom, sw, sh)
        pts.append((sx, sy))
        if traced_len >= max_path_len:
            break
        
    if len(pts) > 1:
        pygame.draw.lines(surface, (255, 255, 0), False, pts, 2)

def draw_car_topdown(surface, car, cx, cy, zoom, sw, sh, true_form):
    ppm = PIXELS_PER_METER * zoom
    
    # Bicycle Model anchors
    rear_x, rear_y = car.x, car.y 
    front_x = rear_x + car.L * math.cos(car.heading)
    front_y = rear_y + car.L * math.sin(car.heading)
    
    rsx, rsy = _transform(rear_x, rear_y, cx, cy, zoom, sw, sh)
    fsx, fsy = _transform(front_x, front_y, cx, cy, zoom, sw, sh)

    if true_form:
        # 1. Bicycle Frame
        pygame.draw.line(surface, (255, 255, 255), (rsx, rsy), (fsx, fsy), 3)
        
        # 2. Wheels
        w_len = int(0.4 * ppm)
        # Rear Wheel
        dx, dy = math.cos(car.heading) * w_len, -math.sin(car.heading) * w_len
        pygame.draw.line(surface, (255, 50, 50), (rsx - dx, rsy - dy), (rsx + dx, rsy + dy), 6)
        # Front Wheel (Rotated by steering angle!)
        fh = car.heading + car.steering_angle
        fdx, fdy = math.cos(fh) * w_len, -math.sin(fh) * w_len
        pygame.draw.line(surface, (50, 255, 50), (fsx - fdx, fsy - fdy), (fsx + fdx, fsy + fdy), 6)
        
        # 3. ICR (Instantaneous Center of Rotation)
        if abs(car.steering_angle) > 0.01:
            R_rear = car.L / math.tan(car.steering_angle)
            icr_x = rear_x - R_rear * math.sin(car.heading)
            icr_y = rear_y + R_rear * math.cos(car.heading)
            icrx_s, icry_s = _transform(icr_x, icr_y, cx, cy, zoom, sw, sh)
            
            pygame.draw.line(surface, (100, 100, 100), (rsx, rsy), (icrx_s, icry_s), 1)
            pygame.draw.line(surface, (100, 100, 100), (fsx, fsy), (icrx_s, icry_s), 1)
            pygame.draw.circle(surface, (255, 255, 0), (int(icrx_s), int(icry_s)), 5)
            
    else:
        # Standard Chassis Box with symmetric wheel placement and slight front bias
        wheelbase_m = max(0.1, car.L)
        front_overhang_m = 0.35
        rear_overhang_m = 0.25
        body_len_m = wheelbase_m + front_overhang_m + rear_overhang_m

        body_l = max(12, int(body_len_m * ppm))
        body_w = max(8, int(2.0 * ppm))
        car_surf = pygame.Surface((body_l, body_w), pygame.SRCALPHA)
        pygame.draw.rect(car_surf, CAR_BODY, (0, 0, body_l, body_w), border_radius=4)

        # Front window marker to clearly indicate heading direction.
        win_w = max(3, int(0.12 * body_l))
        win_h = max(4, int(0.62 * body_w))
        win_x = int(body_l * 0.70) - (win_w // 2)
        win_y = (body_w - win_h) // 2
        pygame.draw.rect(car_surf, (130, 210, 255), (win_x, win_y, win_w, win_h), border_radius=3)
        
        # Draw front wheels slightly turned
        w_l = max(4, int(0.7 * ppm))
        w_w = max(2, int(0.3 * ppm))
        fw_surf = pygame.Surface((w_l, w_w), pygame.SRCALPHA)
        fw_surf.fill(CAR_WHEEL)
        fw_rot = pygame.transform.rotate(fw_surf, math.degrees(car.steering_angle))
        
        wheel_margin_y = max(2, int(0.08 * body_w))
        rear_ax_x = int((rear_overhang_m / body_len_m) * body_l)
        front_ax_x = int(((rear_overhang_m + wheelbase_m) / body_len_m) * body_l)

        rear_x = max(0, min(body_l - w_l, rear_ax_x - w_l // 2))
        front_x = max(0, min(body_l - w_l, front_ax_x - w_l // 2))
        top_y = wheel_margin_y
        bot_y = body_w - w_w - wheel_margin_y

        # Position front wheels by axle-center so rotation doesn't bias right.
        front_cx = front_x + (w_l / 2)
        top_cy = top_y + (w_w / 2)
        bot_cy = bot_y + (w_w / 2)
        car_surf.blit(fw_rot, fw_rot.get_rect(center=(front_cx, top_cy)))
        car_surf.blit(fw_rot, fw_rot.get_rect(center=(front_cx, bot_cy)))
        pygame.draw.rect(car_surf, CAR_WHEEL, (rear_x, top_y, w_l, w_w))
        pygame.draw.rect(car_surf, CAR_WHEEL, (rear_x, bot_y, w_l, w_w))

        rotated_car = pygame.transform.rotate(car_surf, math.degrees(car.heading))
        center_from_rear_m = (body_len_m * 0.5) - rear_overhang_m
        center_factor = center_from_rear_m / wheelbase_m
        r_rect = rotated_car.get_rect(center=(rsx + (fsx-rsx)*center_factor, rsy + (fsy-rsy)*center_factor))
        surface.blit(rotated_car, r_rect)

def draw_hud_planar(surface, rect, font_sm, font_lg, car, throttle, brake, steering, fps, sim_t):
    pygame.draw.rect(surface, GRAPH_BG, rect)
    pygame.draw.line(surface, GRAPH_GRID, (rect.x, rect.y), (rect.right, rect.y), 2)
    
    # --- LEFT SIDE: TELEMETRY TEXT ---
    cx, cy = rect.x + 20, rect.y + 20
    is_m1 = car.engine_id == 1
    
    lines = [
        ("Velocity", f"{car.v:.1f} m/s", TEXT_BRIGHT),
        ("Position", f"X: {car.x:.1f}  Y: {car.y:.1f}", TEXT_BRIGHT),
        ("Heading", f"{math.degrees(car.heading)%360:.1f}°", TEXT_BRIGHT),
        ("Yaw Rate", f"{car.yaw_rate:.2f} rad/s", TEXT_BRIGHT),
        ("Slip Angle", "N/A" if is_m1 else "0.0°", TEXT_DISABLED if is_m1 else TEXT_BRIGHT),
        ("Traction", "N/A" if is_m1 else "100%", TEXT_DISABLED if is_m1 else TEXT_BRIGHT),
    ]
    
    for i, (label, val, col) in enumerate(lines):
        surface.blit(font_sm.render(f"{label:12}: {val}", True, col), (cx, cy + i * 22))

    # --- RIGHT SIDE: SIMCADE INPUT HUD ---
    rx = rect.right - 350
    ry = rect.y + 20
    
    # Steering Wheel
    sw_cx, sw_cy, sw_r = rx + 60, ry + 60, 45
    pygame.draw.circle(surface, (40, 40, 40), (sw_cx, sw_cy), sw_r, 6)
    angle = -steering * 90 # Visual representation
    ex = sw_cx + math.sin(math.radians(angle)) * sw_r
    ey = sw_cy - math.cos(math.radians(angle)) * sw_r
    pygame.draw.line(surface, ACCENT, (sw_cx, sw_cy), (ex, ey), 4)
    surface.blit(font_sm.render("STEER", True, TEXT_DIM), (sw_cx - 20, sw_cy + sw_r + 10))

    # Analog Pedals
    bar_w, bar_h = 20, 90
    pygame.draw.rect(surface, (40, 40, 40), (rx + 140, ry, bar_w, bar_h))
    pygame.draw.rect(surface, (40, 40, 40), (rx + 180, ry, bar_w, bar_h))
    pygame.draw.rect(surface, (100, 200, 100), (rx + 140, ry + bar_h - int(throttle*bar_h), bar_w, int(throttle*bar_h)))
    pygame.draw.rect(surface, (200, 100, 100), (rx + 180, ry + bar_h - int(brake*bar_h), bar_w, int(brake*bar_h)))
    surface.blit(font_sm.render("THR", True, TEXT_DIM), (rx + 138, ry + bar_h + 10))
    surface.blit(font_sm.render("BRK", True, TEXT_DIM), (rx + 178, ry + bar_h + 10))

    # Explicit numeric input readouts
    in_x, in_y = rx + 140, ry + bar_h + 32
    steer_deg = math.degrees(car.steering_angle)
    input_lines = [
        f"Throttle: {throttle:.2f}",
        f"Brake:    {brake:.2f}",
        f"Steer:    {steer_deg:+.2f} deg",
    ]
    for i, line in enumerate(input_lines):
        surface.blit(font_sm.render(line, True, TEXT_BRIGHT), (in_x, in_y + i * 18))

    # Engine Data
    ex, ey = rx + 240, ry
    surface.blit(font_lg.render("GEAR", True, TEXT_DISABLED if is_m1 else TEXT_DIM), (ex, ey))
    surface.blit(font_lg.render("N/A" if is_m1 else "1", True, TEXT_DISABLED if is_m1 else TEXT_BRIGHT), (ex + 10, ey + 25))
    
    surface.blit(font_sm.render("RPM:", True, TEXT_DISABLED if is_m1 else TEXT_DIM), (ex, ey + 65))
    surface.blit(font_sm.render("N/A" if is_m1 else "800", True, TEXT_DISABLED if is_m1 else TEXT_BRIGHT), (ex + 35, ey + 65))
    
    surface.blit(font_sm.render("SHIFT: AUTO", True, TEXT_DISABLED if is_m1 else ACCENT), (ex, ey + 85))