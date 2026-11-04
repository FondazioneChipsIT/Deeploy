# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

set(PULPNNVERSION XPULPV2)
set(PULPNNBITWIDTH 32)

#############################
##  RTL Simulation (Questa) ##
#############################

# Boot address of the PULP-Open L2 binary, as used by the pulp-sdk RTL flow
set(PULP_OPEN_ENTRY_POINT 0x1c008080)

# Creates the targets vsim_<name> and vsim.gui_<name>, which run <name> on the
# PULP-Open RTL (https://github.com/pulp-platform/pulp) with QuestaSim (${QUESTA}).
#
# This mirrors `make run platform=rtl` from the pulp-sdk: the stimuli are
# generated from the binary and the simulation runs in a per-build work
# directory that links the compiled RTL from ${VSIM_PATH}. VSIM_PATH is taken
# from the environment, or derived from PULP_OPEN_HOME as $PULP_OPEN_HOME/sim.
function(add_pulp_open_rtl_simulation name)
  set(_variants vsim vsim.gui)

  if(DEFINED ENV{VSIM_PATH})
    set(_vsimPath $ENV{VSIM_PATH})
  elseif(DEFINED ENV{PULP_OPEN_HOME})
    set(_vsimPath $ENV{PULP_OPEN_HOME}/sim)
  endif()

  if(NOT _vsimPath)
    set(_msg "RTL simulation of PULP-Open needs VSIM_PATH or PULP_OPEN_HOME (pointing to a compiled pulp RTL)")
    foreach(_variant ${_variants})
      add_custom_target(${_variant}_${name}
        COMMAND ${CMAKE_COMMAND} -E echo "[Deeploy PULP-OPEN] ${_msg}"
        COMMAND ${CMAKE_COMMAND} -E false
        VERBATIM
      )
    endforeach()
    return()
  endif()

  set(_binary ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${name})
  set(_workdir ${CMAKE_BINARY_DIR}/rtl_workdir)
  set(_sdkBin $ENV{PULP_SDK_HOME}/bin)

  # Work directory layout expected by the pulp TCL scripts
  file(MAKE_DIRECTORY ${_workdir}/stdout ${_workdir}/fs ${_workdir}/vectors)
  foreach(_link modelsim.ini work boot tcl_files waves)
    file(CREATE_LINK ${_vsimPath}/${_link} ${_workdir}/${_link} SYMBOLIC)
  endforeach()

  set(_genStimuli
    COMMAND ${_sdkBin}/stim_utils.py --binary=${_binary} --vectors=${_workdir}/vectors/stim.txt
    COMMAND ${_sdkBin}/plp_mkflash --flash-boot-binary=${_binary} --stimuli=${_workdir}/vectors/qspi_stim.slm
            --flash-type=spi --qpi
    COMMAND ${_sdkBin}/slm_hyper.py --input=${_workdir}/vectors/qspi_stim.slm
            --output=${_workdir}/vectors/hyper_stim.slm
  )

  set(_simEnv
    ${CMAKE_COMMAND} -E env
    "VSIM_PATH=${_vsimPath}"
    "VSIM_RUNNER_FLAGS=+ENTRY_POINT=${PULP_OPEN_ENTRY_POINT} -permit_unmatched_virtual_intf -gBAUDRATE=115200 -gLOAD_L2=JTAG"
  )
  # One command per -do: a ';' inside a CMake list would split the argument
  set(_batchArgs
    -c
    -do "source ${_vsimPath}/tcl_files/config/run_and_exit.tcl"
    -do "source ${_vsimPath}/tcl_files/run.tcl"
    -do "run_and_exit"
  )
  set(_guiArgs
    -do "source ${_vsimPath}/tcl_files/run_gui.tcl"
    -do "run"
  )

  foreach(_variant ${_variants})
    set(_sim ${_simEnv} ${QUESTA} -64)
    if(_variant MATCHES "\\.gui$")
      list(APPEND _sim ${_guiArgs})
    else()
      list(APPEND _sim ${_batchArgs})
    endif()

    add_custom_target(${_variant}_${name}
      DEPENDS ${name}
      WORKING_DIRECTORY ${_workdir}
      ${_genStimuli}
      COMMAND ${_sim}
      COMMENT "Simulating ${name} on the PULP-Open RTL with ${_variant}"
      USES_TERMINAL
      VERBATIM
    )
  endforeach()
endfunction()
