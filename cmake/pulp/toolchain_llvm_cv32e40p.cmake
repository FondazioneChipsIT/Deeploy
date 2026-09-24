# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

# corev-llvm toolchain for PULP_CORE=cv32e40p, mirroring the USE_CV32E40P arm of the
# SDK's pulp.mk. Needs -DTOOLCHAIN=LLVM -DTOOLCHAIN_INSTALL_DIR=<corev-llvm>: a stock
# clang has neither the xcv* extensions nor zfinx.

# try_compile() re-reads this file in a scope where -D cache vars are invisible.
list(APPEND CMAKE_TRY_COMPILE_PLATFORM_VARIABLES platform TOOLCHAIN_INSTALL_DIR)
include(${CMAKE_CURRENT_LIST_DIR}/pulp_platforms.cmake)

if(NOT TOOLCHAIN_INSTALL_DIR)
  message(FATAL_ERROR "TOOLCHAIN_INSTALL_DIR is not set; ${platform} needs a corev-llvm install")
endif()

set(TOOLCHAIN_PREFIX ${TOOLCHAIN_INSTALL_DIR}/bin)

# As in pulp.mk, an exported RISCV_SYSROOT wins; else newlib sits under
# riscv32-unknown-elf/, or at the root in older layouts.
if(DEFINED ENV{RISCV_SYSROOT})
  set(CV32_SYSROOT $ENV{RISCV_SYSROOT})
elseif(EXISTS ${TOOLCHAIN_INSTALL_DIR}/riscv32-unknown-elf/lib)
  set(CV32_SYSROOT ${TOOLCHAIN_INSTALL_DIR}/riscv32-unknown-elf)
else()
  set(CV32_SYSROOT ${TOOLCHAIN_INSTALL_DIR})
endif()

if(NOT EXISTS ${CV32_SYSROOT}/lib/libc.a)
  message(FATAL_ERROR
    "No libc.a under ${CV32_SYSROOT}/lib; set RISCV_SYSROOT to the newlib sysroot "
    "of ${TOOLCHAIN_INSTALL_DIR}")
endif()

set(CMAKE_SYSTEM_NAME Generic)

set(CMAKE_C_COMPILER   ${TOOLCHAIN_PREFIX}/clang)
set(CMAKE_CXX_COMPILER ${TOOLCHAIN_PREFIX}/clang++)
set(CMAKE_ASM_COMPILER ${TOOLCHAIN_PREFIX}/clang)
set(CMAKE_OBJCOPY ${TOOLCHAIN_PREFIX}/llvm-objcopy)
set(CMAKE_OBJDUMP ${TOOLCHAIN_PREFIX}/llvm-objdump)
set(CMAKE_AR ${TOOLCHAIN_PREFIX}/llvm-ar)
set(SIZE ${TOOLCHAIN_PREFIX}/llvm-size)

# Full CV32E40P ISA, same string as the SDK.
string(JOIN "_" ISA ${PULP_CV32_BASE_ISA} ${PULP_CV32_EXTENSIONS})
set(ABI ${PULP_CV32_ABI})
set(PE 8)

# TEMPORARY: two corev-llvm 23 codegen bugs, each confined to a few files and worked
# around where those are built rather than by weakening the ISA tree-wide. Drop both
# once the toolchain is fixed.
#   xcvmem  -- ISel abort on the post-increment loads it forms in pulp-nn's sub-byte
#              Add kernels; they build with CV32_ISA_NO_XCVMEM below.
#   xcvhwlp -- assembler rejects a hardware loop it emits in Gemm_s8.c.
set(CV32_EXTENSIONS_NO_XCVMEM ${PULP_CV32_EXTENSIONS})
list(REMOVE_ITEM CV32_EXTENSIONS_NO_XCVMEM xcvmem)
string(JOIN "_" CV32_ISA_NO_XCVMEM ${PULP_CV32_BASE_ISA} ${CV32_EXTENSIONS_NO_XCVMEM})

set(CMAKE_EXECUTABLE_SUFFIX ".elf")

# Fail here, not on the first source file, if this is not a corev-llvm.
execute_process(
  COMMAND ${CMAKE_C_COMPILER} -target riscv32-unknown-elf -march=${ISA} -mabi=${ABI}
          --sysroot=${CV32_SYSROOT} -E -x c /dev/null
  RESULT_VARIABLE CV32_MARCH_RESULT
  ERROR_VARIABLE CV32_MARCH_ERROR
  OUTPUT_QUIET
)
if(NOT CV32_MARCH_RESULT EQUAL 0)
  message(FATAL_ERROR
    "${CMAKE_C_COMPILER} rejects -march=${ISA}; ${platform} needs a corev-llvm "
    "install (CORE-V xcv* + zfinx).\n${CV32_MARCH_ERROR}")
endif()

execute_process(
  COMMAND ${CMAKE_C_COMPILER} --version
  OUTPUT_VARIABLE CV32_CLANG_VERSION
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_QUIET
)
string(REGEX MATCH "clang version [^ \n]+" CV32_CLANG_TAG "${CV32_CLANG_VERSION}")
message(STATUS "[CV32E40P] ${CMAKE_C_COMPILER} (${CV32_CLANG_TAG})")
message(STATUS "[CV32E40P] sysroot ${CV32_SYSROOT}")

add_compile_options(
  -target riscv32-unknown-elf
  -march=${ISA}
  -mabi=${ABI}
  --sysroot=${CV32_SYSROOT}
  -isystem ${CV32_SYSROOT}/include
  -ffunction-sections
  -fdata-sections
  -fomit-frame-pointer
  -fno-jump-tables
  -O3
  -DNUM_CORES=${NUM_CORES}
  -MMD
  -MP
  # pulp_nn_utils.h assigns its pack() result to both v4s and v4u.
  -flax-vector-conversions
  # Errors since clang 15; the SDK and pulp-nn still trip them.
  -Wno-error=implicit-function-declaration
  -Wno-error=int-conversion
  -Wno-error=incompatible-pointer-types
)

# No -nostdlib: unlike corev-gcc, this path links the sysroot's newlib. compiler-rt
# is explicit because --rtlib defaults to libgcc, which corev-llvm does not ship.
add_link_options(
  -target riscv32-unknown-elf
  -march=${ISA}
  -mabi=${ABI}
  --sysroot=${CV32_SYSROOT}
  -MMD
  -MP
  -nostartfiles
  -fuse-ld=lld
  --rtlib=compiler-rt
  -Wl,--gc-sections
  -L${CV32_SYSROOT}/lib
)

link_libraries(
  -lc
  -lm
)

add_compile_definitions(__LINK_LD)
add_compile_definitions(__TOOLCHAIN_LLVM__)
