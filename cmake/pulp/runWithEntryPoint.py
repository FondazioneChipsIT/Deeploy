#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0
"""Run a simulator command with +ENTRY_POINT read from the ELF being simulated.

The PULP testbench writes the address passed via the +ENTRY_POINT plusarg into
the FC's dpc and resumes from there. The nominal boot address is 0x1C008080,
but the pulp linker script only pins the vector table softly::

    .vectors MAX(0x1c008000, ALIGN(256)) : { ... }

so whenever .data_tiny_fc + .rodata + .stack overflow the 32 KiB L2 private
bank 0, MAX() silently slides .vectors (and hence _start) forward and the
testbench jumps into the middle of a data section. Read the real entry point
out of the ELF header instead of assuming the nominal one.

Usage:
    runWithEntryPoint.py <elf> -- <command> [args...]
"""

import os
import struct
import sys

NOMINAL_ENTRY_POINT = 0x1C008080

# ELF32 little-endian header layout, see elf(5).
EI_NIDENT = 16
EI_CLASS = 4
EI_DATA = 5
ELFCLASS32 = 1
ELFDATA2LSB = 1
E_ENTRY_OFFSET = 24


def readEntryPoint(elfPath: str) -> int:
    with open(elfPath, "rb") as f:
        header = f.read(E_ENTRY_OFFSET + 4)

    if len(header) < E_ENTRY_OFFSET + 4 or header[:4] != b"\x7fELF":
        raise ValueError(f"{elfPath} is not an ELF file")
    if header[EI_CLASS] != ELFCLASS32 or header[EI_DATA] != ELFDATA2LSB:
        raise ValueError(f"{elfPath} is not a little-endian 32-bit ELF file")

    return struct.unpack_from("<I", header, E_ENTRY_OFFSET)[0]


def main() -> int:
    if "--" not in sys.argv[1:]:
        print(f"usage: {sys.argv[0]} <elf> -- <command> [args...]", file = sys.stderr)
        return 2

    separator = sys.argv.index("--")
    if separator != 2 or len(sys.argv) == separator + 1:
        print(f"usage: {sys.argv[0]} <elf> -- <command> [args...]", file = sys.stderr)
        return 2

    elfPath = sys.argv[1]
    command = sys.argv[separator + 1:]

    try:
        entryPoint = readEntryPoint(elfPath)
    except (OSError, ValueError) as e:
        print(f"[runWithEntryPoint] {e}", file = sys.stderr)
        return 1

    if entryPoint != NOMINAL_ENTRY_POINT:
        # Not fatal, the testbench boots fine from any address, but it does mean
        # the image outgrew L2 private bank 0 and every fixed address in
        # link.ld (.vectors, .l2_data) has slid forward.
        print(f"[runWithEntryPoint] warning: {os.path.basename(elfPath)} starts at "
              f"0x{entryPoint:08x}, not the nominal 0x{NOMINAL_ENTRY_POINT:08x}; "
              f"L2 private bank 0 overflowed and pushed .vectors forward", file = sys.stderr)

    flags = os.environ.get("VSIM_RUNNER_FLAGS", "")
    os.environ["VSIM_RUNNER_FLAGS"] = f"{flags} +ENTRY_POINT=0x{entryPoint:08x}".strip()

    os.execvp(command[0], command)


if __name__ == "__main__":
    sys.exit(main())
