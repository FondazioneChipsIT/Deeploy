# SPDX-FileCopyrightText: 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT
#
# SPDX-License-Identifier: Apache-2.0

set(ProjectId ${TESTNAME})

# CycleCounter is shared with PULPOpen_iDMA (same cluster perf counters)
set(PULP_IDMA_HARNESS ${CMAKE_CURRENT_LIST_DIR}/../PULPOpen_iDMA)

add_deeploy_executable(${ProjectId} EXCLUDE_FROM_ALL
  src/deeploytest.c
  ${PULP_IDMA_HARNESS}/src/CycleCounter.c
)
target_include_directories(${ProjectId} PRIVATE ${PULP_IDMA_HARNESS}/inc)

target_link_libraries(${ProjectId} PRIVATE network deeploylib)

# Build only: the OT host offloads the ELF, no simulation targets
link_compile_dump(${TESTNAME})
