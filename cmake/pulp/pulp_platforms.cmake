# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

# Single source of truth for the PULP platform family.
#
# Naming rule: the bare name is that subsystem's canonical configuration, and each
# suffix names one deviation from it. PULPOpen is the FC-bearing SoC (canonical DMA
# Mchan, so _iDMA is the deviation); PULPCluster is the headless standalone cluster
# (canonical core RI5CY, so _CV32E40P is the deviation).
#
# | platform                   | chip              | FC | DMA   | core     | toolchains |
# |----------------------------|-------------------|----|-------|----------|------------|
# | Siracusa                   | siracusa          | y  | Mchan | RI5CY    | LLVM, GCC  |
# | Siracusa_w_neureka         | siracusa          | y  | Mchan | RI5CY    | LLVM, GCC  |
# | PULPOpen                   | pulp              | y  | Mchan | RI5CY    | LLVM, GCC  |
# | PULPOpen_iDMA              | pulp              | y  | iDMA  | RI5CY    | LLVM, GCC  |
# | PULPCluster_iDMA           | pulp              | n  | iDMA  | RI5CY    | LLVM, GCC  |
# | PULPCluster_iDMA_CV32E40P  | pulp              | n  | iDMA  | CV32E40P | GCC        |
# | OpenTitanCluster_iDMA      | opentitan_cluster | n  | iDMA  | RI5CY    | GCC        |
#
# PULPCluster == the SDK's configs/pulp_cluster.sh (CONFIG_NO_FC=1).
# OpenTitanCluster == configs/opentitan_cluster.sh: same cluster in the OT secure domain (build only).
#
# DMA has no variable here: it is the one axis that changes the generated
# Network.c, so platformMapping.py owns it.
#
# Also included from the toolchain files, so read only `platform` and set only
# PULP_* names -- never ISA/FC/PE, which those files re-set at project() time.

# The CV32E40P ISA/ABI, mirroring PULP_CV32_MARCH in the SDK's pulp.mk. A list so a
# toolchain file can drop a single extension it cannot handle. zfinx rather than f:
# the core keeps floats in the integer regfile, hence ilp32 and not ilp32f.
set(PULP_CV32_BASE_ISA rv32imc)
set(PULP_CV32_EXTENSIONS xcvalu xcvbi xcvbitmanip xcvhwlp xcvmac xcvmem xcvsimd xcvelw zfinx)
set(PULP_CV32_ABI ilp32)

set(PULP_IS_PULP_PLATFORM TRUE)

if(platform STREQUAL Siracusa OR platform STREQUAL Siracusa_w_neureka)
  set(PULP_CHIP siracusa)
  set(PULP_HAS_FC ON)
  set(PULP_CORE ri5cy)
  set(PULP_HARNESS_DIR Siracusa)
elseif(platform STREQUAL PULPOpen)
  set(PULP_CHIP pulp)
  set(PULP_HAS_FC ON)
  set(PULP_CORE ri5cy)
  set(PULP_HARNESS_DIR PULPOpen)
elseif(platform STREQUAL PULPOpen_iDMA)
  set(PULP_CHIP pulp)
  set(PULP_HAS_FC ON)
  set(PULP_CORE ri5cy)
  set(PULP_HARNESS_DIR PULPOpen_iDMA)
elseif(platform STREQUAL PULPCluster_iDMA)
  set(PULP_CHIP pulp)
  set(PULP_HAS_FC OFF)
  set(PULP_CORE ri5cy)
  set(PULP_HARNESS_DIR PULPOpen_iDMA)
elseif(platform STREQUAL PULPCluster_iDMA_CV32E40P)
  set(PULP_CHIP pulp)
  set(PULP_HAS_FC OFF)
  set(PULP_CORE cv32e40p)
  set(PULP_HARNESS_DIR PULPOpen_iDMA)
elseif(platform STREQUAL OpenTitanCluster_iDMA)
  set(PULP_CHIP opentitan_cluster)
  set(PULP_HAS_FC OFF)
  set(PULP_CORE ri5cy)
  set(PULP_HARNESS_DIR OpenTitanCluster)
else()
  set(PULP_IS_PULP_PLATFORM FALSE)
endif()
