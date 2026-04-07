# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from Deeploy.MemoryLevelExtension.MemoryLevels import MemoryHierarchy, MemoryLevel
from Deeploy.Targets.NeurekaSCARV.Engine import NeurekaSCARVEngine
from Deeploy.Targets.Neureka.Platform import MemoryNeurekaPlatform, NeurekaConstantBuffer, NeurekaPlatform
from Deeploy.Targets.PULPOpen.Platform import PULPStructBuffer, PULPTransientBuffer, PULPVariableBuffer
from Deeploy.Targets.PULPOpen_iDMA.Platform import PULPClusterEngine_iDMA


class NeurekaSCARVPlatform(NeurekaPlatform):

    def __init__(self,
                 engines = [NeurekaSCARVEngine("Neureka"), PULPClusterEngine_iDMA("PULPCluster")],
                 variableBuffer = PULPVariableBuffer,
                 constantBuffer = NeurekaConstantBuffer,
                 structBuffer = PULPStructBuffer,
                 transientBuffer = PULPTransientBuffer) -> None:
        super().__init__(engines, variableBuffer, constantBuffer, structBuffer, transientBuffer)


class MemoryNeurekaSCARVPlatform(MemoryNeurekaPlatform):

    def __init__(self,
                 memoryHierarchy: MemoryHierarchy,
                 defaultTargetMemoryLevel: MemoryLevel,
                 weightMemoryLevel: Optional[MemoryLevel] = None,
                 engines = [NeurekaSCARVEngine("Neureka"), PULPClusterEngine_iDMA("PULPCluster")],
                 variableBuffer = PULPVariableBuffer,
                 constantBuffer = NeurekaConstantBuffer,
                 structBuffer = PULPStructBuffer,
                 transientBuffer = PULPTransientBuffer) -> None:
        super().__init__(memoryHierarchy, defaultTargetMemoryLevel, weightMemoryLevel, engines, variableBuffer,
                         constantBuffer, structBuffer, transientBuffer)
