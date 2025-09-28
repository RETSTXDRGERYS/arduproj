# Copilot Instructions for `arduproj`

## Big Picture Architecture
- **Two main components:**
  - `brushless motor/`: Arduino-based ESC controller (C++/INO, Visual Studio solution)
  - `web/`: MicroPython/Pico W scripts for wireless control, BLE, and web API
- **Data flow:**
  - Physical ESC is controlled by Arduino (`brushless motor.ino`)
  - Pico W (`web/main.py`) exposes PWM control via WiFi and BLE
  - `web/client.py` is a Python script for remote control via HTTP
  - BLE peripheral (`ble_simple_peripheral.py`) enables mobile/IoT integration

## Developer Workflows
- **Arduino/ESC:**
  - Edit `brushless motor.ino` and related files in `brushless motor/src/`
  - Build/deploy using Visual Studio (see `.sln`/`.vcxproj`)
  - Folders under `src/` are auto-included in builds (see `arduino folders read me.txt`)
- **Pico W/MicroPython:**
  - Main entry: `web/main.py` (PWM, WiFi, LED control)
  - BLE: `web/ble_simple_peripheral.py`
  - HTTP client: `web/client.py` (update `PICO_IP` as needed)
  - Use Thonny or ampy for deployment to Pico W
- **Testing:**
  - No formal test suite; manual testing via serial console, HTTP requests, and BLE tools

## Project-Specific Conventions
- **Arduino:**
  - All `.ino`, `.cpp`, `.h` files in project or `src/` are compiled
  - Button press required for arming ESC (see `brushless motor.ino`)
  - Use built-in LED and buzzer for status
- **Pico W:**
  - PWM range clamped to 1000-2000us for ESC safety
  - Ramping functions for smooth speed changes
  - Pin assignments: 15 (ESC PWM), 16 (external LED), "LED" (onboard)
  - BLE UART service UUIDs are hardcoded

## Integration Points & Dependencies
- **Arduino:**
  - Uses Servo library, AVR watchdog
- **Pico W:**
  - Relies on `machine`, `network`, `bluetooth`, `micropython` modules
  - BLE service for UART-like communication
  - HTTP API for remote control
- **Cross-component:**
  - No direct communication; integration is via physical ESC wiring and wireless protocols

## Examples
- To ramp ESC speed: `ramp_to(target_micros)` in `main.py`
- To blink LED remotely: `GET /blink` on Pico W HTTP server
- To arm ESC: Press button on Arduino during startup

## Key Files/Directories
- `brushless motor/brushless motor.ino`: Arduino ESC logic
- `brushless motor/src/`: Additional Arduino sources
- `web/main.py`: Pico W PWM & web API
- `web/ble_simple_peripheral.py`: BLE UART service
- `web/client.py`: HTTP client for Pico W
- `arduino folders read me.txt`: Arduino build folder rules

---
**Feedback requested:**
- Are any build, deployment, or integration steps unclear?
- Is there undocumented automation, testing, or workflow logic?
- Are there conventions or patterns not covered here?
