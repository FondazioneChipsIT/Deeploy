# SPDX-FileCopyrightText: 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT
#
# SPDX-License-Identifier: Apache-2.0

# PULP cluster in the OpenTitan secure domain: the SDK's opentitan_cluster chip.
# No FLL, no hyperram/hyperflash (no L3); printf goes to the host (Cheshire) UART.

include(cmake/pulp-sdk-base.cmake)

set(PULP_SDK_HOME $ENV{PULP_SDK_HOME})

set(OT_CLUSTER_COMPILE_FLAGS
  -include ${PULP_SDK_HOME}/rtos/pulpos/pulp/include/pos/chips/opentitan_cluster/config.h
  -DCONFIG_PULP
  -DCONFIG_BOARD_VERSION_PULP
  -DCONFIG_PROFILE_PULP
  -DPULP_CHIP_STR=opentitan_cluster
  -DPOS_CONFIG_IO_HOST_UART=1
  -DDEEPLOY_NO_L3
)

set(OT_CLUSTER_INCLUDES
  ${PULP_SDK_HOME}/rtos/pulpos/pulp/include/pos/chips/opentitan_cluster
)

set(PULP_SDK_OT_CLUSTER_C_SOURCE
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/freq-domains.c
  ${PULP_SDK_HOME}/rtos/pulpos/pulp/kernel/chips/opentitan_cluster/soc.c
)

add_library(pulp-sdk OBJECT ${PULP_SDK_BASE_C_SOURCE} ${PULP_SDK_BASE_ASM_SOURCE} ${PULP_SDK_OT_CLUSTER_C_SOURCE})

set(PULP_SDK_COMPILE_FLAGS ${OT_CLUSTER_COMPILE_FLAGS} ${PULP_SDK_BASE_COMPILE_FLAGS})
set(PULP_SDK_INCLUDES ${OT_CLUSTER_INCLUDES} ${PULP_SDK_BASE_INCLUDE})

target_include_directories(pulp-sdk SYSTEM PUBLIC ${PULP_SDK_INCLUDES})
target_compile_options(pulp-sdk PUBLIC ${PULP_SDK_COMPILE_FLAGS})
target_compile_options(pulp-sdk PRIVATE
  -O3
  -Wno-sign-conversion
  -Wno-unused-function
  -Wno-unused-parameter
  -Wno-conversion
  -Wno-sign-conversion
  -Wno-unused-variable
  -Wno-sign-compare
  -Wno-return-type
  -fno-inline-functions
)
target_compile_options(pulp-sdk INTERFACE
  -Wno-unused-function
)

target_link_libraries(pulp-sdk PUBLIC
  -Wl,--gc-sections
  -L${PULP_SDK_HOME}/rtos/pulpos/pulp/kernel
  -Tchips/opentitan_cluster/link.ld
)
