# Desktop Tensile Testing Machine

![Construction Diagram](Pictures/Konstruktion.png)

## Overview

The tensile testing machine described here is a fully open-source device designed to determine the mechanical tensile strength of test specimens. At its core, it uses a single-board computer (typically a Raspberry Pi), which, in combination with a load cell and an HX711 amplifier, performs precise force measurements. A bipolar stepper motor module ensures defined positioning and feed control, enabling reproducible loading profiles.
The goal of the project is to provide an affordable and modular testing rig that can be used and further developed by both hobbyists and research laboratories. Control is provided via an intuitive touch GUI (based on ttkbootstrap and tkinter), which visualizes all relevant parameters—test length, feed rate, and force-drop threshold—in real time and automatically saves measurement data to CSV logs.
Thanks to the MIT open-source license, the entire source code is freely available on GitHub. The modular architecture and clear interfaces allow for customization, extensions, and the integration of additional sensors or actuators. This makes the tensile tester a flexible platform for material testing, educational purposes, and DIY projects.


![Construction Diagram](Pictures/Diagram_Extrudr_PCTG.jpeg)

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
