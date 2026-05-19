# Hackaday FI Workshop Extraction Notes

## Summary

This repository was executed on Windows with a connected glitcher and ST-Link.

The firmware readout protection bypass succeeded with:

- Pattern: `0b0000011`
- Holdoff: `14005` cycles
- Time after trigger: `56.02 us`
- Glitcher frequency: `250 MHz`
- Glitcher control port at time of success: `COM116`

The successful run produced a full `dump.bin` flash image and the extracted firmware matches the sample firmware in `test_firmware/main.c`.

## What Was Done

1. Cloned the original repository locally.
2. Verified the host-side Python dependencies.
3. Confirmed the ST-Link could communicate with the STM8 target using the bundled `stm8flash` binary.
4. Confirmed the glitcher was present, then identified the correct control interface because it enumerated as two serial ports.
5. Patched `firmware_extraction/dump_firmware.py` so it can be run without editing source each time.
6. Swept the glitch timing window using the user-provided pattern `0b0000011`.
7. Extracted the firmware when the successful holdoff was hit.
8. Installed SDCC 4.5.0, rebuilt the sample firmware, and compared it against the extracted image.

## Code Changes

`firmware_extraction/dump_firmware.py` was updated to make the extraction flow usable from the command line on this machine:

- Added `argparse`
- Added `--port`
- Added `--stm8flash`
- Added `--start-us`
- Added `--stop-us`
- Added `--step`
- Added `--tries`
- Added `--pattern`
- Defaulted `stm8flash` to the bundled Windows executable
- Switched `stm8flash` invocation from shell strings to argument lists
- Added a guard for empty sweep ranges

This allowed runs such as:

```powershell
python firmware_extraction\dump_firmware.py --port COM116 --start-us 8 --stop-us 100 --step 5 --tries 1 --pattern 0b0000011
```

## Successful Result

The successful run reported:

```text
success at 14005 (56.02 us)!
```

After that, the script dumped a full flash image instead of the locked readout pattern `0x71 0x71 0x71 0x71`.

## Verification

The extracted image was verified in two ways:

1. `dump.bin` contains the expected format string from `test_firmware/main.c`:

```text
[%lu][%lu][%lu]: %lu\r\n
```

2. The sample firmware was rebuilt with SDCC 4.5.0 and compared against the extracted image:

- `test_firmware/build/main.bin`: `1892` bytes
- `dump.bin`: `8192` bytes
- The rebuilt binary matches the beginning of `dump.bin` exactly, byte-for-byte
- The remaining bytes in `dump.bin` are zero-filled flash space

## Notes

- The original repository version of `dump_firmware.py` used `step = 1`, which means one holdoff cycle per increment.
- At `250 MHz`, one cycle is `4 ns`.
- In the patched script, `start-us` and `stop-us` are microseconds, but `step` is still expressed in cycles.
