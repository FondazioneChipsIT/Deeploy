# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

set(ProjectId ${TESTNAME})

file(GLOB_RECURSE SOURCES
    src/CycleCounter.c
    src/deeploytest.c
)

add_deeploy_executable(${ProjectId} EXCLUDE_FROM_ALL ${SOURCES})
target_include_directories(${ProjectId} PRIVATE ${CMAKE_CURRENT_LIST_DIR}/inc)

target_link_libraries(${ProjectId} PRIVATE network deeploylib)

# GVSoC pulp-open cluster L1 (TCDM) size, 256 KB as in the pulp_fpga RTL
set(GVSOC_L1_SIZE 0x40000 CACHE STRING "GVSoC pulp-open cluster L1 size in bytes")
list(APPEND GVSOC_EXTRA_FLAGS --target-property chip/cluster/l1_size=${GVSOC_L1_SIZE})
add_gvsoc_emulation(${ProjectId} "pulp-open")
add_pulp_open_vsim_simulation(${ProjectId})
add_pulp_open_qsim_simulation(${ProjectId})
link_compile_dump(${TESTNAME})
