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
# add_gvsoc_emulation(${ProjectId} "pulp-open") --> NO GVSOC EMULATION FOR PULP OPEN + 32-bits iDMA YET
# The two subsystems have incompatible testbenches, not merely different paths:
# pulp-open loads L2 over emulated JTAG from $PULP_OPEN_HOME/sim/vectors, the
# standalone cluster reads the ELF directly. Same target names either way, so
# --simulator vsim/qsim works on both.
if(PULP_HAS_FC)
  add_pulp_open_vsim_simulation(${ProjectId})
  add_pulp_open_qsim_simulation(${ProjectId})
  add_pulp_open_fpga_bin_generation(${ProjectId})
else()
  add_pulp_cluster_vsim_simulation(${ProjectId})
  add_pulp_cluster_qsim_simulation(${ProjectId})
endif()
link_compile_dump(${TESTNAME})