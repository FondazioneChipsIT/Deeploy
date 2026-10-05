#!/usr/bin/env python
# SPDX-FileCopyrightText: 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT
#
# SPDX-License-Identifier: Apache-2.0

# Tiled flow for the PULP cluster in the OpenTitan secure domain (no FC, iDMA, RI5CY).
# Needs PULP_SDK_HOME with the opentitan_cluster chip (mmram L3). Build only: the ELF is run by the OT offload flow.

import sys

from testUtils.deeployRunner import main

if __name__ == "__main__":

    def setup_parser(parser):
        parser.add_argument('--cores', type = int, default = 8, help = 'Number of cores (default: 8)\n')
        # L1: 256 KiB TCDM minus cluster stacks (8000 + 7*3800 B), mmram staging (2*4 KiB), margin.
        # L2: arena from the 448 KiB shared banks, which also hold the static image.
        # L3: HyperRAM window of link.ld (8 MiB); with -D OT_L3_SIZE=<n> pass --l3 <n> too.
        # --defaultMemLevel L3 puts weights/IO in HyperRAM.
        parser.set_defaults(l3 = 8388608, l2 = 320000, l1 = 212000, defaultMemLevel = "L2")

    sys.exit(
        main(default_platform = "OpenTitanCluster_iDMA",
             default_simulator = "none",
             tiling_enabled = True,
             parser_setup_callback = setup_parser))
