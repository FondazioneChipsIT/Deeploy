# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

# corev-gcc toolchain for PULP_CORE=cv32e40p. Separate file rather than a branch in
# toolchain_gcc.cmake so the RI5CY platforms stay untouched.
# Needs -DTOOLCHAIN=GCC -DTOOLCHAIN_INSTALL_DIR=<corev-gcc>, not pulp-gcc.

list(APPEND CMAKE_TRY_COMPILE_PLATFORM_VARIABLES TOOLCHAIN_INSTALL_DIR)

if(NOT TOOLCHAIN_INSTALL_DIR)
  message(FATAL_ERROR "TOOLCHAIN_INSTALL_DIR is not set; ${platform} needs a corev-gcc install")
endif()

if(EXISTS ${TOOLCHAIN_INSTALL_DIR}/bin/riscv32-unknown-elf-gcc)
  set(TOOLCHAIN_PREFIX ${TOOLCHAIN_INSTALL_DIR}/bin/riscv32-unknown-elf)
else()
  set(TOOLCHAIN_PREFIX ${TOOLCHAIN_INSTALL_DIR}/bin/riscv64-unknown-elf)
endif()

set(CMAKE_SYSTEM_NAME Generic)

set(CMAKE_C_COMPILER ${TOOLCHAIN_PREFIX}-gcc)
set(CMAKE_CXX_COMPILER ${TOOLCHAIN_PREFIX}-g++)
set(CMAKE_ASM_COMPILER ${CMAKE_C_COMPILER})
set(CMAKE_OBJCOPY ${TOOLCHAIN_PREFIX}-objcopy)
set(CMAKE_OBJDUMP ${TOOLCHAIN_PREFIX}-objdump)
set(CMAKE_AR ${TOOLCHAIN_PREFIX}-ar)
set(SIZE ${TOOLCHAIN_PREFIX}-size)

set(ISA rv32imc_xcvalu_xcvbi_xcvbitmanip_xcvhwlp_xcvmac_xcvmem_xcvsimd_xcvelw_zfinx)
set(ABI ilp32)
set(PE 8)

# -mtune=cv32e40p only exists in newer corev-gcc builds; sniff it as pulp.mk does.
execute_process(
  COMMAND ${CMAKE_C_COMPILER} -mtune=cv32e40p -E -x c /dev/null
  RESULT_VARIABLE CV32_TUNE_RESULT
  OUTPUT_QUIET ERROR_QUIET
)
if(CV32_TUNE_RESULT EQUAL 0)
  set(CV32_TUNE_FLAGS -mtune=cv32e40p)
else()
  set(CV32_TUNE_FLAGS)
endif()

set(CMAKE_EXECUTABLE_SUFFIX ".elf")

# No libgcc/libm multilib matches rv32imfc + xcv* + ilp32f, so the driver falls back
# to the rv64 default and the link dies on an ABI mismatch. Point it at the closest
# compatible copies, as pulp.mk does.
set(CV32_COMPAT_ARCH -march=rv32imafc -mabi=ilp32f)

execute_process(
  COMMAND ${CMAKE_C_COMPILER} ${CV32_COMPAT_ARCH} -print-libgcc-file-name
  OUTPUT_VARIABLE CV32_LIBGCC_PATH
  OUTPUT_STRIP_TRAILING_WHITESPACE
  RESULT_VARIABLE CV32_LIBGCC_RESULT
)
if(NOT CV32_LIBGCC_RESULT EQUAL 0 OR NOT CV32_LIBGCC_PATH)
  message(FATAL_ERROR "Could not query libgcc from ${CMAKE_C_COMPILER}; is ${TOOLCHAIN_INSTALL_DIR} a corev-gcc install?")
endif()
get_filename_component(CV32_LIBGCC_DIR ${CV32_LIBGCC_PATH} DIRECTORY)

execute_process(
  COMMAND ${CMAKE_C_COMPILER} ${CV32_COMPAT_ARCH} -print-file-name=libm.a
  OUTPUT_VARIABLE CV32_LIBM_PATH
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
get_filename_component(CV32_LIBM_DIR ${CV32_LIBM_PATH} DIRECTORY)

execute_process(
  COMMAND ${CMAKE_C_COMPILER} --version
  OUTPUT_VARIABLE CV32_GCC_VERSION
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_QUIET
)
string(REGEX MATCH "\\(g[0-9a-f]+\\)" CV32_GCC_PKGVERSION "${CV32_GCC_VERSION}")
message(STATUS "[CV32E40P] ${CMAKE_C_COMPILER} ${CV32_GCC_PKGVERSION}")
message(STATUS "[CV32E40P] libgcc ${CV32_LIBGCC_DIR}")
message(STATUS "[CV32E40P] libm   ${CV32_LIBM_DIR}")

add_compile_options(
  -march=${ISA}
  -mabi=${ABI}
  ${CV32_TUNE_FLAGS}
  -ffunction-sections
  -fdata-sections
  -fomit-frame-pointer
  -fno-jump-tables
  -fno-tree-loop-distribute-patterns
  -O3
  -DNUM_CORES=${NUM_CORES}
  -MMD
  -MP
  # GCC 14 made implicit-decl / int-conversion errors;
  -fpermissive
  # pulp_nn_utils.h assigns its pack() result to both v4s and v4u.
  -flax-vector-conversions
)

add_link_options(
  -MMD
  -MP
  -march=${ISA}
  -mabi=${ABI}
  -nostartfiles
  -nostdlib
  -Wl,--gc-sections
  #-L${CV32_LIBGCC_DIR}
  -L${CV32_LIBM_DIR}
)

link_libraries(
  -lm
  -lgcc
)

add_compile_definitions(__LINK_LD)
add_compile_definitions(__TOOLCHAIN_GCC__)
