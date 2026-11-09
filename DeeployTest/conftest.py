# SPDX-FileCopyrightText: 2025 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

import coloredlogs
import pytest

from Deeploy.Logging import DEFAULT_FMT
from Deeploy.Logging import DEFAULT_LOGGER as log


def pytest_addoption(parser: pytest.Parser) -> None:
    """Native PyTest hook: add custom command-line options for Deeploy tests."""
    parser.addoption(
        "--skipgen",
        action = "store_true",
        default = False,
        help = "Skip network generation step",
    )
    parser.addoption(
        "--skipsim",
        action = "store_true",
        default = False,
        help = "Skip simulation step (only generate and build)",
    )
    parser.addoption(
        "--profile-untiled",
        action = "store_true",
        default = False,
        help = "Enable profiling for untiled Siracusa runs",
    )
    parser.addoption(
        "--toolchain",
        action = "store",
        default = "LLVM",
        help = "Compiler toolchain to use (LLVM or GCC)",
    )
    parser.addoption(
        "--toolchain-install-dir",
        action = "store",
        default = os.environ.get("LLVM_INSTALL_DIR"),
        help = "Path to toolchain installation directory",
    )
    parser.addoption(
        "--cmake-args",
        action = "append",
        default = [],
        help = "Additional CMake arguments (can be used multiple times)",
    )
    parser.addoption(
        "--simulator",
        action = "store",
        default = None,
        help = "Override the platform's default simulator",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Native PyTest hook: configure pytest for Deeploy tests."""
    # Register custom markers
    config.addinivalue_line("markers", "generic: mark test as a Generic platform test")
    config.addinivalue_line("markers", "cortexm: mark test as a Cortex-M (QEMU-ARM) platform test")
    config.addinivalue_line("markers", "mempool: mark test as a MemPool platform test")
    config.addinivalue_line("markers", "chimera: mark test as a Chimera platform test")
    config.addinivalue_line("markers", "softhier: mark test as a SoftHier platform test")
    config.addinivalue_line("markers", "snitch: mark test as a Snitch platform test")
    config.addinivalue_line("markers", "snitch_tiled: mark test as a Snitch platform test (tiled)")
    config.addinivalue_line("markers", "siracusa: mark test as a Siracusa platform test (untiled)")
    config.addinivalue_line("markers", "siracusa_tiled: mark test as a Siracusa platform test (tiled)")
    config.addinivalue_line("markers",
                            "siracusa_neureka_tiled: mark test as a Siracusa + Neureka platform test (tiled)")
    config.addinivalue_line("markers", "pulpopen: mark test as a PULP-Open platform test (untiled)")
    config.addinivalue_line("markers", "pulpopen_tiled: mark test as a PULP-Open platform test (tiled)")
    config.addinivalue_line("markers", "gap9: mark test as a GAP9 platform test")
    config.addinivalue_line("markers", "gap9_tiled: mark test as a GAP9 platform test (tiled)")
    config.addinivalue_line("markers", "xdna2: mark test as an XDNA2 (AIE2p) platform test")
    config.addinivalue_line("markers", "kernels: mark test as a kernel test (individual operators)")
    config.addinivalue_line("markers", "models: mark test as a model test (full networks)")
    config.addinivalue_line("markers", "singlebuffer: mark test as single-buffer configuration")
    config.addinivalue_line("markers", "doublebuffer: mark test as double-buffer configuration")
    config.addinivalue_line("markers", "l2: mark test as L2 default memory level")
    config.addinivalue_line("markers", "l3: mark test as L3 default memory level")
    config.addinivalue_line("markers", "wmem: mark test as using Neureka weight memory")
    config.addinivalue_line("markers", "dma: mark test as DMA test")
    config.addinivalue_line(
        "markers",
        "deeploy_internal: mark test as internal Deeploy test (state serialization, extensions, transformations)")

    config.addinivalue_line("markers", "xheep: mark test as an X-HEEP platform test")

    # Configure logging based on verbosity
    verbosity = config.option.verbose
    if verbosity >= 3:
        coloredlogs.install(level = 'DEBUG', logger = log, fmt = DEFAULT_FMT)
    elif verbosity >= 2:
        coloredlogs.install(level = 'INFO', logger = log, fmt = DEFAULT_FMT)
    else:
        coloredlogs.install(level = 'WARNING', logger = log, fmt = DEFAULT_FMT)


_RTL_SIMULATORS = ("vsim", "vsim.gui")


def _pulpopen_rtl_selection():
    """Return the (marker, kind) -> allowed parameters map for PULP-Open runs on RTL.

    RTL simulation is much slower than GVSoC, so only a subset of the PULP-Open tests runs there.
    Untiled entries are test names; tiled entries are (test_name, l1, config_name) tuples, matching the
    parameters generated in test_platforms.py.
    """
    from test_pulpopen_config import KERNEL_TESTS_RTL, MODEL_TESTS_RTL
    from test_pulpopen_tiled_config import L2_DOUBLEBUFFER_KERNELS_RTL, L2_DOUBLEBUFFER_MODELS_RTL, \
        L2_SINGLEBUFFER_KERNELS_RTL, L2_SINGLEBUFFER_MODELS_RTL

    def tiled(*dicts_and_configs):
        return {(name, l1, cfg) for d, cfg in dicts_and_configs for name, l1s in d.items() for l1 in l1s}

    return {
        ("pulpopen", "kernels"): set(KERNEL_TESTS_RTL),
        ("pulpopen", "models"): set(MODEL_TESTS_RTL),
        ("pulpopen_tiled", "kernels"): tiled((L2_SINGLEBUFFER_KERNELS_RTL, "L2-singlebuffer"),
                                             (L2_DOUBLEBUFFER_KERNELS_RTL, "L2-doublebuffer")),
        ("pulpopen_tiled", "models"): tiled((L2_SINGLEBUFFER_MODELS_RTL, "L2-singlebuffer"),
                                            (L2_DOUBLEBUFFER_MODELS_RTL, "L2-doublebuffer")),
    }


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    """Native PyTest hook: on RTL simulators, restrict PULP-Open tests to their RTL subset."""
    if config.getoption("--simulator") not in _RTL_SIMULATORS:
        return

    selection = _pulpopen_rtl_selection()
    kept, deselected = [], []
    for item in items:
        callspec = getattr(item, "callspec", None)
        marker = next((m for m in ("pulpopen", "pulpopen_tiled") if item.get_closest_marker(m)), None)
        kind = next((k for k in ("kernels", "models") if item.get_closest_marker(k)), None)
        if callspec is None or marker is None or kind is None:
            kept.append(item)
            continue
        param = callspec.params.get("test_name", callspec.params.get("test_params"))
        (kept if param in selection[(marker, kind)] else deselected).append(item)

    if deselected:
        config.hook.pytest_deselected(items = deselected)
        items[:] = kept


@pytest.fixture(scope = "session")
def deeploy_test_dir():
    """Return the DeeployTest directory path."""
    return Path(__file__).parent


@pytest.fixture(scope = "session")
def tests_dir(deeploy_test_dir):
    """Return the Tests directory path."""
    return deeploy_test_dir / "Tests"


@pytest.fixture(scope = "session")
def toolchain_dir(request):
    """Return the toolchain installation directory."""
    toolchain_install = request.config.getoption("--toolchain-install-dir")
    if toolchain_install is None:
        pytest.skip(reason = "LLVM_INSTALL_DIR not set")
    return toolchain_install


@pytest.fixture(scope = "session", autouse = True)
def ccache_dir():
    """Setup and return ccache directory."""
    # Use existing CCACHE_DIR if already set
    if "CCACHE_DIR" in os.environ:
        return Path(os.environ["CCACHE_DIR"])

    # Fall back to /app/.ccache if it exists (for CI containers)
    ccache_path = Path("/app/.ccache")
    if ccache_path.exists():
        os.environ["CCACHE_DIR"] = str(ccache_path)
        return ccache_path

    return None


@pytest.fixture
def skipgen(request):
    """Return whether to skip network generation."""
    return request.config.getoption("--skipgen")


@pytest.fixture
def skipsim(request):
    """Return whether to skip simulation."""
    return request.config.getoption("--skipsim")


@pytest.fixture
def profile_untiled(request):
    """Return whether untiled profiling is enabled."""
    return request.config.getoption("--profile-untiled")


@pytest.fixture
def toolchain(request):
    """Return the toolchain to use."""
    return request.config.getoption("--toolchain")


@pytest.fixture
def cmake_args(request):
    """Return additional CMake arguments."""
    return request.config.getoption("--cmake-args")


@pytest.fixture
def simulator(request):
    """Return the simulator override, or None to use the platform default."""
    return request.config.getoption("--simulator")
