# Desktop Tensile Testing Machine

![Construction Diagram](Pictures/Konstruktion.png)

## Overview

This project provides an open‑source desktop tensile testing machine based on a single‑board computer (e.g., Raspberry Pi) and a bipolar stepper motor. A load cell (HX711 amplifier) measures force in real time, while a Python/Tkinter GUI allows you to configure and run test routines, logging all data to CSV.

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
