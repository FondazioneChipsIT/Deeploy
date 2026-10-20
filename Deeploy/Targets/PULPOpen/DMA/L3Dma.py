# SPDX-FileCopyrightText: 2025 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

import math
import os
from typing import Dict, Tuple

from Deeploy.DeeployTypes import NetworkContext, NodeTemplate, OperatorRepresentation, VariableBuffer
from Deeploy.TilingExtension.AsyncDma import AsyncDma, BlockingDmaFromAsyncDmaAdapter, DmaDirection, Future, \
    PerTensorWaitingStrategy


class L3DmaFuture(Future):

    _initTemplate = NodeTemplate("pi_cl_ram_req_t ${name} = {0};")

    _deinitTemplate = NodeTemplate("")

    _allocTemplate = NodeTemplate("")

    _waitTemplate = NodeTemplate("""
    if (${name}.size != 0) {
        pi_cl_ram_copy_wait(&${name});
    }""")


class L3Dma(AsyncDma):

    _transferTemplates = {
        2:
            NodeTemplate(
                "pi_cl_ram_copy_2d(get_ram_ptr(), ${ext}, ${loc}, ${transfer_size}, ${stride}, ${length}, ${ext2loc}, &${future});"
            )
    }
    _waitingStrategy = PerTensorWaitingStrategy(L3DmaFuture)

    def __init__(self, transferTemplates: Dict[int, NodeTemplate] = _transferTemplates) -> None:
        super().__init__(transferTemplates)

    def checkTransfer(self, ctxt: NetworkContext, externalBuffer: VariableBuffer, localBuffer: VariableBuffer,
                      shape: Tuple[int, ...], strideExt: Tuple[int, ...], strideLoc: Tuple[int, ...],
                      direction: DmaDirection) -> None:
        super().checkTransfer(ctxt, externalBuffer, localBuffer, shape, strideExt, strideLoc, direction)
        assert strideExt[-1] == 1, \
            "Mchan supports only contigous transfers of the innermost dimension for external memory"
        assert strideLoc[0] == shape[1] and strideLoc[1] == 1, \
            f"Mchan supports only contigous transfers for local memory. Received local shape: {shape}, stride: {strideLoc}"

    def transferOpRepr(self, externalBuffer: VariableBuffer, localBuffer: VariableBuffer, shape: Tuple[int, ...],
                       strideExt: Tuple[int, ...], strideLoc: Tuple[int, ...], direction: DmaDirection,
                       future: Future) -> OperatorRepresentation:
        operatorRepresentation = super().transferOpRepr(externalBuffer, localBuffer, shape, strideExt, strideLoc,
                                                        direction, future)
        operatorRepresentation.update({
            "ext2loc": 1 if direction == "ExternalToLocal" else 0,
            "transfer_size": math.prod(shape),
            "length": shape[1],
            "stride": strideExt[0],
        })
        return operatorRepresentation


# LMACAN: It's a hack because the driver is now working correctly
l3DmaHack = BlockingDmaFromAsyncDmaAdapter(L3Dma())

# DEEPLOY_L3_ASYNC=1: keep L3 transfers non-blocking (wait only before a buffer is used), so that
# --doublebuffer can overlap them with computation. Experimental, see the hack note above.
# Asynchronous L3 transfers. A 3D transfer is a single pi_cl_ram_copy_3d request, which the FC splits
# into 2D copies, so the cluster does not block on the inner copies. Higher ranks are emitted as a loop of
# 3D copies sharing one request, so each copy must wait for the previous one: re-sending a pending request
# links its task to itself in the FC scheduler. The wait is a no-op when the tiling code already waited.
class L3AsyncDma(L3Dma):

    _waitPreviousTemplate = """
    if (${future}.size != 0) {
        pi_cl_ram_copy_wait(&${future});
    }"""

    _transferTemplates = {
        2:
            NodeTemplate(_waitPreviousTemplate + """
    pi_cl_ram_copy_2d(get_ram_ptr(), ${ext}, ${loc}, ${transfer_size}, ${stride}, ${length}, ${ext2loc}, &${future});"""
                        ),
        3:
            NodeTemplate(_waitPreviousTemplate + """
    pi_cl_ram_copy_3d(get_ram_ptr(), ${ext}, ${loc}, ${transfer_size}, ${stride}, ${length}, ${count}, ${ram_outer_stride}, ${loc_outer_stride}, ${ext2loc}, &${future});"""
                        ),
    }

    def __init__(self, transferTemplates: Dict[int, NodeTemplate] = _transferTemplates) -> None:
        super().__init__(transferTemplates)

    def checkTransfer(self, ctxt: NetworkContext, externalBuffer: VariableBuffer, localBuffer: VariableBuffer,
                      shape: Tuple[int, ...], strideExt: Tuple[int, ...], strideLoc: Tuple[int, ...],
                      direction: DmaDirection) -> None:
        # The 2D checks apply to the inner two dimensions, the outer strides are free
        super().checkTransfer(ctxt, externalBuffer, localBuffer, shape[-2:], strideExt[-2:], strideLoc[-2:],
                              direction)
        AsyncDma.checkTransfer(self, ctxt, externalBuffer, localBuffer, shape, strideExt, strideLoc, direction)

    def transferOpRepr(self, externalBuffer: VariableBuffer, localBuffer: VariableBuffer, shape: Tuple[int, ...],
                       strideExt: Tuple[int, ...], strideLoc: Tuple[int, ...], direction: DmaDirection,
                       future: Future) -> OperatorRepresentation:
        operatorRepresentation = super().transferOpRepr(externalBuffer, localBuffer, shape[-2:], strideExt[-2:],
                                                        strideLoc[-2:], direction, future)
        if len(shape) == 3:
            operatorRepresentation.update({
                "count": shape[0],
                "ram_outer_stride": strideExt[0],
                "loc_outer_stride": strideLoc[0],
            })
        return operatorRepresentation


if os.environ.get("DEEPLOY_L3_ASYNC") == "1":
    l3DmaHack = L3AsyncDma()
