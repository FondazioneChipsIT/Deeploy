# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

set(PULP_SDK_HOME $ENV{PULP_SDK_HOME})

set(PULP_SDK_BASE_C_SOURCE
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/ram/ram.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/ram/alloc_extern.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/ram/hyperram/hyperram.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/fs/read_fs/read_fs.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/fs/host_fs/semihost.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/fs/host_fs/host_fs.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/fs/fs.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/flash/hyperflash/hyperflash.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/flash/flash.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/partition/partition.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/partition/flash_partition.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/crc/md5.c
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/bsp/siracusa.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/init.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/kernel.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/device.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/task.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/alloc.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/alloc_pool.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/irq.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/soc_event.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/log.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/time.c
  ${PULP_SDK_HOME}/rtos/pulpos/pulp/drivers/hyperbus/hyperbus-v3.c
  ${PULP_SDK_HOME}/rtos/pulpos/pulp/drivers/uart/uart-v1.c
  ${PULP_SDK_HOME}/rtos/pulpos/pulp/drivers/udma/udma-v3.c
  ${PULP_SDK_HOME}/rtos/pulpos/pulp/drivers/cluster/cluster.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/lib/libc/minimal/io.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/lib/libc/minimal/fprintf.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/lib/libc/minimal/prf.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/lib/libc/minimal/sprintf.c
  ${PULP_SDK_HOME}/rtos/pulpos/common/lib/libc/minimal/semihost.c
)

set(PULP_SDK_BASE_ASM_SOURCE
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/crt0.S
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/irq_asm.S
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/task_asm.S
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/time_asm.S
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/soc_event_v2_itc.S
  ${PULP_SDK_HOME}/rtos/pulpos/pulp/drivers/cluster/pe-eu-v3.S
)

set(PULP_SDK_BASE_INCLUDE
  ${PULP_SDK_HOME}/rtos/pulpos/common/lib/libc/minimal/include
  ${PULP_SDK_HOME}/rtos/pulpos/common/include
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel
  ${PULP_SDK_HOME}/rtos/pulpos/pulp_archi/include
  ${PULP_SDK_HOME}/rtos/pulpos/pulp_hal/include
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_api/include
  ${PULP_SDK_HOME}/rtos/pulpos/pulp/include
  ${PULP_SDK_HOME}/rtos/pmsis/pmsis_bsp/include
)

# The SDK's own core switch, mirroring the USE_CV32E40P arm of pulp.mk. __riscv__
# means "RI5CY/xpulpv2", and gates code calling __builtin_pulp_* directly.
if(PULP_CORE STREQUAL cv32e40p)
  set(PULP_SDK_CORE_FLAGS -U__riscv__ -D__cv32e40p__)
else()
  set(PULP_SDK_CORE_FLAGS -D__riscv__)
endif()

# The SDK's CONFIG_NO_FC, i.e. cluster core 0 emulates the FC. Chip-derived, not a
# knob. Only chips/pulp/properties.h honours it -- chips/siracusa/properties.h
# defines the FC macros unconditionally, so setting it there is incoherent, not
# merely different.
if(PULP_HAS_FC)
  set(PULP_SDK_FC_FLAGS)
else()
  set(PULP_SDK_FC_FLAGS -DARCHI_NO_FC=1)
endif()

set(PULP_SDK_BASE_COMPILE_FLAGS
  ${PULP_SDK_CORE_FLAGS}
  ${PULP_SDK_FC_FLAGS}
  -D__CONFIG_UDMA__
  -D__PULPOS2__
  -DARCHI_CLUSTER_NB_PE=8
  -D__TRACE_LEVEL__=3
  -DPI_LOG_LOCAL_LEVEL=2
  -D__PLATFORM__=ARCHI_PLATFORM_${SDK_PLATFORM}
  -D__PLATFORM_${SDK_PLATFORM}__
)

set_source_files_properties(${PULP_SDK_BASE_ASM_SOURCE} PROPERTIES COMPILE_FLAGS -DLANGUAGE_ASSEMBLY)

# pos_init_do_ctors() reads off the end of a 1-element array and relies on linker
# placement -- UB that LTO is entitled to fold away. Cold init code, nothing to gain.
set_source_files_properties(
  ${PULP_SDK_HOME}/rtos/pulpos/common/kernel/init.c
  PROPERTIES COMPILE_OPTIONS -fno-lto
)

add_library(pulp-sdk-base OBJECT ${PULP_SDK_BASE_C_SOURCE} ${PULP_SDK_BASE_ASM_SOURCE})
