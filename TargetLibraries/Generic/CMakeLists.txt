# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

file(GLOB_RECURSE SOURCES
    "src/**"
)

# TEMPORARY: corev-llvm 23 emits a hardware loop here that the assembler rejects
# ("loop offset must be a multiple of 4"); the only such file in the tree, so
# hardware loops stay on everywhere else. Remove once the toolchain is fixed.
if(PULP_CORE STREQUAL cv32e40p AND TOOLCHAIN STREQUAL LLVM)
  set_source_files_properties(${CMAKE_CURRENT_LIST_DIR}/src/Gemm_s8.c
    PROPERTIES COMPILE_OPTIONS "-mllvm;-hwloops-disable")
endif()

add_deeploy_library(deeploybasic STATIC ${SOURCES})

target_include_directories(deeploybasic
    PUBLIC
    ${CMAKE_CURRENT_LIST_DIR}/inc
)
