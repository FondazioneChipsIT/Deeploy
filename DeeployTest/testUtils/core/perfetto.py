# SPDX-FileCopyrightText: 2026 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from Deeploy.Logging import DEFAULT_LOGGER as log

from .config import DeeployTestConfig

# Repository root, i.e. the parent of DeeployTest/
_REPO_ROOT = Path(__file__).resolve().parents[3]

CONVERTER_DIR = _REPO_ROOT / "scripts" / "gvsoc2perfetto-rs"
CONVERTER = CONVERTER_DIR / "target" / "release" / "gvsoc2perfetto"
BUILD_HINT = (f"cargo build --release --manifest-path {CONVERTER_DIR.relative_to(_REPO_ROOT)}/Cargo.toml")

# Name of the dump GVSoC writes into its work directory
VCD_NAME = "all.vcd"

# Which events GVSoC writes into the dump, per platform. This is the first of
# two filters and by far the more important one.
#
# Keep these selectors tight. GVSoC's VCD writer segfaults once too many events
# are traced at once: on Siracusa each of chip/cluster/{pe,icache,event_unit,
# dma}.* completes fine on its own, but chip/cluster/.* -- let alone the .* that
# the magia-sdk Makefile uses -- crashes it mid-run. Widening a selector is
# therefore something to re-verify, not to assume.
#
# Each entry becomes one --event flag. The selectors are matched loosely by
# gvsoc (hierarchy prefixes rather than strict regexes), so on Siracusa
# 'chip/cluster/pe.*' also picks up the DMA channels.
_PULP_CLUSTER_EVENTS = ["chip/cluster/pe.*"]
_NEUREKA_EVENTS = ["chip/cluster/pe.*", "chip/cluster/neureka.*"]
_SNITCH_EVENTS = ["soc/pe.*", "soc/fp_ss.*"]

DEFAULT_EVENTS = _PULP_CLUSTER_EVENTS

PLATFORM_EVENTS: Dict[str, List[str]] = {
    "Siracusa": _PULP_CLUSTER_EVENTS,
    "Siracusa_w_neureka": _NEUREKA_EVENTS,
    "PULPOpen": _PULP_CLUSTER_EVENTS,
    "Chimera": _PULP_CLUSTER_EVENTS,
    "Snitch": _SNITCH_EVENTS,
}

# Which of the dumped signals become Perfetto tracks. Second filter, applied by
# the converter: the dump still carries power traces and performance counters
# that would drown the interesting tracks.
_PULP_CLUSTER_INCLUDE = (r"chip\.cluster\.pe\d+\.(busy|asm|func|active_pc)$"
                         r"|chip\.cluster\.neureka\.(neureka_busy|fsm_state)$"
                         r"|chip\.cluster\.dma\.channel_\d+$")
_SNITCH_INCLUDE = r"soc\.(pe|fp_ss)\d+\.(busy|asm|func|active_pc)$"

# Hierarchy-agnostic fallback for platforms whose signal tree we have not
# characterised yet. Matches on leaf names only, so it degrades gracefully.
DEFAULT_INCLUDE = r"\.(busy|asm|func|active_pc|fsm_state)$"

PLATFORM_INCLUDE: Dict[str, str] = {
    "Siracusa": _PULP_CLUSTER_INCLUDE,
    "Siracusa_w_neureka": _PULP_CLUSTER_INCLUDE,
    "PULPOpen": _PULP_CLUSTER_INCLUDE,
    "Snitch": _SNITCH_INCLUDE,
}

# Platforms that define their own gvsoc target instead of the add_gvsoc_emulation
# macro in cmake/simulation.cmake, and therefore ignore the gvsoc_vcd option.
# GAP9 is deliberately excluded rather than wired up on spec: gvsoc segfaults
# when too many events are traced, so an unverified event selector would turn a
# passing test red instead of merely producing an empty dump.
UNSUPPORTED_PLATFORMS = ("GAP9", "SoftHier")


def vcd_path(config: DeeployTestConfig) -> Path:
    return Path(config.build_dir) / "gvsoc_workdir" / VCD_NAME


def vcd_events(config: DeeployTestConfig) -> List[str]:
    """GVSoC --event selectors to use for this test."""
    return config.vcd_events or PLATFORM_EVENTS.get(config.platform, DEFAULT_EVENTS)


def trace_path(config: DeeployTestConfig) -> Path:
    return Path(config.build_dir) / "gvsoc_workdir" / f"{config.test_name}.perfetto-trace"


def warn_if_unsupported(config: DeeployTestConfig) -> bool:
    """Warn when VCD dumping was requested on a platform that cannot provide it."""
    if config.platform in UNSUPPORTED_PLATFORMS:
        log.warning(f"VCD dumping is not wired for the {config.platform} platform, ignoring --vcd/--profile")
        return True
    if config.simulator != "gvsoc":
        log.warning(f"VCD dumping requires the gvsoc simulator (got '{config.simulator}'), "
                    "ignoring --vcd/--profile")
        return True
    return False


def convert_vcd_to_perfetto(config: DeeployTestConfig) -> Optional[Path]:
    """Convert the GVSoC VCD dump of a test into a Perfetto trace.

    Never raises: profiling is best-effort and must not turn a passing test into
    a failing one. Returns the trace path on success, None otherwise.
    """
    if not CONVERTER.is_file():
        log.warning(f"Perfetto converter not found at {CONVERTER}, skipping conversion. "
                    f"Build it with: {BUILD_HINT}")
        return None

    vcd = vcd_path(config)
    if not vcd.is_file() or vcd.stat().st_size == 0:
        log.warning(f"No VCD dump found at {vcd}, skipping conversion")
        return None

    trace = trace_path(config)
    include = config.vcd_include or PLATFORM_INCLUDE.get(config.platform, DEFAULT_INCLUDE)

    cmd = [
        str(CONVERTER),
        str(vcd),
        "-o",
        str(trace),
        "--split-asm",
        # The converter warns and emits no function tracks if the disassembly is
        # missing, so this can be passed unconditionally.
        "--symbolize",
        str(Path(config.build_dir) / "bin" / f"{config.test_name}.s"),
        "--rename",
        "active_pc=pc",
        "--include",
        include,
    ]

    log.debug(f"[Perfetto] Conversion command: {' '.join(cmd)}")

    result = subprocess.run(cmd, check = False, capture_output = True, encoding = "utf-8")

    if result.returncode != 0:
        log.warning(f"Perfetto conversion failed with return code {result.returncode}:\n{result.stderr.strip()}")
        return None

    # The converter reports the event/track counts on stderr; echo it so the run
    # log shows how much actually made it into the trace.
    for line in result.stderr.strip().splitlines():
        log.info(f"[Perfetto] {line}")

    log.info(f"Perfetto trace written to {trace}")

    if not config.keep_vcd:
        vcd.unlink()
        log.debug(f"[Perfetto] Removed {vcd} (pass --vcd to keep it)")

    return trace
