# SPDX-FileCopyrightText: 2025 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

# Standalone build of pulp-nn-mixed for the PULP platforms. The installed library is picked up by
# Deeploy builds with USE_PREBUILT_PULPNN=ON (see TargetLibraries/PULPOpen/CMakeLists.txt), so it does
# not have to be compiled for every test. Normally used through `make pulp-nn-mixed`.
#
# Required: -Dplatform=<PULPOpen|Siracusa|Siracusa_w_neureka> -DNUM_CORES=<n>
#           -DTOOLCHAIN=<LLVM|GCC> -DTOOLCHAIN_INSTALL_DIR=<dir>, and PULP_SDK_HOME in the environment.
# Optional: -DPULPNN_INSTALL_ROOT=<dir> (default: <Deeploy>/install/pulp-nn-mixed).
#
# `cmake --install` puts libpulp-nn-mixed.a and include/ in
# <PULPNN_INSTALL_ROOT>/<platform>-<toolchain>-<NUM_CORES>cores.
#
# The setup mirrors the PULP branch of the top-level CMakeLists.txt, so the library is compiled with
# the same flags as when it is built from source inside a Deeploy build.

cmake_minimum_required(VERSION 3.19)

get_filename_component(DEEPLOY_ROOT ${CMAKE_CURRENT_LIST_DIR}/../../.. ABSOLUTE)

if(NOT platform MATCHES "^(PULPOpen|Siracusa|Siracusa_w_neureka)$")
  message(FATAL_ERROR "[pulp-nn-mixed] Unsupported platform '${platform}' (PULPOpen, Siracusa, Siracusa_w_neureka)")
endif()
if(NOT NUM_CORES)
  message(FATAL_ERROR "[pulp-nn-mixed] NUM_CORES not set")
endif()
if(NOT DEFINED ENV{PULP_SDK_HOME})
  message(FATAL_ERROR "[pulp-nn-mixed] Environment variable PULP_SDK_HOME not set.")
endif()

set(CMAKE_C_STANDARD 99)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

find_program(CCACHE_PROGRAM ccache)
if(CCACHE_PROGRAM)
  set(CMAKE_C_COMPILER_LAUNCHER ${CCACHE_PROGRAM})
endif()

if(TOOLCHAIN STREQUAL GCC)
  set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
endif()

include(${DEEPLOY_ROOT}/cmake/common.cmake)

if(TOOLCHAIN STREQUAL LLVM)
  set(CMAKE_TOOLCHAIN_FILE ${DEEPLOY_ROOT}/cmake/pulp/toolchain_llvm.cmake)
else()
  set(CMAKE_TOOLCHAIN_FILE ${DEEPLOY_ROOT}/cmake/pulp/toolchain_gcc.cmake)
endif()

include(${DEEPLOY_ROOT}/cmake/pulp/pulp.cmake)

if(platform STREQUAL Siracusa OR platform STREQUAL Siracusa_w_neureka)
  include(${DEEPLOY_ROOT}/cmake/pulp/siracusa/siracusa.cmake)
else()
  include(${DEEPLOY_ROOT}/cmake/pulp/pulp-open/pulp-open.cmake)
endif()

project(pulp-nn-mixed-prebuilt LANGUAGES C ASM)

# Provides PULP_SDK_INCLUDES and PULP_SDK_COMPILE_FLAGS, used by the pulp-nn-mixed CMakeLists.txt.
# The pulp-sdk object libraries it also defines are not built: only the pulp-nn-mixed target is.
if(platform STREQUAL Siracusa OR platform STREQUAL Siracusa_w_neureka)
  include(${DEEPLOY_ROOT}/TargetLibraries/PULPOpen/cmake/pulp-sdk-siracusa.cmake)
else()
  include(${DEEPLOY_ROOT}/TargetLibraries/PULPOpen/cmake/pulp-sdk-pulp-open.cmake)
endif()

# Same as the build from source in TargetLibraries/PULPOpen/CMakeLists.txt
add_subdirectory(${DEEPLOY_ROOT}/TargetLibraries/third_party/pulp-nn-mixed ${CMAKE_CURRENT_BINARY_DIR}/pulp-nn-mixed)
target_compile_options(pulp-nn-mixed PRIVATE -Wno-error)
target_compile_definitions(pulp-nn-mixed PUBLIC NUM_CORES=${NUM_CORES})

include(${DEEPLOY_ROOT}/TargetLibraries/PULPOpen/cmake/pulp-nn-mixed-prebuilt.cmake)
set(PULPNN_INSTALL_ROOT ${DEEPLOY_ROOT}/install/pulp-nn-mixed CACHE PATH "Root folder of the prebuilt pulp-nn-mixed libraries")
set(PULPNN_INSTALL_DIR ${PULPNN_INSTALL_ROOT}/${PULPNN_PREBUILT_SUBDIR})

install(TARGETS pulp-nn-mixed ARCHIVE DESTINATION ${PULPNN_INSTALL_DIR})
foreach(_include IN LISTS PULPNN_INCLUDES)
  install(DIRECTORY ${_include}/ DESTINATION ${PULPNN_INSTALL_DIR}/include)
endforeach()

message(STATUS "[pulp-nn-mixed] Install folder: ${PULPNN_INSTALL_DIR}")
