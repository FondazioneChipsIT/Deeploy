# SPDX-FileCopyrightText: 2025 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

import os
from typing import List, Union

from ortools.constraint_solver.pywrapcp import IntVar

from Deeploy.DeeployTypes import NetworkContext, SubGraph, TransientBuffer
from Deeploy.TilingExtension.TilerExtension import Tiler
from Deeploy.TilingExtension.TilerModel import TilerModel


class DBOnlyL3Tiler(Tiler):

    def multiBufferStrategy(self, tilerModel: TilerModel, ctxt: NetworkContext, pattern: SubGraph, path: List[str],
                            hop: str, tensorName: str) -> Union[int, IntVar]:
        buffer = ctxt.lookup(tensorName)

        if isinstance(buffer, TransientBuffer):
            return 1

        if hop == 'L1':
            return 1

        # DEEPLOY_DB_SINGLE=transpose,...: single-buffer patterns whose node op type or name contains one
        # of these (case-insensitive): little compute to hide L3 behind, and large tiles that set the L2
        # peak. Experimental.
        singleKeys = [k.lower() for k in os.environ.get("DEEPLOY_DB_SINGLE", "").split(",") if k]
        if any(k in node.op.lower() or k in node.name.lower() for node in pattern for k in singleKeys):
            return 1

        return 2


class DBTiler(Tiler):

    def multiBufferStrategy(self, tilerModel: TilerModel, ctxt: NetworkContext, pattern: SubGraph, path: List[str],
                            hop: str, tensorName: str) -> Union[int, IntVar]:
        buffer = ctxt.lookup(tensorName)

        if isinstance(buffer, TransientBuffer):
            return 1

        return 2


class SBTiler(Tiler):

    def multiBufferStrategy(self, tilerModel: TilerModel, ctxt: NetworkContext, pattern: SubGraph, path: List[str],
                            hop: str, tensorName: str) -> Union[int, IntVar]:
        return 1
