# SPDX-FileCopyrightText: 2025 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

import os
from dataclasses import dataclass
from typing import List, Literal, Optional


@dataclass
class DeeployTestConfig:
    """Configuration for a single test case."""
    test_name: str
    test_dir: str
    platform: str
    simulator: Literal['gvsoc', 'banshee', 'qemu', 'vsim', 'vsim.gui', 'host', 'none']
    tiling: bool
    gen_dir: str
    build_dir: str
    toolchain: str = "LLVM"
    toolchain_install_dir: Optional[str] = None
    gvsoc_install_dir: Optional[str] = None
    cmake_args: List[str] = None
    gen_args: List[str] = None
    verbose: int = 0
    debug: bool = False
    # Keep the raw GVSoC VCD event dump in <build_dir>/gvsoc_workdir/all.vcd
    vcd: bool = False
    # Convert the VCD dump to a Perfetto trace after simulation. Implies dump_vcd.
    profile: bool = False
    # Override the gvsoc --event selectors (default: per-platform)
    vcd_events: Optional[List[str]] = None
    # Override the gvsoc2perfetto --include regex (default: per-platform)
    vcd_include: Optional[str] = None

    @property
    def dump_vcd(self) -> bool:
        """Whether GVSoC has to write a VCD event dump at all."""
        return self.vcd or self.profile

    @property
    def keep_vcd(self) -> bool:
        """Whether to keep the raw dump after a successful Perfetto conversion.

        The dumps are large (tens of MB), so --profile alone cleans up after
        itself; passing --vcd on top of it keeps the raw dump for GTKWave.
        """
        return self.vcd

    def __post_init__(self):
        if self.cmake_args is None:
            self.cmake_args = []
        if self.gen_args is None:
            self.gen_args = []
        if self.toolchain_install_dir is None:
            self.toolchain_install_dir = os.environ.get('LLVM_INSTALL_DIR')
        if self.gvsoc_install_dir is None:
            self.gvsoc_install_dir = os.environ.get('GVSOC_INSTALL_DIR')
