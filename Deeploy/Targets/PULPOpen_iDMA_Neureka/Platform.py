# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from Deeploy.MemoryLevelExtension.MemoryLevels import MemoryHierarchy, MemoryLevel
from Deeploy.Targets.Generic.Layers import ConvLayer
from Deeploy.Targets.Neureka.Engine import NeurekaDenseConv2DMapper, NeurekaDWConv2DMapper, NeurekaPWConv2DMapper, \
    NeurekaRqntDenseConv2DMapper, NeurekaRqntDWConv2DMapper, NeurekaRqntPWConv2DMapper, _includeList as \
    _neurekaIncludeList, _neurekaInitCode
from Deeploy.Targets.Neureka.Platform import MemoryNeurekaPlatform, NeurekaConstantBuffer, NeurekaPlatform
from Deeploy.Targets.PULPOpen.Layers import PULPRQSConvLayer
from Deeploy.Targets.PULPOpen.Platform import PULPStructBuffer, PULPTransientBuffer, PULPVariableBuffer
from Deeploy.Targets.PULPOpen_iDMA.Platform import Conv1DMapper, Conv2DMapper, DWConv1DMapper, DWConv2DMapper, \
    FPConv2DMapper, FPDWConv2DMapper, PULPClusterEngine_iDMA, PULPMapping, _includeList as _iDMAIncludeList

# Combined include list: iDMA headers + Neureka-specific headers
_includeList = _iDMAIncludeList + [inc for inc in _neurekaIncludeList if inc not in _iDMAIncludeList]

# Combined mapping: Neureka conv mappers first, PULP as fallback for non-Neureka convolutions
PULPMapping_iDMA_Neureka = {
    **PULPMapping,
    'RequantizedConv':
        PULPRQSConvLayer([
            NeurekaRqntPWConv2DMapper, NeurekaRqntDWConv2DMapper, NeurekaRqntDenseConv2DMapper,
            Conv2DMapper, DWConv2DMapper, Conv1DMapper, DWConv1DMapper
        ]),
    'Conv':
        ConvLayer([
            NeurekaPWConv2DMapper, NeurekaDWConv2DMapper, NeurekaDenseConv2DMapper,
            FPConv2DMapper, FPDWConv2DMapper
        ]),
}


class PULPClusterEngine_iDMA_Neureka(PULPClusterEngine_iDMA):

    def __init__(self,
                 name: str,
                 Mapping = PULPMapping_iDMA_Neureka,
                 initCode = _neurekaInitCode,
                 includeList = _includeList,
                 n_cores: int = 8,
                 enable3x3: bool = False,
                 enableStrides: bool = False) -> None:
        super().__init__(name, Mapping, initCode, includeList, n_cores)
        self.enable3x3 = enable3x3
        self.enableStrides = enableStrides


class NeurekaPlatform_iDMA(NeurekaPlatform):

    def __init__(self,
                 engines = [PULPClusterEngine_iDMA_Neureka("PULPCluster")],
                 variableBuffer = PULPVariableBuffer,
                 constantBuffer = NeurekaConstantBuffer,
                 structBuffer = PULPStructBuffer,
                 transientBuffer = PULPTransientBuffer) -> None:
        super().__init__(engines, variableBuffer, constantBuffer, structBuffer, transientBuffer)


class MemoryNeurekaPlatform_iDMA(MemoryNeurekaPlatform):

    def __init__(self,
                 memoryHierarchy: MemoryHierarchy,
                 defaultTargetMemoryLevel: MemoryLevel,
                 weightMemoryLevel: Optional[MemoryLevel] = None,
                 engines = [PULPClusterEngine_iDMA_Neureka("PULPCluster")],
                 variableBuffer = PULPVariableBuffer,
                 constantBuffer = NeurekaConstantBuffer,
                 structBuffer = PULPStructBuffer,
                 transientBuffer = PULPTransientBuffer) -> None:
        super().__init__(memoryHierarchy, defaultTargetMemoryLevel, weightMemoryLevel, engines, variableBuffer,
                         constantBuffer, structBuffer, transientBuffer)
