# ─────────────────────────────────────────────────────────────────────────────
# physics.py — Vehicle2D wrapper and Longitudinal Engines
# ─────────────────────────────────────────────────────────────────────────────

import math
from constants import L, MAX_STEER
from longitudinal import get_longitudinal_engine, supported_engine_ids

class Vehicle2D:
    """2D Kinematic Bicycle Model wrapper for longitudinal engines."""
    def __init__(self, engine_id=1):
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0        # radians (0 = facing East/Right)
        self.steering_angle = 0.0 # radians (relative to chassis)
        self.yaw_rate = 0.0
        
        self.L = L
        
        if engine_id not in supported_engine_ids():
            engine_id = 1
        self.engine_id = engine_id
        self.engine = get_longitudinal_engine(engine_id)
        
    def reset(self):
        self.x, self.y, self.heading = 0.0, 0.0, 0.0
        self.engine.reset()

    @property
    def v(self): return self.engine.v

    def update(self, dt, throttle, brake, steering_input):
        # 1. Update Steering Angle (capped by MAX_STEER)
        max_steer_rad = math.radians(MAX_STEER)
        self.steering_angle = steering_input * max_steer_rad

        # 2. Get Longitudinal Velocity from Engine
        v = self.engine.update(dt, throttle, brake)

        # 3. Model 6 Kinematics (Bicycle Model Yaw Rate)
        # r = v * sin(delta) / L
        if abs(self.steering_angle) > 0.001:
            self.yaw_rate = (v * math.sin(self.steering_angle)) / self.L
        else:
            self.yaw_rate = 0.0

        # 4. Integrate Heading
        self.heading += self.yaw_rate * dt

        # 5. Transform Local Velocity to World Space
        vx = v * math.cos(self.heading)
        vy = v * math.sin(self.heading)

        # 6. Integrate Position
        self.x += vx * dt
        self.y += vy * dt 

        # Keep attributes in sync for options menu overrides
        if hasattr(self.engine, 'L'): self.engine.L = self.L
        for attr in ['M', 'F_ENGINE_MAX', 'C_RR', 'C_DRAG', 'C_BRAKING']:
            if hasattr(self, attr) and hasattr(self.engine, attr):
                setattr(self.engine, attr, getattr(self, attr))