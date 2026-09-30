# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

file(GLOB_RECURSE SOURCES
  "src/**"
)

if(NOT DEFINED ENV{PULP_SDK_HOME})
  message(FATAL_ERROR "Environment variable PULP_SDK_HOME not set.")
endif()

if(PULP_CHIP STREQUAL siracusa)
  include(cmake/pulp-sdk-siracusa.cmake)
elseif(PULP_CHIP STREQUAL opentitan_cluster)
  include(cmake/pulp-sdk-opentitan-cluster.cmake)
else()
  include(cmake/pulp-sdk-pulp-open.cmake)
endif()

add_deeploy_library(deeploypulp STATIC ${SOURCES})
target_include_directories(deeploypulp
  PUBLIC
  ${CMAKE_CURRENT_LIST_DIR}/inc
)

target_compile_options(deeploypulp PRIVATE
  -Wno-implicit-function-declaration
  -Wno-implicit-int-conversion
  -Wno-sign-conversion
  -Wno-sign-compare
  -Wno-typedef-redefinition
  -Wno-unused-parameter
  -Wno-unused-function
  -Wno-unused-variable
  -Wno-uninitialized
)

target_include_directories(deeploypulp PUBLIC ${PULP_SDK_INCLUDES})
target_compile_options(deeploypulp PUBLIC ${PULP_SDK_COMPILE_FLAGS})

add_subdirectory(../third_party/pulp-nn-mixed ${CMAKE_CURRENT_BINARY_DIR}/pulp-nn-mixed)
target_include_directories(pulp-nn-mixed PUBLIC ${PULP_SDK_INCLUDES})
target_compile_options(pulp-nn-mixed PUBLIC ${PULP_SDK_COMPILE_FLAGS})

# TEMPORARY: corev-llvm 23 cannot select the post-increment loads it forms from these
# kernels' sub-byte unpack helpers ("Cannot select: load <post-inc>"), 197 of 222 of
# them. Only this directory gives up xcvmem; per-source options come last, so this
# -march wins over the toolchain's. Remove once the toolchain is fixed.
if(PULP_CORE STREQUAL cv32e40p AND TOOLCHAIN STREQUAL LLVM)
  file(GLOB PULP_NN_ADD_SOURCES
    ${CMAKE_CURRENT_LIST_DIR}/../third_party/pulp-nn-mixed/XpulpV2/32bit/src/Add/*.c)
  set_source_files_properties(${PULP_NN_ADD_SOURCES}
    TARGET_DIRECTORY pulp-nn-mixed
    PROPERTIES COMPILE_OPTIONS -march=${CV32_ISA_NO_XCVMEM})
endif()

target_link_libraries(deeploypulp PUBLIC pulp-nn-mixed)
target_link_libraries(deeploypulp INTERFACE pulp-sdk)
target_sources(deeploypulp INTERFACE $<TARGET_OBJECTS:pulp-sdk>)

if(PULP_CHIP STREQUAL siracusa)
  set(USE_NEUREKA ON)
  add_subdirectory(../third_party/pulp-nnx ${CMAKE_CURRENT_BINARY_DIR}/pulp-nnx)
  target_include_directories(pulp-nnx PUBLIC ${PULP_SDK_INCLUDES})
  target_compile_options(pulp-nnx PUBLIC ${PULP_SDK_COMPILE_FLAGS})
    target_compile_options(pulp-nnx PRIVATE
    -Wno-implicit-int-conversion
    -Wno-sign-conversion
    -Wno-typedef-redefinition
    -Wno-unused-parameter
    -Wno-incompatible-pointer-types-discards-qualifiers
    )
  target_link_libraries(deeploypulp INTERFACE pulp-nnx)
endif()
