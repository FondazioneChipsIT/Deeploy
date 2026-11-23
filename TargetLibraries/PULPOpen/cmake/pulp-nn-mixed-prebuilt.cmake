# SPDX-FileCopyrightText: 2025 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

# Name of the folder a prebuilt pulp-nn-mixed is installed into, relative to the install root.
#
# Shared by TargetLibraries/PULPOpen/CMakeLists.txt (lookup) and
# TargetLibraries/PULPOpen/pulp-nn-mixed-prebuilt/CMakeLists.txt (build and install), so both agree.
#
# The library depends on the ISA/ABI (PULP-Open is rv32imc_zfinx/ilp32, Siracusa rv32imf/ilp32f),
# on the toolchain and on NUM_CORES, so there is one folder per combination.
# Siracusa_w_neureka uses the same toolchain settings as Siracusa and shares its library.

if(platform STREQUAL "Siracusa_w_neureka")
  set(_pulpnn_platform Siracusa)
else()
  set(_pulpnn_platform ${platform})
endif()

# Same rule as the top-level CMakeLists.txt: anything but LLVM selects the GCC toolchain
if(TOOLCHAIN STREQUAL LLVM)
  set(_pulpnn_toolchain LLVM)
else()
  set(_pulpnn_toolchain GCC)
endif()

set(PULPNN_PREBUILT_SUBDIR ${_pulpnn_platform}-${_pulpnn_toolchain}-${NUM_CORES}cores)
