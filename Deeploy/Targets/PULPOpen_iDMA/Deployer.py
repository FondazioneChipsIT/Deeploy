# SPDX-FileCopyrightText: 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT
#
# SPDX-License-Identifier: Apache-2.0

from Deeploy.Targets.PULPOpen.Deployer import PULPDeployer


class OpenTitanClusterDeployer(PULPDeployer):
    """PULPDeployer without the flash loading of L3 constants: on the OT cluster they are
    PI_L3 initialised arrays (OpenTitanClusterConstantBuffer) preloaded with the ELF."""

    def generateBufferAllocationCode(self) -> str:
        return super(PULPDeployer, self).generateBufferAllocationCode()
