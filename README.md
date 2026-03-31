# Planar Kinematic Car Model

Main reference: [Macro Monster's Car Physics Guide](https://www.asawicki.info/Mirror/Car%20Physics%20for%20Games/Car%20Physics%20for%20Games.html)

Check out the learning journey on my blog: [yuk068.github.io](https://yuk068.github.io/)

**Model 1-5** (Longitudinal Simulators) are in this repository: [duy-phamduc68/Longitudinal-Car-Physics](https://github.com/duy-phamduc68/Longitudinal-Car-Physics)

I try to break down each model both mathematically (continuous math) and implement them in code.

This repository contains code for **Model 6** of the roadmap.

## Model 6: Low-Speed Kinematic Turning (2D)

![thumbnail](/media/thumbnail.png)

[Technical Breakdown](https://yuk068.github.io/2026/03/26/car-physics-model6)

### Overview

This simulator combines a 2D kinematic bicycle model with interchangeable longitudinal powertrain models so you can compare increasing levels of drivetrain realism under the same steering/turning framework.

At runtime, the vehicle state is integrated in fixed-timestep updates, while rendering and input are decoupled for stable behavior across different frame rates.

Technical highlights:

- **Planar vehicle core (Model 6):** low-speed bicycle kinematics for heading and yaw-rate evolution in world coordinates.
- **Swappable longitudinal engines:**
    - **Long.1:** point-mass force balance (engine, rolling resistance, drag, braking).
    - **Long.3:** torque-curve + gearing model with drivetrain mapping and load transfer terms.
    - **Long.5:** wheel rotational dynamics, slip-ratio traction saturation, and traction-limited acceleration behavior.
- **Preset-driven tuning:** `presets.json` applies shared and engine-specific constants (mass, drag, gearing, torque curves, CG geometry, optional hybrid assist).
- **Global configuration settting:** `config.yaml` serves as the entry to tune various default settings, including selecting the default preset.
- **Unified telemetry/HUD:** one consistent dashboard across engines, with unsupported channels shown as disabled.
- **Interactive tooling:** keyboard/XInput control paths, runtime options panel, trajectory visualization, timer, and resettable scenarios for repeatable testing.

The goal is to keep the simulator educational and inspectable: each model layer maps directly to equations and assumptions discussed in the technical breakdown.

### Input Guide

This guide lists all simulator controls. It replaces the in-simulator input guide popup.

#### Keyboard Controls

| Key(s)                            | Action                                        |
| --------------------------------- | --------------------------------------------- |
| `W` / `Up`                        | Throttle                                      |
| `Space` / `Down` / `S` / `LShift` | Brake                                         |
| `A` / `Left`                      | Steer left                                    |
| `D` / `Right`                     | Steer right                                   |
| `J`                               | Downshift                                     |
| `K`                               | Upshift                                       |
| `1`                               | Toggle auto shift                             |
| `2`                               | Zoom in                                       |
| `3`                               | Zoom out                                      |
| `4`                               | Toggle trajectory                             |
| `5`                               | Toggle true form                              |
| `Q`                               | Timer cycle (idle → running → stopped → idle) |
| `R`                               | Reset scenario                                |
| `Esc`                             | Open/close options                            |

#### Xbox Controller (XInput)

| Control           | Action                                        |
| ----------------- | --------------------------------------------- |
| `RT`              | Throttle                                      |
| `LT`              | Brake                                         |
| `Left Stick X`    | Steering                                      |
| `X` / `LB`        | Downshift                                     |
| `B` / `RB`        | Upshift                                       |
| `A`               | Toggle auto shift                             |
| `Y`               | Toggle trajectory                             |
| `D-pad Left`      | Timer cycle (idle → running → stopped → idle) |
| `D-pad Right`     | Toggle true form                              |
| `Back` / `Select` | Reset scenario                                |
| `D-pad Up`        | Zoom in                                       |
| `D-pad Down`      | Zoom out                                      |
| `Start`           | Open/close options                            |

### Note

A `MCLAREN_P1` preset can be found in the provided presets, this set is estimated from various in-real-life public sources, meant to represent an actual car. Its here mostly to help me validate a mathematical modeling paper for my schoolwork.

## Roadmap

```
- [x] Model 1: Longitudinal Point Mass (1D)
    - Straight Line Physics
    - Magic Constants
    - Braking
- [x] Model 2: Load Transfer Without Traction Limits (1D)
    - Weight Transfer
- [x] Model 3: Engine Torque + Gearing without Slip (1D)
    - Engine Force
    - Gear Ratios
    - Drive Wheel Acceleration (simplified)
- [x] Model 4: Wheel Rotational Dynamics (1D)
    - Drive Wheel Acceleration (full)
- [x] Model 5: Slip Ratio + Traction Curve (1D)
    - Slip Ratio & Traction Force
- [x] Model 6: Low-Speed Kinematic Turning (2D)
    - Curves (low speed)
- [ ] Model 7: High-Speed Lateral Tire Model (2D)
    - High Speed Turning
- [ ] Model 8: Full Coupled Tire Model (2D)
```

Completed models:

- [Model 1: Longitudinal Point Mass (1D)](https://github.com/duy-phamduc68/Longitudinal-Car-Physics#model-1-longitudinal-point-mass-1d)
- [Model 2: Load Transfer Without Traction Limits (1D)](https://github.com/duy-phamduc68/Longitudinal-Car-Physics#model-2-load-transfer-without-traction-limits-1d)
- [Model 3: Engine Torque + Gearing without Slip (1D)](https://github.com/duy-phamduc68/Longitudinal-Car-Physics#model-3-engine-torque--gearing-without-slip-1d)
- [Model 4: Wheel Rotational Dynamics (1D)](https://github.com/duy-phamduc68/Longitudinal-Car-Physics#model-4-wheel-rotational-dynamics-1d)
- [Model 5: Slip Ratio + Traction Curve (1D)](https://github.com/duy-phamduc68/Longitudinal-Car-Physics#model-5-slip-ratio--traction-curve-1d)
- [Model 6: Low-Speed Kinematic Turning (2D)](#model-6-low-speed-kinematic-turning-2d)
- [Model 7: High-Speed Lateral Tire Model (2D)]
- [Model 8: Full Coupled Tire Model (2D)]