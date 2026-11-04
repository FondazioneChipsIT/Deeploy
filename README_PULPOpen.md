## Using Deeploy with PULP-Open

[PULP-Open](https://github.com/pulp-platform/pulp) can be targeted in three ways:

| Target | Simulator flag | What happens |
|---|---|---|
| GVSoC | `-s gvsoc` (default) | Build and run on the GVSoC `pulp-open` target |
| RTL | `-s vsim` / `-s vsim.gui` | Build and run on the PULP-Open RTL with QuestaSim |
| FPGA | `-s fpga` | Build only, with `printf` routed to the UART; loading the binary on the board is up to you |

The selected target also sets `SDK_PLATFORM` (`GVSOC`, `RTL` or `FPGA`), which configures the PULP SDK runtime
(`__PLATFORM__`, UART I/O) for where the binary runs.

### Cluster DMA

The cluster DMA is selected with `--dma {mchan,idma}` (default `idma`). It must match the hardware you run on: for RTL
and FPGA, use the DMA the PULP-Open hardware was built with.

### GVSoC

```sh
cd DeeployTest
python deeployRunner_pulpopen.py       -t ./Tests/Kernels/Integer/Add/Regular
python deeployRunner_tiled_pulpopen.py -t ./Tests/Kernels/Integer/Add/Regular
```

### RTL Simulation (QuestaSim)

Requirements:
- A compiled PULP-Open RTL (see the [pulp](https://github.com/pulp-platform/pulp) repository).
- `VSIM_PATH` pointing to its simulation directory (as exported by `source setup/vsim.sh` in the pulp repository), or
  `PULP_OPEN_HOME` pointing to the pulp repository (`VSIM_PATH` then defaults to `$PULP_OPEN_HOME/sim`).
- QuestaSim. The executable is set by the CMake variable `QUESTA` (default `questa-2022.3`); pass `-DQUESTA=vsim` to
  use the `vsim` in your `PATH`.

```sh
export VSIM_PATH=<pulp>/sim

cd DeeployTest
python deeployRunner_pulpopen.py -t ./Tests/Kernels/Integer/Add/Regular -s vsim -DQUESTA=vsim

# Same, with the QuestaSim GUI
python deeployRunner_pulpopen.py -t ./Tests/Kernels/Integer/Add/Regular -s vsim.gui -DQUESTA=vsim
```

As in the PULP SDK RTL flow, the stimuli are generated from the binary and the simulation runs in
`<build>/rtl_workdir`, which links the compiled RTL from `VSIM_PATH`. Each build directory has its own work directory,
so parallel runs do not interfere.

### FPGA

```sh
cd DeeployTest
python deeployRunner_pulpopen.py -t ./Tests/Kernels/Integer/Add/Regular -s fpga
```

The test is generated and built, but not run: the path of the binary is printed and, as with `--skipsim`, the test is
reported as passed without checking its output.

### Pytest

The PULP-Open tests run on GVSoC by default. Use `--simulator` to run them on another target:

```sh
cd DeeployTest

# GVSoC
pytest test_platforms.py -v -m "pulpopen and kernels"

# RTL, 4 simulations in parallel
pytest test_platforms.py -v -m "pulpopen and kernels" -n 4 --simulator=vsim --cmake-args=QUESTA=vsim

# Check that all tests build for the FPGA
pytest test_platforms.py -v -m "pulpopen or pulpopen_tiled" -n 8 --simulator=fpga
```
