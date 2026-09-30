# Copyright (c) 2025 FondazioneChipsIT
# SPDX-License-Identifier: Apache-2.0

import math
from typing import Dict, List, Tuple

from Deeploy.DeeployTypes import CodeSnippet, NetworkContext, NodeTemplate, OperatorRepresentation, VariableBuffer, \
    _ReferenceBuffer
from Deeploy.TilingExtension.AsyncDma import AnydimAsyncDmaTransferAdapter, AsyncDma, DirectionWaitingStrategy, \
    DmaDirection, Future

# HAL pulp_idma_transfer_*_and_wait take the (row) length as unsigned short
_MAX_LEN = 2**16 - 1
# Split rows for long 1D transfers, word-aligned so the tail offset stays aligned
_CHUNK = _MAX_LEN & ~3


class iDMAChannelFuture(Future):

    _initTemplate = NodeTemplate("")
    _deinitTemplate = NodeTemplate("")
    _waitTemplate = NodeTemplate("")
    _allocTemplate = NodeTemplate("")


class iDMA(AsyncDma):

    _transferTemplates = {
        1:
            NodeTemplate("pulp_idma_transfer_1d_and_wait(${direction}, ${ext}, ${loc}, ${length});"),
        2:
            NodeTemplate(
                "pulp_idma_transfer_2d_and_wait(${direction}, ${ext}, ${loc}, ${length}, ${strideExt}, ${strideLoc}, ${num_reps});"
            )
    }
    _waitingStrategy = DirectionWaitingStrategy(iDMAChannelFuture, "channel_id")

    def __init__(self, transferTemplates: Dict[int, NodeTemplate] = _transferTemplates) -> None:
        super().__init__(transferTemplates)

    def checkTransfer(self, ctxt: NetworkContext, externalBuffer: VariableBuffer, localBuffer: VariableBuffer,
                      shape: Tuple[int, ...], strideExt: Tuple[int, ...], strideLoc: Tuple[int, ...],
                      direction: DmaDirection) -> None:
        super().checkTransfer(ctxt, externalBuffer, localBuffer, shape, strideExt, strideLoc, direction)

        # Here are some assertions on the iDMA transfer parameters
        transferRank = len(shape)

        assert transferRank == 1 or transferRank == 2, "Only 1D and 2D transfers are supported for now"

        if transferRank == 1:
            length = shape[0]
        elif transferRank == 2:
            length = shape[1]

        # Long 1D transfers are split by transfer(); in 2D only the row length is 16-bit
        assert length <= _MAX_LEN, (f"iDMA row length {length} exceeds the HAL's 16-bit limit ({_MAX_LEN})")

        if transferRank == 2:
            assert strideExt[0] >= length, "External stride must be at least equal to the length"
            assert strideLoc[0] >= length, "Local stride must be at least equal to the length"

    def transfer(self, ctxt: NetworkContext, externalBuffer: VariableBuffer, localBuffer: VariableBuffer,
                 shape: Tuple[int, ...], strideExt: Tuple[int, ...], strideLoc: Tuple[int, ...],
                 direction: DmaDirection, future: Future) -> List[CodeSnippet]:
        if len(shape) != 1 or shape[0] <= _MAX_LEN:
            return super().transfer(ctxt, externalBuffer, localBuffer, shape, strideExt, strideLoc, direction, future)

        full, rem = divmod(shape[0], _CHUNK)
        # Bulk as one contiguous 2D transfer of _CHUNK-byte rows
        callStack = super().transfer(ctxt, externalBuffer, localBuffer, (full, _CHUNK), (_CHUNK, 1), (_CHUNK, 1),
                                     direction, future)
        if rem == 0:
            return callStack

        # Tail as a 1D transfer at the bulk's end, scoped so the pointer names can't collide
        ptrTemplate = AnydimAsyncDmaTransferAdapter.offsetPtrTemplate
        extTail = _ReferenceBuffer("external_buffer_tail", externalBuffer)
        extTail._memoryLevel = externalBuffer._memoryLevel
        locTail = _ReferenceBuffer("local_buffer_tail", localBuffer)
        locTail._memoryLevel = localBuffer._memoryLevel
        offset = full * _CHUNK
        callStack.append(CodeSnippet(NodeTemplate("{"), {}))
        callStack.append(
            CodeSnippet(ptrTemplate, {
                "resultPtr": extTail.name,
                "basePtr": externalBuffer.name,
                "offset": offset
            }))
        callStack.append(
            CodeSnippet(ptrTemplate, {
                "resultPtr": locTail.name,
                "basePtr": localBuffer.name,
                "offset": offset
            }))
        callStack.extend(super().transfer(ctxt, extTail, locTail, (rem,), (1,), (1,), direction, future))
        callStack.append(CodeSnippet(NodeTemplate("}"), {}))
        return callStack

    def transferOpRepr(self, externalBuffer: VariableBuffer, localBuffer: VariableBuffer, shape: Tuple[int, ...],
                       strideExt: Tuple[int, ...], strideLoc: Tuple[int, ...], direction: DmaDirection,
                       future: Future) -> OperatorRepresentation:
        operatorRepresentation = super().transferOpRepr(externalBuffer, localBuffer, shape, strideExt, strideLoc,
                                                        direction, future)

        transferRank = len(shape)
        operatorRepresentation["direction"] = 1 if direction == "ExternalToLocal" else 0

        iDMA_transfer_size = math.prod(shape)

        if transferRank == 1:
            operatorRepresentation["length"] = shape[0]
        elif transferRank == 2:
            operatorRepresentation["length"] = shape[1]
            operatorRepresentation["strideExt"] = strideExt[0]
            operatorRepresentation["strideLoc"] = strideLoc[0]
            operatorRepresentation["num_reps"] = iDMA_transfer_size // shape[1]

        return operatorRepresentation
