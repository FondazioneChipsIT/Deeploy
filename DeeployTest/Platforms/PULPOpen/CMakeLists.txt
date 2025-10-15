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
<<<<<<< HEAD
# add_gvsoc_emulation(${ProjectId} "pulp-open") --> NO GVSOC EMULATION FOR PULP OPEN + 32-bits iDMA YET
=======
add_gvsoc_emulation(${ProjectId} "pulp-open")
>>>>>>> 89f98de (First changes for pulp-open rtl simulation inside Deeploy)
add_pulp_open_vsim_simulation(${ProjectId})
link_compile_dump(${TESTNAME})
