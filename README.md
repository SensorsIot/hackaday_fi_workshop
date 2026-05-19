# Hackaday FI Workshop

Hackaday Fault Injection 101 workshop training material.

This repository contains:

- Windows host tooling for STM8 readout attempts
- a Python glitch sweep script
- sample STM8 firmware source
- reference traces to help you choose a glitch window

This README is written for a novice running the workshop on Windows.

## Goal

Use the glitcher to reset the STM8 target, inject a fault at a controlled time, and try to read flash through the ST-Link.

You are expected to determine the useful timing and glitch parameters yourself.

## Repository Layout

- `firmware_extraction/`
  - `dump_firmware.py`: host-side glitch sweep script
  - `glitcher.py`: serial protocol wrapper for the glitcher
  - `power_trace.png`, `power_trace.csv`, `bootup.png`: reference traces
- `stm8flash_win64/`
  - bundled Windows `stm8flash.exe`
- `test_firmware/`
  - STM8 sample firmware source
  - `build/main.bin`: prebuilt firmware image for comparison

## What You Need

Hardware:

- a Windows PC
- the workshop glitcher connected by USB
- an ST-Link V2 or compatible debugger
- the STM8 target board used for the workshop
- the required wiring between glitcher, ST-Link, and target

Software:

- Python 3
- the Python packages from `firmware_extraction/requirements.txt`

Optional:

- SDCC, if you want to rebuild the sample firmware yourself

## Before You Start

1. Connect the glitcher over USB.
2. Connect the ST-Link to the STM8 target.
3. Make sure the target powers up normally.
4. Open PowerShell in the repository root.

Install Python dependencies:

```powershell
python -m pip install -r firmware_extraction\requirements.txt
```

## Check That Windows Sees The Devices

List serial ports:

```powershell
python -c "import serial.tools.list_ports as lp; print('\n'.join(f'{p.device} vid={p.vid} pid={p.pid} interface={p.interface} desc={p.description}' for p in lp.comports()))"
```

The glitcher may appear as two serial ports. The correct control port is the one that responds to the glitcher protocol. If you do not know which one that is, test candidate ports with:

```powershell
@'
import serial, struct
for port in ['COM3', 'COM4']:
    print(f'== {port} ==')
    try:
        ser = serial.Serial(port, timeout=0.5)
        ser.write(struct.pack('<B', 0x8A))
        print('ack:', ser.read(2))
        ser.close()
    except Exception as e:
        print('error:', e)
'@ | python -
```

Replace `COM3` and `COM4` with the ports shown on your machine.

## Check That The ST-Link Works

Run:

```powershell
.\stm8flash_win64\stm8flash.exe -c stlinkv2 -p stm8s003f3 -s flash -b 4 -r dump.bin
```

If the ST-Link and target are wired correctly, `stm8flash` should identify the ST-Link and complete the read command.

That does not mean the protection bypass worked. It only confirms that the debugger path is functioning.

## How The Sweep Script Works

`firmware_extraction\dump_firmware.py` does this:

1. opens the glitcher control port
2. configures the glitch pattern and timing
3. resets the target
4. waits for the trigger
5. asks `stm8flash` to read flash through the ST-Link
6. repeats over a timing range until a useful result is found

## Important Parameter Meanings

- `--start-us`: sweep start in microseconds after the trigger
- `--stop-us`: sweep stop in microseconds after the trigger
- `--step`: holdoff increment in glitcher clock cycles
- `--tries`: attempts per timing point
- `--pattern`: glitch bit pattern such as `0b0000011`
- `--port`: glitcher control serial port

Important:

- `--start-us` and `--stop-us` are in microseconds
- `--step` is not in microseconds
- the glitcher runs at `250 MHz`, so one cycle is `4 ns`

Examples:

- `--step 1` = `4 ns`
- `--step 5` = `20 ns`
- `--step 10` = `40 ns`

## First Sweep

Start with a broad timing window and a small step size:

```powershell
python firmware_extraction\dump_firmware.py --port COMX --start-us 0 --stop-us 100 --step 5 --tries 1 --pattern 0b0000011
```

Replace `COMX` with the glitcher control port on your machine.

Use the provided trace images to narrow the timing window after broad scans.

## Using The Reference Traces

- `firmware_extraction/bootup.png` shows reset and trigger timing
- `firmware_extraction/power_trace.png` shows power activity after reset
- `firmware_extraction/power_trace.csv` contains the sampled trace data

Use these files to decide where in time to focus your sweep. Start wide, then narrow the window as you learn more.

## What Success Looks Like

On unsuccessful attempts, the read operation may still complete but the returned data will not be useful.

On a useful attempt, the script will report a successful timing point and then dump the beginning of the recovered firmware image.

When that happens, it writes `dump.bin` in the repository root.

## Compare Against The Sample Firmware

This repository includes a prebuilt firmware image for comparison:

- `test_firmware/build/main.bin`

You can compare the extracted image against the prebuilt binary with:

```powershell
@'
from pathlib import Path
built = Path(r'test_firmware/build/main.bin').read_bytes()
dumped = Path(r'dump.bin').read_bytes()
print('prefix_match:', dumped[:len(built)] == built)
print('built_len:', len(built))
print('dumped_len:', len(dumped))
'@ | python -
```

## Rebuild The Sample Firmware Yourself

This is optional. The prebuilt binary is already included.

If you install SDCC, you can rebuild with:

```powershell
$env:Path='C:\Program Files\SDCC\bin;' + $env:Path
New-Item -ItemType Directory -Force -Path test_firmware\build | Out-Null
Set-Location test_firmware
sdcc -c -mstm8 -pstm8s003f3 --std-sdcc11 -DF_CPU=2000000UL -I. --stack-auto --noinduction --use-non-free main.c -o build\main.rel
sdcc -mstm8 -lstm8 --out-fmt-ihx build\main.rel -o build\main.hex
sdobjcopy -I ihex --output-target=binary build\main.hex build\main.bin
Set-Location ..
```

## Troubleshooting

### `No ACK received`

Usually means one of these:

- wrong serial port
- the glitcher enumerated on a different COM port after reconnecting
- another process already has the COM port open

### `could not open port`

Usually means:

- wrong COM port
- stale Python process still holding the port
- the glitcher disconnected and re-enumerated

### `stm8flash not found`

The patched script defaults to the bundled Windows binary. If you moved files around, pass the path explicitly:

```powershell
python firmware_extraction\dump_firmware.py --port COMX --stm8flash .\stm8flash_win64\stm8flash.exe ...
```

### ST-Link is detected but readout never succeeds

That is expected until you find working glitch parameters. Adjust:

- timing window
- step size
- tries per point
- pattern

## Notes

- `dump.bin` is not committed by default.
- The repository includes a prebuilt `test_firmware/build/main.bin` so that firmware comparison does not require SDCC.
