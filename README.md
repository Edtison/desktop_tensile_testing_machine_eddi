# Desktop Tensile Testing Machine

![Construction Diagram](Pictures/Konstruktion.png)

## Overview

The tensile testing machine described here is a fully open-source device for determining
the mechanical tensile strength of test specimens. At its core is a single-board computer
(typically a Raspberry Pi), which, together with a load cell and an HX711 amplier, per-
forms precise force measurements. A bipolar stepper-motor module handles the dened
positioning and feed control, enabling reproducible loading proles.
The goal of the project is to provide an aordable, modular test rig that can be used and
further developed by hobbyists as well as research laboratories. Control is provided via
an intuitive touch GUI (using ttkbootstrap and tkinter), which visualizes all relevant
parameterstest length, feed rate, force-drop thresholdin real time and automatically
saves measurement data to CSV logs through programmable routines.
Thanks to the MIT open-source license, the entire source code is freely available on
GitHub. The modular architecture and clear interfaces facilitate customization, exten-
sion, and integration of additional sensors or actuators. This makes the tensile tester a
exible platform for material testing, educational purposes, and DIY projects.

## Features

- **Precise Force Measurement**  
  Load cell with HX711 amplifier, tare & calibration routines.
- **Stepper Motor Control**  
  Configurable pull‑rate, travel distance, and emergency stop on force drop.
- **Intuitive Touch GUI**  
  Built with `ttkbootstrap` + `tkinter` for live feedback and parameter adjustment.
- **Automatic Logging**  
  CSV log files with position vs. force data, auto‑incrementing filenames.


## Requirements

- **Hardware**  
  - Raspberry Pi (5)  
  - HX711 load cell amplifier + load cell  
  - Bipolar stepper motor (Nema 23) + driver (enable, dir, step pins) (3,3V compatible) 
- **Software**  
  - Python 3.11 < 
  - MicroPython (for MCU variant)  
  - `gpiozero`  
  - `ttkbootstrap`  
  - `tkinter`
