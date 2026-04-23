# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

from typing import List

from Deeploy.DeeployTypes import NodeMapper
from Deeploy.Targets.Generic.Layers import ConvLayer
from Deeploy.Targets.Neureka.Engine import NeurekaEngine
from Deeploy.Targets.Neureka.Parsers import NeurekaDenseConv2DParser, NeurekaDWConv2DParser, NeurekaPWConv2DParser, \
    NeurekaRQSDenseConv2DParser, NeurekaRQSDWConv2DParser, NeurekaRQSPWConv2DParser
from Deeploy.Targets.NeurekaSCARV.Tiler import NeurekaDenseConv2DTilingReadyBindings, \
    NeurekaDWConv2DTilingReadyBindings, NeurekaPWConv2DTilingReadyBindings, \
    NeurekaRQSDenseConv2DTilingReadyBindings, NeurekaRQSDWConv2DTilingReadyBindings, \
    NeurekaRQSPWConv2DTilingReadyBindings
from Deeploy.Targets.PULPOpen.Layers import PULPRQSConvLayer
from Deeploy.Targets.Neureka.Config import NeurekaConfig
from Deeploy.Targets.NeurekaSCARV.Config import NEUREKA_SCARV_CONFIG

NeurekaRqntPWConv2DMapper = NodeMapper(NeurekaRQSPWConv2DParser(), NeurekaRQSPWConv2DTilingReadyBindings)
NeurekaPWConv2DMapper = NodeMapper(NeurekaPWConv2DParser(), NeurekaPWConv2DTilingReadyBindings)

NeurekaRqntDWConv2DMapper = NodeMapper(NeurekaRQSDWConv2DParser(), NeurekaRQSDWConv2DTilingReadyBindings)
NeurekaDWConv2DMapper = NodeMapper(NeurekaDWConv2DParser(), NeurekaDWConv2DTilingReadyBindings)

NeurekaRqntDenseConv2DMapper = NodeMapper(NeurekaRQSDenseConv2DParser(), NeurekaRQSDenseConv2DTilingReadyBindings)
NeurekaDenseConv2DMapper = NodeMapper(NeurekaDenseConv2DParser(), NeurekaDenseConv2DTilingReadyBindings)

NeurekaMapping = {
    'RequantizedConv':
        PULPRQSConvLayer([NeurekaRqntPWConv2DMapper, NeurekaRqntDWConv2DMapper, NeurekaRqntDenseConv2DMapper]),
    'Conv':
        ConvLayer([NeurekaPWConv2DMapper, NeurekaDWConv2DMapper, NeurekaDenseConv2DMapper]),
}

# TOFIX
_includeList = ["pulp_nnx_neureka.h", "pulp_nnx_util.h", "neureka_bsp.h", "neureka.h", "neureka_task.h"]

_neurekaInitCode = r"""
neureka_dev_t *dev = neureka_bsp_get_dev();
neureka_bsp_conf_t conf = {.max_stall = 8};
neureka_nnx_init(dev, &conf);
neureka_nnx_dispatch_wait(dev);
"""


class NeurekaSCARVEngine(NeurekaEngine):

    def __init__(self,
                 name: str,
                 Mapping = NeurekaMapping,
                 initCode: str = _neurekaInitCode,
                 includeList: List[str] = _includeList,
                 enable3x3: bool = False,
                 enableStrides: bool = False,
                 config: NeurekaConfig = NEUREKA_SCARV_CONFIG) -> None:
        super().__init__(name, Mapping, initCode, includeList, enable3x3, enableStrides, config)
