# SPDX-FileCopyrightText: 2025 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0
"""Test configuration for PULPOpen_iDMA platform with Neureka accelerator (tiled)."""

PLATFORM_NAME = "PULPOpen_iDMA_Neureka"
SIMULATOR = "qsim"
DEFAULT_CORES = 8

# L2 single-buffer kernel tests
# Format: dict of {test_name: [L1_sizes]}
L2_SINGLEBUFFER_KERNELS = {
    "Kernels/Integer/GEMM/Regular_RQPerColumn": [16000],
    "Kernels/Integer/Conv/PW_2D": [32000],
    "Kernels/Integer/Conv/PW_2D_RQ/Regular_RQ": [32000],
    "Kernels/Integer/Conv/PW_2D_RQ/Unsigned_RQ": [32000],
}

# L2 double-buffer kernel tests
L2_DOUBLEBUFFER_KERNELS = {
    "Kernels/Integer/GEMM/Regular_RQPerColumn": [16000],
    "Kernels/Integer/Conv/PW_2D": [32000],
    "Kernels/Integer/Conv/PW_2D_RQ/Regular_RQ": [32000],
    "Kernels/Integer/Conv/PW_2D_RQ/Unsigned_RQ": [32000],
}

# L2 single-buffer kernel tests with weight memory (neureka-wmem)
L2_SINGLEBUFFER_KERNELS_WMEM = {
    "Kernels/Integer/GEMM/Regular_RQPerColumn": [16000],
    "Kernels/Integer/Conv/PW_2D": [32000],
    "Kernels/Integer/Conv/PW_2D_RQ/Regular_RQ": [32000],
    "Kernels/Integer/Conv/PW_2D_RQ/Unsigned_RQ": [32000],
}

# L2 single-buffer model tests
L2_SINGLEBUFFER_MODELS = {
    "Models/miniMobileNet": [16000, 8000],
    "Kernels/Integer/Attention": [32000, 16000],
}

# L2 double-buffer model tests
L2_DOUBLEBUFFER_MODELS = {
    "Models/miniMobileNet": [32000, 16000],
    "Kernels/Integer/Attention": [64000, 32000],
}

# L2 double-buffer model tests with weight memory (neureka-wmem)
L2_DOUBLEBUFFER_MODELS_WMEM = {
    "Models/miniMobileNet": [16000],
    "Kernels/Integer/Attention": [32000],
}
