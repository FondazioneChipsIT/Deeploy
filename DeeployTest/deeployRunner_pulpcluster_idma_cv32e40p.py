#!/usr/bin/env python
# SPDX-FileCopyrightText: 2025 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

# Untiled flow for the standalone PULP cluster with iDMA on OpenHW CV32E40P cores.
# See deeployRunner_tiled_pulpcluster_idma_cv32e40p.py for the invocation notes.

import sys

from testUtils.deeployRunner import main

if __name__ == "__main__":

    def setup_parser(parser):
        parser.add_argument('--cores', type = int, default = 8, help = 'Number of cores (default: 8)\n')

    sys.exit(
        main(default_platform = "PULPCluster_iDMA_CV32E40P",
             default_simulator = "qsim",
             tiling_enabled = False,
             parser_setup_callback = setup_parser))
