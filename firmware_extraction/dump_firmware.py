#!/usr/bin/env python3
import argparse
import subprocess
import time
from pathlib import Path

import rich.progress
from glitcher import Glitcher

DEFAULT_STM8FLASH = Path(__file__).resolve().parent.parent / 'stm8flash_win64' / 'stm8flash.exe'

F_CPU   = 250e6
RST_PIN = 29

us = lambda v : int(v * 1e-6 * F_CPU)

def parse_args():
    parser = argparse.ArgumentParser(description='STM8 fault injection firmware extraction helper')
    parser.add_argument('--port', help='Serial port for the glitcher control interface, e.g. COM114')
    parser.add_argument('--stm8flash', default=str(DEFAULT_STM8FLASH), help='Path to stm8flash executable')
    parser.add_argument('--start-us', type=float, default=0.0, help='Sweep start in microseconds')
    parser.add_argument('--stop-us', type=float, default=0.0, help='Sweep stop in microseconds (exclusive)')
    parser.add_argument('--step', type=int, default=1, help='Holdoff step in clock cycles')
    parser.add_argument('--tries', type=int, default=1, help='Attempts per holdoff value')
    parser.add_argument('--pattern', type=lambda v: int(v, 0), default=0b00000, help='Glitch pattern, e.g. 0b101 or 0x15')
    return parser.parse_args()

args = parse_args()
STM8FLASH = args.stm8flash
start = us(args.start_us)
stop = us(args.stop_us)
step = args.step
tries = args.tries
pattern = args.pattern

dev = Glitcher(args.port)
dev.set_freq(int(F_CPU))
dev.set_pattern(pattern)
dev.set_trigger_edge(0)
dev.gpio_set_pull(RST_PIN, up=True, down=False)

settings = dev.get_settings()
print(f'glitcher config:')
for key, value in settings.items():
    print(f'  - {key}: {value}')
print()

def read_flash():
    cmd = [STM8FLASH, '-c', 'stlinkv2', '-p', 'stm8s003f3', '-s', 'flash', '-b', '4', '-r', 'dump.bin']
    return_code = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if return_code == 0:
        with open('dump.bin', 'rb') as f:
            if f.read(4) != b'\x71\x71\x71\x71':
                cmd = [STM8FLASH, '-c', 'stlinkv2', '-p', 'stm8s003f3', '-s', 'flash', '-b', '8192', '-r', 'dump.bin']
                return_code = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
    elif return_code != 0 and not Path(STM8FLASH).exists():
        print('ERROR: stm8flash not found!')
        exit(-1)
    return False

def hexdump(data, width=16):
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_bytes = ' '.join(f'{b:02x}' for b in chunk)
        hex_padded = hex_bytes.ljust(width * 3 - 1)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f'{i:08x}: {hex_padded}  {ascii_part}')

with rich.progress.Progress(
    rich.progress.TextColumn('[bold magenta]{task.description}'),
    rich.progress.BarColumn(),
    rich.progress.TextColumn('step: {task.fields[holdoff]}', justify='right'),
    rich.progress.TextColumn('[bold cyan]{task.percentage:>3.0f}%'),
    rich.progress.TimeElapsedColumn(),
) as progress:
    total = len(range(start, stop, step))
    if total == 0:
        print('No sweep to run. Increase --stop-us or adjust --start-us/--step.')
        exit(1)

    task = progress.add_task('glitching...', total=total, holdoff=start)

    for holdoff in range(start, stop, step):
        for t in range(tries):
            dev.set_holdoff(holdoff)

            # reset target
            dev.gpio_write(RST_PIN, 0)
            dev.arm()
            dev.gpio_write(RST_PIN, 1)

            # wait for trigger
            if not dev.get_trigger_state():
                print('no trigger')
                time.sleep(0.01)
                if not dev.get_trigger_state():
                    print('trigger timeout!')

            # try reading flash
            if read_flash():
                print(f'success at {holdoff} ({(holdoff/F_CPU * 1e6):.2f} us)!')
                print('dumping firmware..')

                with open('dump.bin', 'rb') as f:
                    data = f.read()
                    hexdump(data[:256])
                exit(0)

        progress.update(task, advance=step, holdoff=holdoff)
