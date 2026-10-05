#!/usr/bin/env python
# SPDX-FileCopyrightText: 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT
#
# SPDX-License-Identifier: Apache-2.0

# Untiled flow for the PULP cluster in the OpenTitan secure domain (no FC, iDMA, RI5CY).
# Needs PULP_SDK_HOME with the opentitan_cluster chip. Build only: the ELF is run by the OT offload flow.

import sys

from testUtils.deeployRunner import main

if __name__ == "__main__":

    def setup_parser(parser):
        parser.add_argument('--cores', type = int, default = 8, help = 'Number of cores (default: 8)\n')

    sys.exit(
        main(default_platform = "OpenTitanCluster_iDMA",
             default_simulator = "none",
             tiling_enabled = False,
             parser_setup_callback = setup_parser))
