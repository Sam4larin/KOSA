# Connecting real hardware to KoSa

**Status: experimental.** The Python side is tested against simulated boards. The sketch has run in the Wokwi simulator but has not yet been tried on a physical board. Please report what you find.

## How it works
KoSa and the board exchange one text line each way over USB serial (9600 baud):

| KoSa sends | Board replies |
|---|---|
| `PING` | `PONG` |
| `D13 ON`, `D13 OFF`, `D13 LOCK`, `D13 UNLOCK` (pins D2 to D13) | `OK` (or `ERR`) |

`ON` and `LOCK` set the pin HIGH, `OFF` and `UNLOCK` set it LOW. The sketch is `KoSa_device/KoSa_device.ino`.

## With a real board
1. Install the free Arduino IDE, open `KoSa_device/KoSa_device.ino` and upload it.
2. Run KoSa, open the **Devices** page, press **Refresh ports**.
3. Try pin **D13** first: on an Arduino Uno it is the built-in LED, so no wiring is needed.
4. Choose the port and pin next to a device, press **Pair**, then **Test**.
5. Give each device its own pin. Two devices on one pin will fight each other.

For an external LED: pin, then a 220 ohm resistor, then the LED, then GND. For lamps, fans or locks, use a relay or lock module designed for low-voltage control signals. **Never connect mains electricity directly to a board.**

## Plain USB gadgets do not work
A USB fan or lamp plugged straight into the laptop only receives power. The port has no data channel for switching it, so KoSa cannot turn it on or off. To control one, power it through a relay or transistor that a board switches.

## Testing without hardware

**Layer 1, KoSa's side:** run `python hardware/fake_board.py`, then pair a device to the **KoSa test board** port. The window shows every command and pin change.

**Layer 2, the sketch:** paste the sketch into a new Arduino Uno project at wokwi.com, press play, and type `PING`, `D13 ON` and `D13 OFF` into the serial monitor.

**Layer 3, KoSa talking to the simulated Uno (advanced, not yet verified):**
1. Install VS Code and the **Wokwi Simulator** extension. In the Command Palette run **Wokwi: Request a New License** (free).
2. Install `arduino-cli` and run: `arduino-cli core install arduino:avr`
3. From the project root: `arduino-cli compile --fqbn arduino:avr:uno --output-dir hardware/wokwi/build hardware/KoSa_device`
4. Open the folder `hardware/wokwi` in VS Code. Its `wokwi.toml` turns on a serial server on port 4000 (`rfc2217ServerPort = 4000`).
5. Run **Wokwi: Start Simulator** and keep the simulator tab visible. Wokwi pauses when it is hidden.
6. In KoSa's Devices page choose the **Wokwi simulator** port (`rfc2217://localhost:4000`) and pair a device to D13.
7. Say "turn on the bedside light". The virtual Uno's pin 13 LED should light up. If pairing errors, try the address `rfc2217://localhost:4000?ign_set_control=1`.
